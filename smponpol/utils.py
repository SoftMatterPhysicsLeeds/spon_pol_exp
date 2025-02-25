import dearpygui.dearpygui as dpg
from smponpol.ui import lcd_ui
from smponpol.ui_qt import MainWindow
from smponpol.dataclasses import Instruments, State, Status
from smponpol.instruments import Agilent33220A, Instec, Rigol4204
import json
import pyvisa
import time
import threading

# TODO: find a way to handle exceptions in instrument threads?


def write_handler(instrument, command_string):
    try:
        instrument.write(command_string)
    except Exception as e:
        print(f"Could not write {command_string} to {instrument}: ", e)


def start_measurement(state: State, frontend: lcd_ui, instruments: Instruments) -> None:
    dpg.configure_item(frontend.start_button, enabled=False)
    with dpg.theme() as DEACTIVATED_THEME:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(
                dpg.mvThemeCol_Button, (100, 100, 100), category=dpg.mvThemeCat_Core
            )
    dpg.bind_item_theme(frontend.start_button, DEACTIVATED_THEME)

    state.T_list = [
        float(x.split("\t")[-1])
        for x in dpg.get_item_configuration(frontend.temperature_list.list_handle)[
            "items"
        ]
    ]

    state.voltage_list = [
        float(x.split("\t")[-1])
        for x in dpg.get_item_configuration(frontend.volt_list.list_handle)["items"]
    ]

    state.T_list = [round(x, 2) for x in state.T_list]

    # instruments.agilent.set_voltage(dpg.get_value(frontend.voltage_input))
    instruments.agilent.set_frequency(dpg.get_value(frontend.frequency_input))

    match dpg.get_value(frontend.selected_waveform):
        case "Sine":
            waveform = "SIN"
        case "Square":
            waveform = "SQU"
        case "Triangle":
            waveform = "TRI"
        case "User":
            waveform = "USER"
    instruments.agilent.set_waveform(waveform)

    instruments.agilent.set_output("OFF")

    state.T_step = 0
    state.voltage_step = 0

    T_str = f"{state.T_step + 1}: {state.T_list[state.T_step]}"
    v_str = f"{state.voltage_step + 1: {state.voltage_list[state.voltage_step]}}"

    state.resultsDict[T_str] = dict()
    state.resultsDict[T_str][v_str] = dict()
    state.resultsDict[T_str][v_str]["time"] = []
    state.resultsDict[T_str][v_str]["channel1"] = []
    state.resultsDict[T_str][v_str]["channel2"] = []
    state.resultsDict[T_str][v_str]["channel3"] = []

    state.measurement_status = Status.SET_TEMPERATURE
    state.xdata = []
    state.ydata = []


def stop_measurement(instruments: Instruments, state: State, frontend: lcd_ui) -> None:
    instruments.hotstage.stop()
    state.measurement_status = Status.IDLE


def init_agilent(frontend: MainWindow, instruments: Instruments, state: State) -> None:
    if instruments.agilent:
        instruments.agilent.close()
    agilent = Agilent33220A(dpg.get_value(frontend.agilent_com_selector))
    agilent = Agilent33220A(frontend.equipment_init.agilent_combo.currentText())
    agilent.set_output("OFF")
    instruments.agilent = agilent
    state.agilent_connection_status = "Connected"


def init_oscilloscope(
    frontend: MainWindow, instruments: Instruments, state: State
) -> None:
    if instruments.oscilloscope:
        instruments.oscilloscope.close()

    instruments.oscilloscope = Rigol4204(
        frontend.equipment_init.oscilloscope_combo.currentText()
    )

    state.oscilloscope_connection_status = "Connected"


def init_hotstage(frontend: MainWindow, instruments: Instruments, state: State) -> None:
    hotstage = Instec(frontend.equipment_init.hotstage_combo.currentText())
    try:
        hotstage.get_temperature()
        instruments.hotstage = hotstage
        state.hotstage_connection_status = "Connected"
        with open("address.dat", "w") as f:
            f.write(dpg.get_value(frontend.hotstage_com_selector))

    except pyvisa.errors.VisaIOError:
        dpg.set_value(frontend.hotstage_status, "Couldn't connect")


