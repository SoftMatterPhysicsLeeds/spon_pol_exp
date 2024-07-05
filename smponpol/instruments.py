from typing import Any
import pyvisa
import threading

def write_handler(instrument, command_string):
    try:
        instrument.write(command_string)
        return None
    except Exception as e:
        print(f"Could not write {command_string} to {instrument}: ",e) 
        return e

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
        with self.lock:
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


class AgilentSpectrometer:
    def __init__(self, address: str) -> None:
        self.address = address
        self.initialise(self.address)

    def initialise(self, address: str) -> None:
        rm = pyvisa.ResourceManager()
        self.spectrometer = rm.open_resource(
            address
        )  # if no USB attached, this just connects to whatever first instrument is...
        # self.spectrometer = rm.open_resource(rm.list_resources()[0])
        self.spectrometer.read_termination = "\n"  # type: ignore
        self.spectrometer.write_termination = "\n"  # type: ignore
        # set timeout to long enough that the machine doesn't loose
        # connection during measurement.
        self.spectrometer.timeout = None
        # self.spectrometer.query("*IDN?")
        try:
            write_handler(self.spectrometer, "*IDN?")
            self.spectrometer_id = self.spectrometer.read()  # type: ignore
            print(self.spectrometer_id)
            self.reset_and_clear()

        except pyvisa.errors.VisaIOError:
            print("Could not connect to E4980A. Check address is correct.")

    def reset_and_clear(self) -> None:
        err = write_handler(self.spectrometer,"*RST; *CLS")  # type:ignore # reset and clear buffer
        err = write_handler(self.spectrometer,":DISP:ENAB")  # type:ignore # enable display and update
        err = write_handler(self.spectrometer,  # type: ignore
            ":INIT:CONT"
        )  # type: ignore # automatically perform continuous measurements
        err = write_handler(self.spectrometer,":TRIG:SOUR EXT")  # type: ignore
        self.set_voltage(0)
        return err

    def set_frequency(self, freq: float) -> None:
        err = write_handler(self.spectrometer, f":FREQ {freq}")
        return err

    def set_freq_list(self, freq_list: Any) -> None:
        err = write_handler(self.spectrometer,":DISP:PAGE LIST")  # type: ignore
        err = write_handler(self.spectrometer,":LIST:MODE SEQ")  # type: ignore

        freq_str = str(freq_list)
        freq_str = freq_str.split("[")[1].split("]")[0]

        err = write_handler(self.spectrometer,":LIST:FREQ ", freq_str)  # type: ignore
        return err

    def set_volt_list(self, volt_list: Any) -> None:
        err = write_handler(self.spectrometer,":DISP:PAGE LIST")  # type: ignore
        err = write_handler(self.spectrometer,":LIST:MODE SEQ")  # type: ignore

        volt_str = str(volt_list)
        volt_str = volt_str.split("[")[1].split("]")[0]

        err = write_handler(self.spectrometer,":LIST:VOLT ", volt_str)  # type: ignore
        return err

    def set_voltage(self, volt: float) -> None:
        err = write_handler(self.spectrometer,f":VOLT {volt}")  # type: ignore
        return err

    def set_func(self, func: str, auto: bool = True) -> None:
        err= write_handler(self.spectrometer,f":FUNC:IMP {func}")  # type: ignore
        if auto:
            err = write_handler(self.spectrometer,":FUNC:IMP:RANG:AUTO ON")  # type: ignore
        return err

    def set_aperture_mode(self, mode: str, av_factor: int) -> None:
        err= write_handler(self.spectrometer,f":APER {mode},{av_factor}")  # type: ignore
        return err

    def measure(self, func: str) -> list[float]:
        # write_handler(self.spectrometer,":INIT")
        err = write_handler(self.spectrometer,f":FUNC:IMP {func}")  # type: ignore
        err = write_handler(self.spectrometer,":TRIG:IMM")  # type: ignore
        err = write_handler(self.spectrometer,":FETC?")  # type: ignore # request data acquisition
        # get data as [val1, val2, data_status].
        # For CP-D func, this is [Cp, D, data_status]
        return self.spectrometer.read_ascii_values(), err  # type: ignore

    def set_DC_bias(self, voltage: float) -> None:
        err = write_handler(self.spectrometer,f":BIAS:VOLT {voltage}")  # type: ignore
        err = write_handler(self.spectrometer,":BIAS:STATE ON")  # type: ignore
        return err

    def turn_off_DC_bias(self) -> None:
        err = write_handler(self.spectrometer,":BIAS:STATE OFF")  # type: ignore
        return err

    def close(self):
        self.spectrometer.close()
