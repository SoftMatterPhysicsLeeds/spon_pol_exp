import threading
import pyvisa


class LinkamHotstage:
    def __init__(self, address: str) -> None:
        self.address = address
        self.lock = threading.Lock()
        self.initialise_linkam()

    def initialise_linkam(self) -> None:
        rm = pyvisa.ResourceManager()

        self.link = rm.open_resource(self.address)
        self.init = False

        self.link.baud_rate = 19200  # type: ignore

        self.link.read_termination = "\r"  # type: ignore
        self.link.write_termination = "\r"  # type: ignore

        self.link.timeout = 3000

        try:
            self.current_temperature()
            print("Linkam Connected!")

        except pyvisa.errors.VisaIOError:
            print(
                "Could not connect to Linkam Hotstage. Try different address \
                (make sure it is switched on)"
            )

    def set_temperature(self, T: float, rate: float = 20.0) -> None:
        if self.init:
            with self.lock:
                self.link.write(f"R1{int(rate*100)}")  # type: ignore
                self.link.read()  # type: ignore
                self.link.write(f"L1{int(T*10)}")  # type: ignore
                self.link.read()  # type: ignore
        else:
            with self.lock:
                self.link.write(f"R1{int(rate*100)}")  # type: ignore
                self.link.read()  # type: ignore
                self.link.write(f"L1{int(T*10)}")  # type: ignore
                self.link.read()  # type: ignore
                self.link.write("S")  # type: ignore
                self.link.read()

                self.init = True

    def stop(self) -> None:
        self.link.write("E")  # type: ignore
        self.link.read()  # type: ignore
        self.init = False

    def current_temperature(self) -> tuple[float, str]:
        with self.lock:
            try:
                self.link.write("T")  # type: ignore
                raw_string = self.link.read_raw()  # type: ignore
            except UnicodeDecodeError:
                return 0.0, 0.0
        status_byte = int(raw_string[0])

        if status_byte == 1:
            status = "Stopped"
        elif status_byte == 16 or status_byte == 17:
            status = "Heating"
        elif status_byte == 32 or status_byte == 33:
            status = "Cooling"
        elif status_byte == 48 or status_byte == 49:
            status = "Holding"
        else:
            status = "Dunno"
        try:
            temperature = int(raw_string[6:10], 16) / 10.0
        except ValueError:
            return 0.0, 0.0
        return temperature, status

    def close(self):
        self.link.close()


class Agilent33220A:
    def __init__(self, address):
        rm = pyvisa.ResourceManager()
        self.wfg = rm.open_resource(address)

    def set_waveform(self, waveform="SIN"):
        self.wfg.write(f"FUNC {waveform}")

    def set_frequency(self, frequency=1000.0):
        self.wfg.write(f"FREQ {frequency}")

    def set_voltage(self, voltage=1.0):
        self.wfg.write(f"VOLT {voltage}")

    def set_voltage_unit(self, voltage_unit="VPP"):
        # options VPP | VRMS | DBM
        self.wfg.write(f"VOLT:UNIT {voltage_unit}")

    def set_dc_offset(self, offset=0):
        self.wfg.write(f"VOLT:OFFS {offset}")

    def set_output(self, output="OFF"):
        self.wfg.write(f":OUTP {output}")

    def close_wfg(self):
        self.wfg.close()


