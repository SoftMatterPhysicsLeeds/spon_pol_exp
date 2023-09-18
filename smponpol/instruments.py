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
