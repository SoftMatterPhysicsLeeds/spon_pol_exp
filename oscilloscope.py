import pyvisa


class Tektronix():
    def __init__(self):
        rm = pyvisa.ResourceManager()
        self.scope = rm.open_resource("USB0::0x0699::0x03A6::C019341::INSTR")

    def set_channel_coupling(self, channel="CH1", coupling="AC"):
        self.scope.write(f"{channel}:COUP {coupling};")

    def set_channel_offset(self, channel="CH1", vertical_offset="0.0"):
        self.scope.write(f"{channel}:POS {vertical_offset}")

    def set_channel_attenuation(self, channel="CH1", prob_atten="10"):
        self.scope.write(f"{channel}:PRO {prob_atten}")

    def set_channel_range(self, channel="CH1", vertical_range="0"):
        self.scope.write(f"{channel}:POS {vertical_range}")

    def toggle_channel(self, channel="CH1", on=True):
        if on:
            self.scope.write(f"SEL:{channel} ON")
        else:
            self.scope.write(f"SEL:{channel} OFF")

    def set_timebase(self, timebase=0):
        self.scope.write(f":HOR:MAI:SCA {timebase}")

    def set_horizontal_offset(self, offset=0):
        self.scope.write(f":HOR:MAI:POS {offset}")

    def reset_to_default(self):
        self.scope.write("*RST")
        self.scope.write(":HEADER OFF;*ESE 60;*SRE 32;*CLS;")
