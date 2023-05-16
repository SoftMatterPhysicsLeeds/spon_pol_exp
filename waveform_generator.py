import pyvisa

## Agilent 3320A driver wrapper

# need to be able to set the:
# - function (e.g. Sine)
# - Unit (e.g. Vpp)
# - Amplitude (volts)
# - Frequency (Hz)
# - DC Offset (volts)

class Agilent33220A():
    def __init__(self):
        rm = pyvisa.ResourceManager()
        self.wfg = rm.open_resource("USB0::0x0957::0x0407::MY44059093::INSTR")


    def set_waveform(self, waveform = "SIN"):
        self.wfg.write(f"FUNC {waveform}")


    def set_frequency(self, frequency = 1000.0):
        self.wfg.write(f"FREQ {frequency}")


    def set_voltage(self, voltage = 1.0):
        self.wfg.write(f"VOLT {voltage}")


    def set_voltage_unit(self, voltage_unit = "VPP"):
        # options VPP | VRMS | DBM
        self.wfg.write(f"VOLT:UNIT {voltage_unit}")


    def set_dc_offset(self, offset = 0):
        self.wfg.write(f"VOLT:OFFS {offset}")


    def set_output(self, output = "OFF"):
        self.wfg.write(f":OUTP {output}")


    def close_wfg(self):
        self.wfg.close()