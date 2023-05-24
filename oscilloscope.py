import pyvisa


class Tektronix:
    def __init__(self):
        rm = pyvisa.ResourceManager()
        self.scope = rm.open_resource("USB0::0x0699::0x03A6::C019341::INSTR")
        self.scope.timeout = 10000

    # DATA ACQUISITION

    def set_acq_state(self, acq_state="ON"):
        self.scope.write(f"ACQ:STATE {acq_state}")

    def set_data_source(self, channel="CH1"):
        self.scope.write(f"DATA:SOURCE {channel}")

    def set_data_encoding(self):
        # self.scope.write(f"DAT:ENC RPB; WID 2")
        self.scope.write("DAT:ENC ASCII")

    def get_scaling_factors(self):
        self.scope.write("WFMPRE:XZE?;XIN?;YZE?;YMU?;YOFF?")
        factors = self.scope.read()
        return [float(x) for x in factors.strip().split(";")]

    # SETUP

    def initialise_scope(
        self,
        timebase=0,
        h_offset=0,
        channel="CH1",
        trigger_slope="RIS",
        trigger_coupling="AC",
        trigger_holdoff=0.0,
        trigger_level=0.0,
        trigger_mode="AUTO",
    ):
        self.reset_to_default()
        self.set_timebase(timebase)
        self.set_horizontal_offset(h_offset)
        self.set_trigger_type_edge()
        self.set_trigger_source(channel)
        self.set_trigger_slope(trigger_slope)
        self.set_trigger_coupling(trigger_coupling)
        self.set_trigger_holdoff(trigger_holdoff)
        self.set_trigger_level(trigger_level)
        self.set_trigger_mode()

    def initialise_channel(
        self, channel="CH1", coupling="AC", v_offset=0.0, probe_atten=10, v_range=0
    ):
        self.set_channel_coupling(channel, coupling)
        self.set_channel_offset(channel, v_offset)
        self.set_channel_attenuation(channel, probe_atten)
        self.set_channel_range(channel, v_range)
        self.toggle_channel()

    def set_channel_coupling(self, channel="CH1", coupling="AC"):
        self.scope.write(f"{channel}:COUP {coupling};")

    def set_channel_offset(self, channel="CH1", vertical_offset=0.0):
        self.scope.write(f"{channel}:POS {vertical_offset}")

    def set_channel_attenuation(self, channel="CH1", prob_atten=10):
        self.scope.write(f"{channel}:PRO {prob_atten}")

    def set_channel_range(self, channel="CH1", vertical_range=0):
        self.scope.write(f"{channel}:SCA {vertical_range}")

    def toggle_channel(self, channel="CH1", on=True):
        if on:
            self.scope.write(f"SEL:{channel} ON")
        else:
            self.scope.write(f"SEL:{channel} OFF")

    def set_timebase(self, timebase=0):
        self.scope.write(f":HOR:MAI:SCA {timebase}")

    def set_horizontal_offset(self, offset=0):
        self.scope.write(f":HOR:MAI:POS {offset}")

    def set_trigger_type_edge(self):
        self.scope.write("TRIG:MAIN:TYP EDGE")

    def set_trigger_source(self, channel="CH1"):
        self.scope.write(f"TRIG:MAIN:EDGE:SOU {channel}")

    def set_trigger_slope(self, slope="RIS"):
        self.scope.write(f"SLO {slope}")

    def set_trigger_coupling(self, coupling="AC"):
        self.scope.write(f"COUP {coupling}")

    def set_trigger_mode(self, mode="AUTO"):
        self.scope.write(f"MODE {mode}")

    def set_trigger_holdoff(self, holdoff=0.0):
        self.scope.write(f"TRIG:MAI:HOLDO:VAL {holdoff}")

    def set_trigger_level(self, level=0.0):
        self.scope.write(f"TRIG:MAIN:LEV {level}")

    def set_acquisition_mode(self, mode="SAM"):
        self.scope.write(f"ACQ:MODE {mode}")

    def set_number_of_averages(self, num_av=64):
        self.scope.write(f"NUMAV {num_av}")

    def reset_to_default(self):
        self.scope.write("*RST")
        self.scope.write(":HEADER OFF;*ESE 60;*SRE 32;*CLS;")