class Rigol4204:
    def __init__(self, address):
        rm = pyvisa.ResourceManager()
        self.scope = rm.open_resource(address)
        self.scope.timeout = 100000.0
        self.scope.write(":TIM:HREF:MODE CENT")
        self.scope.write(":TRIG:NREJ ON")

    # Memory Depth options: 1k, 10k, 100k, 1M, 10M, 25M, 50M, 100M, 125M
    def set_memory_depth(self, depth=10000):
        self.scope.write(f"ACQ:MDEP {depth}")

    # acqusition types: NORM, AVER, PEAK, HRES
    def set_acquisition_type(self, acq_type="AVER"):
        self.scope.write(f":ACQ:TYPE {acq_type}")

    def set_number_of_averages(self, averages=64):
        self.scope.write(f":ACQ:AVER {averages}")

    def set_offset(self, offset=0.0):
        self.scope.write(f":TIM:OFFS {offset}")

    def set_scale(self, scale=0.01):
        self.scope.write(f":TIM:SCAL {scale}")

    # Mode options: Main, XY, Roll
    def set_mode(self, mode="MAIN"):
        self.scope.write(f":TIM:MODE {mode}")

    # coupling mode options: AC, DC, LFR, HFR
    def set_coupling_mode(self, mode="AC"):
        self.scope.write(f":TRIG:COUP {mode}")

    def set_holdoff_time(self, holdoff_time=1e-7):
        self.scope.write(f":TRIG:HOLD {holdoff_time}")

    # trigger type options: EDGE, PULS, RUNT, WIND, NEDG, SLOP, VID, PATT, DEL, TIM, DURAT, SHOL, RS232, IIC, SPI, USB, flexray, CAN
    def set_trigger_type(self, trigger_type="EDGE"):
        self.scope.write(f":TRIG:MODE {trigger_type}")

    # trigger slope options: POS, NEG, RFAL
    def set_trigger_slope(self, trigger_slope="POS"):
        self.scope.write(f":TRIG:EDGE:SLOP {trigger_slope}")

    def set_trigger_level(self, trigger_level=0.0):
        self.scope.write(f":TRIG:EDGE:LEV {trigger_level}")

    def set_trigger_channel(self, channel=1):
        self.scope.write(f":TRIG:EDGE:SOUR CHAN{channel}")

    # trigger modes: AUTO, NORM, SING
    def set_trigger_mode(self, mode="AUTO"):
        self.scope.write(f":TRIG:SWE {mode}")

    # channel set up

    def initialise_channel(self, channel=1, mode="AC", attenuation=1, offset=0.0, v_range=0.0):
        self.set_channel_coupling_mode(channel, mode)
        self.set_channel_probe_attenuation(channel, attenuation)
        self.set_channel_vertical_offset(channel, offset)
        self.set_channel_vertical_range(channel, v_range)
        self.scope.write(f"CHAN{channel}:BWL ON")
        self.scope.write(f"CHAN{channel}:DISP ON")

    def set_channel_coupling_mode(self, channel=1, mode="AC"):
        self.scope.write(f":CHAN{channel}:COUP {mode}")

    def set_channel_probe_attenuation(self, channel=1, attenuation=1):
        self.scope.write(f":CHAN{channel}:PROB {attenuation}")

    def set_channel_vertical_offset(self, channel=1, offset=0.0):
        self.scope.write(f"CHAN{channel}:OFFS {offset}")

    def set_channel_vertical_range(self, channel=1, v_range=0.0):
        self.scope.write(f"CHAN{channel}:SCAL {v_range}")

    def get_channel_trace(self, channel=1):
        self.scope.write(":STOP")
        # if channel display is 'off', then don't do anything and just return.
        if int(self.scope.query(":CHAN{channel}:DISP?").strip()) == 0:
            return

        self.scope.write(f":WAV:SOUR CHAN{channel}")
        self.scope.write(":WAV:FORM ASC;:WAV:MODE MAX")
        x_increment = float(self.scope.query("WAV:XINC?"))
        y_increment = float(self.scope.query("WAV:YINC?"))
        y_reference = float(self.scope.query("WAV:YREF?"))
        start_time = float(self.scope.query("WAV:XOR?"))

        data = self.scope.query(":WAV:DATA?")
        if self.scope.query("WAV:MODE?").strip() == "NORM":
            y_reference = y_reference * y_increment
        data = [(float(x) - y_reference) *
                y_increment for x in data.strip().split(',')]
        time = [start_time+(x_increment * x) for x in range(len(data))]

        return time, data

# operation order for RIGOL (from "Main_program_v1_18_RIGOL.vi"):
# Connect
# set memory depth, offset, scale and mode
