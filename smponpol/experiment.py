from PySide6.QtCore import QObject, Signal, Slot, QThread, QTimer
from dataclasses import dataclass, field
import itertools
import time
import pyvisa
import threading

from smponpol.instruments import Instec, Agilent33220A, Rigol4204

# TODO: need to add ramp setting for T


@dataclass
class Instruments:
    hotstage: Instec | None = None
    agilent: Agilent33220A | None = None
    oscilloscope: Rigol4204 | None = None
    hotstage_temperature: float = 25.0

    Slot(float)

    def set_hotstage_temperature(self, T: float):
        self.hotstage_temperature = T


@dataclass
class MeasurementPoint:
    temperature: float
    voltage: float
    frequency: float
    file_path: str
    rate: float
    result: dict = field(default_factory=dict)


class ExperimentWorker(QObject):
    status_changed = Signal(str)
    measurement_finished = Signal(MeasurementPoint)

    def __init__(self, instruments: Instruments):
        super().__init__()
        self.instruments = instruments

        self.should_stop = True
        # Setup timer for temperature monitoring
        self.temp_timer = QTimer()
        self.temp_timer.timeout.connect(self.check_temperature)

        # Flag to track what we're doing
        self.waiting_for_temp = False
        self.current_point = None
        self.t_stable_start = 0

    def run_single_point(self, point: MeasurementPoint):
        self.should_stop = False
        self.current_point = point
        self.set_temperature(point)
        # take_data will be called when temperature is stable

    def set_temperature(self, point: MeasurementPoint):
        if self.should_stop:
            self.status_changed.emit("Idle")
            return
        self.instruments.hotstage.ramp(point.temperature, point.rate)
        self.status_changed.emit(f"Going to {point.temperature}°C")

        # Start monitoring temperature
        self.waiting_for_temp = True
        self.at_temperature = False
        self.stabilised = False
        self.temp_timer.start(100)  # Check every 100ms

    def check_temperature(self):
        if self.should_stop:
            self.temp_timer.stop()
            self.status_changed.emit("Idle")
            return

        point = self.current_point

        if not self.at_temperature:
            # Check if we've reached target temperature
            if (
                self.instruments.hotstage_temperature > point.temperature - 0.1
                and self.instruments.hotstage_temperature < point.temperature + 0.1
            ):
                self.t_stable_start = time.time()
                self.at_temperature = True
        else:
            # We're at temperature, check stabilization
            current_wait = time.time() - self.t_stable_start
            self.status_changed.emit(
                f"Stabilising temperature for {current_wait:.2f}/{30}s\tT: {self.instruments.hotstage_temperature:.2f}°C"
            )

            if current_wait >= 30:
                self.stabilised = True
                self.waiting_for_temp = False
                self.temp_timer.stop()

                # Now proceed to take data
                self.take_data(self.current_point)

    def take_data(self, point: MeasurementPoint):
        if self.should_stop:
            self.status_changed.emit("Idle")
            return
        self.status_changed.emit(
            f"Taking data: V: {point.voltage}V, T: {point.temperature}°C"
        )
        result = dict()

        self.instruments.agilent.set_voltage(point.voltage)
        self.instruments.agilent.set_output("ON")

        times, data = self.instruments.oscilloscope.get_channel_trace(1)
        _, data2 = self.instruments.oscilloscope.get_channel_trace(2)
        _, data3 = self.instruments.oscilloscope.get_channel_trace(3)

        self.instruments.oscilloscope.run()
        self.instruments.agilent.set_output("OFF")

        result["time"] = times
        result["channel1"] = data
        result["channel2"] = data2
        result["channel3"] = data3

        point.result = result
        self.measurement_finished.emit(point)