def connect_to_instruments_callback(
    main_window: MainWindow, instruments: Instruments, state: State
):
    hotstage_thread = threading.Thread(
        target=init_hotstage,
        args=(main_window, instruments, state),
    )

    hotstage_thread.daemon = True
    hotstage_thread.start()

    agilent_thread = threading.Thread(
        target=init_agilent,
        args=(main_window, instruments, state),
    )

    agilent_thread.daemon = True
    agilent_thread.start()

    oscilloscope_thread = threading.Thread(
        target=init_oscilloscope,
        args=(main_window, instruments, state),
    )

    oscilloscope_thread.daemon = True
    oscilloscope_thread.start()

    main_window.equipment_init.setVisible(False)
    main_window.control_box.setVisible(True)


def handle_measurement_status(state: State, frontend: lcd_ui, instruments: Instruments):
    current_wait = 0

    if state.measurement_status == Status.IDLE:
        dpg.set_value(
            frontend.measurement_status, f"Idle\tT: {state.hotstage_temperature:.2f}°C"
        )
        dpg.configure_item(frontend.start_button, enabled=True)

        with dpg.theme() as START_THEME:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(
                    dpg.mvThemeCol_Button, (0, 100, 0), category=dpg.mvThemeCat_Core
                )
        dpg.bind_item_theme(frontend.start_button, START_THEME)
    elif state.measurement_status == Status.SET_TEMPERATURE:
        instruments.hotstage.ramp(
            state.T_list[state.T_step], dpg.get_value(frontend.T_rate)
        )
        state.measurement_status = Status.GOING_TO_TEMPERATURE
        dpg.set_value(
            frontend.measurement_status,
            f"Going to {state.T_list[state.T_step]}°C\tT: {state.hotstage_temperature:.2f}°C",
        )
    elif state.measurement_status == Status.GOING_TO_TEMPERATURE and (
        state.hotstage_temperature > state.T_list[state.T_step] - 0.1
        and state.hotstage_temperature < state.T_list[state.T_step] + 0.1
    ):
        state.t_stable_start = time.time()
        state.measurement_status = Status.STABILISING_TEMPERATURE

    elif state.measurement_status == Status.GOING_TO_TEMPERATURE:
        dpg.set_value(
            frontend.measurement_status,
            f"Going to {state.T_list[state.T_step]}°C\tT: {state.hotstage_temperature:.2f}°C",
        )

    elif state.measurement_status == Status.STABILISING_TEMPERATURE:
        current_wait = time.time() - state.t_stable_start
        dpg.set_value(
            frontend.measurement_status,
            f"Stabilising temperature for {current_wait:.2f}/{dpg.get_value(frontend.stab_time)}s\tT: {state.hotstage_temperature:.2f}°C",
        )
        if current_wait >= dpg.get_value(frontend.stab_time):
            state.measurement_status = Status.TEMPERATURE_STABILISED

    elif state.measurement_status == Status.TEMPERATURE_STABILISED:
        state.measurement_status = Status.COLLECTING_DATA
        take_data(frontend, instruments, state)

    elif state.measurement_status == Status.COLLECTING_DATA:
        dpg.set_value(
            frontend.measurement_status,
            f"Taking data\tT: {state.hotstage_temperature:.2f}°C",
        )

    elif state.measurement_status == Status.FINISHED:
        instruments.hotstage.stop()
        instruments.agilent.set_output("OFF")
        state.measurement_status = Status.IDLE
        dpg.set_value(
            frontend.measurement_status, f"Idle\tT: {state.hotstage_temperature:.2f}°C"
        )


def find_instruments(frontend: lcd_ui):
    dpg.set_value(frontend.measurement_status, "Finding Instruments...")
    rm = pyvisa.ResourceManager()
    visa_resources = rm.list_resources("?*")

    usb_selector = [x for x in visa_resources if x.split("::")[0] == "USB0"]

    rigol_addresses = [x for x in usb_selector if x.split("::")[1] == "0x1AB1"]
    agilent_addresses = [x for x in usb_selector if x.split("::")[1] == "0x0957"]
    instec_addresses = [x for x in usb_selector if x.split("::")[1] == "0x03EB"]

    dpg.configure_item(frontend.hotstage_com_selector, items=instec_addresses)
    dpg.configure_item(frontend.agilent_com_selector, items=agilent_addresses)
    dpg.configure_item(frontend.oscilloscope_com_selector, items=rigol_addresses)

    dpg.set_value(
        frontend.hotstage_com_selector,
        instec_addresses[0] if (len(instec_addresses) > 0) else "",
    )
    dpg.set_value(
        frontend.agilent_com_selector,
        agilent_addresses[0] if len(agilent_addresses) > 0 else "",
    )
    dpg.set_value(
        frontend.oscilloscope_com_selector,
        rigol_addresses[0] if len(rigol_addresses) > 0 else "",
    )

    dpg.set_value(frontend.measurement_status, "Found instruments!")
    dpg.set_value(frontend.measurement_status, "Idle")


def take_data(
    frontend: lcd_ui, instruments: Instruments, state: State, single_shot=False
) -> None:
    thread = threading.Thread(
        target=run_experiment, args=(frontend, instruments, state, single_shot)
    )
    thread.daemon = True
    thread.start()


def run_experiment(
    frontend: lcd_ui, instruments: State, state: State, single_shot=False
):
    if single_shot:
        state.measurement_status = Status.COLLECTING_DATA

    result = dict()
    instruments.agilent.set_voltage(state.voltage_list[state.voltage_step])
    instruments.agilent.set_output("ON")

    times, data = instruments.oscilloscope.get_channel_trace(1)
    _, data2 = instruments.oscilloscope.get_channel_trace(2)
    _, data3 = instruments.oscilloscope.get_channel_trace(3)

    instruments.oscilloscope.run()
    instruments.agilent.set_output("OFF")

    result["time"] = times
    result["channel1"] = data
    result["channel2"] = data2
    result["channel3"] = data3

    get_result(result, state, frontend, instruments, single_shot)


def read_temperature(frontend: lcd_ui, instruments: Instruments, state: State):
    log_time = 0
    time_step = 0.05
    while True:
        temperature = instruments.hotstage.get_temperature()
        if temperature is None:
            continue

        state.hotstage_temperature = temperature
        dpg.set_value(frontend.hotstage_status, f"T: {temperature:.2f}")
        state.T_log_time.append(log_time)
        state.T_log_T.append(temperature)

        if len(state.T_log_T) == 1000:
            state.T_log_T = state.T_log_T[1:]
            state.T_log_time = state.T_log_time[1:]

        # state.hotstage_action = status
        time.sleep(time_step)
        log_time += time_step


def export_data_file(frontend: lcd_ui, state: State, result, single_shot=False):
    if single_shot:
        times = result["time"]
        channel1 = result["channel1"]
        channel2 = result["channel2"]
        output_filename = (
            dpg.get_value(frontend.output_file_path).split(".json")[0]
            + f" {dpg.get_value(frontend.voltage_input):.2f} Volts"
            + f" {dpg.get_value(frontend.frequency_input):.1f} Hz"
            + f" {state.hotstage_temperature:.2f} C.dat"
        )
    else:
        T_str = f"{state.T_step + 1}: {state.T_list[state.T_step]}"
        v_str = f"{state.voltage_step + 1: {state.voltage_list[state.voltage_step]}}"
        times = state.resultsDict[T_str][v_str]["time"]
        channel1 = state.resultsDict[T_str][v_str]["channel1"]
        channel2 = state.resultsDict[T_str][v_str]["channel2"]
        channel3 = state.resultsDict[T_str][v_str]["channel3"]

        output_filename = (
            dpg.get_value(frontend.output_file_path).split(".json")[0]
            + f" {dpg.get_value(state.voltage_list[state.voltage_step]):.2f} Volts"
            + f" {dpg.get_value(frontend.frequency_input):.1f} Hz"
            + f" {state.T_list[state.T_step]:.2f} C.dat"
        )

    with open(output_filename, "w") as f:
        f.write("time\tChannel1\tChannel2\tChannel3\n")
        f.write("Data\n")
        for time_inc, channel1_inc, channel2_inc, channel3_inc in zip(
            times, channel1, channel2, channel3
        ):
            f.write(f"{time_inc}\t{channel1_inc}\t{channel2_inc}\t{channel3_inc}\n")