class InstrumentWorker(QObject):
    current_temperature = Signal(float)

    instruments_found = Signal(list, list, list)

    def __init__(self, instruments: Instruments):
        super().__init__()

        self.instruments = instruments

    def find_instruments(self):
        rm = pyvisa.ResourceManager()
        visa_resources = rm.list_resources("?*")

        usb_selector = [x for x in visa_resources if x.split("::")[0] == "USB0"]

        instec_addresses = [x for x in usb_selector if x.split("::")[1] == "0x03EB"]
        agilent_addresses = [x for x in usb_selector if x.split("::")[1] == "0x0957"]
        rigol_addresses = [x for x in usb_selector if x.split("::")[1] == "0x1AB1"]

        self.instruments_found.emit(
            instec_addresses, agilent_addresses, rigol_addresses
        )

    def temperature_loop(self):
        time_step = 0.05
        while True:
            temperature = self.instruments.hotstage.get_temperature()
            if temperature is None:
                continue
            self.current_temperature.emit(temperature)
            time.sleep(time_step)


class ExperimentController(QObject):
    start_experiment = Signal(list, list, float, str, str, float)
    start_reading_temperature = Signal()
    update_graph = Signal(dict)

    def __init__(self, instruments: Instruments):
        super().__init__()
        self.measurement_points = []
        self.current_point_index = 0
        self.instruments = instruments

        self.worker = ExperimentWorker(instruments)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.thread.start()

        self.instrument_thread = QThread()
        self.instrument_worker = InstrumentWorker(self.instruments)
        self.instrument_worker.moveToThread(self.instrument_thread)
        self.instrument_thread.start()

        self.worker.measurement_finished.connect(self.parse_result)
        self.start_experiment.connect(self.experiment_setup_and_run)
        self.start_reading_temperature.connect(self.instrument_worker.temperature_loop)

    @Slot(list, list, str)
    def experiment_setup_and_run(
        self, temperatures, voltages, frequency, file_path, waveform_in, rate
    ):
        match waveform_in:
            case "Sine":
                waveform = "SIN"
            case "Square":
                waveform = "SQU"
            case "Triangle":
                waveform = "TRI"
            case "User":
                waveform = "USER"
        self.instruments.agilent.set_waveform(waveform)
        self.instruments.agilent.set_output("OFF")

        self.current_point_index = 0
        self.create_measurement_points(
            temperatures, voltages, frequency, file_path, rate
        )
        self.run_next_point()

    def create_measurement_points(
        self, temperatures, voltages, frequency, file_path, rate
    ):
        for t, v in itertools.product(temperatures, voltages):
            self.measurement_points.append(
                MeasurementPoint(t, v, frequency, file_path, rate)
            )

    def run_next_point(self):
        if self.current_point_index >= len(self.measurement_points):
            self.worker.status_changed.emit("Idle")
            return

        point = self.measurement_points[self.current_point_index]
        self.worker.run_single_point(point)

    @Slot(MeasurementPoint)
    def parse_result(self, point: MeasurementPoint):
        self.update_graph.emit(point.result)
        output_filename = (
            point.file_path.split(".json")[0]
            + f" {point.voltage:.2f} Volts"
            + f" {point.frequency:.1f} Hz"
            + f" {point.temperature:.2f} C.dat"
        )
        with open(output_filename, "w") as f:
            f.write("time\tChannel1\tChannel2\tChannel3\n")
            f.write("Data\n")
            for time_inc, channel1_inc, channel2_inc, channel3_inc in zip(
                point.result["time"],
                point.result["channel1"],
                point.result["channel2"],
                point.result["channel3"],
            ):
                f.write(f"{time_inc}\t{channel1_inc}\t{channel2_inc}\t{channel3_inc}\n")

        self.current_point_index += 1
        self.run_next_point()

    def stop_experiment(self):
        self.instruments.hotstage.stop()
        self.worker.stop = True
        self.worker.status_changed.emit("Idle")

    def stop_and_cleanup(self):
        self.stop_experiment()

        self.thread.quit()
        self.thread.wait(1000)

        self.instrument_thread.quit()
        self.instrument_thread.wait(1000)