def get_result(
    result: dict,
    state: State,
    frontend: lcd_ui,
    instruments: Instruments,
    single_shot=False,
) -> None:
    parse_result(result, state, frontend, single_shot)

    if state.measurement_status == Status.IDLE:
        pass

    else:
        with open(dpg.get_value(frontend.output_file_path), "w") as write_file:
            json.dump(state.resultsDict, write_file, indent=4)

        export_data_file(frontend, state, result, single_shot)

        if single_shot:
            state.measurement_status = Status.IDLE
            dpg.set_value(frontend.measurement_status, "Idle")

        if not single_shot:
            if (
                state.T_step == len(state.T_list) - 1
                and state.voltage_step == len(state.voltage_list) - 1
            ):
                state.measurement_status = Status.FINISHED
            elif state.voltage_step == len(state.voltage_list) - 1:
                state.T_step += 1
                T_str = f"{state.T_step + 1}: {state.T_list[state.T_step]}"
                v_str = f"{state.voltage_step + 1: {state.voltage_list[state.voltage_step]}}"
                state.resultsDict[T_str][v_str] = dict()
                state.resultsDict[T_str][v_str]["time"] = []
                state.resultsDict[T_str][v_str]["channel1"] = []
                state.resultsDict[T_str][v_str]["channel2"] = []
                state.resultsDict[T_str][v_str]["channel3"] = []

                state.measurement_status = Status.TEMPERATURE_STABILISED

            else:
                # state.T_step += 1
                state.voltage_step += 1
                T_str = f"{state.T_step + 1}: {state.T_list[state.T_step]}"
                v_str = f"{state.voltage_step + 1: {state.voltage_list[state.voltage_step]}}"

                state.resultsDict[T_str] = dict()
                state.resultsDict[T_str][v_str] = dict()
                state.resultsDict[T_str][v_str]["time"] = []
                state.resultsDict[T_str][v_str]["channel1"] = []
                state.resultsDict[T_str][v_str]["channel2"] = []
                state.resultsDict[T_str][v_str]["channel3"] = []

                state.measurement_status = Status.SET_TEMPERATURE


def parse_result(
    result: dict, state: State, frontend: lcd_ui, single_shot=False
) -> None:
    if not single_shot:
        T_str = f"{state.T_step + 1}: {state.T_list[state.T_step]}"
        v_str = f"{state.voltage_step + 1: {state.voltage_list[state.voltage_step]}}"
        state.resultsDict[T_str][v_str]["time"] = result["time"]
        state.resultsDict[T_str][v_str]["channel1"] = result["channel1"]
        state.resultsDict[T_str][v_str]["channel2"] = result["channel2"]
        state.resultsDict[T_str][v_str]["channel3"] = result["channel3"]

    dpg.set_value(frontend.results_plot, [result["time"], result["channel1"]])
    dpg.set_value(frontend.results_plot2, [result["time"], result["channel2"]])
    dpg.set_value(frontend.results_plot3, [result["time"], result["channel3"]])

    dpg.fit_axis_data("V_axis")
    dpg.fit_axis_data("time_axis")
    dpg.fit_axis_data("current_axis")
