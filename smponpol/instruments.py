from typing import Any
import pyvisa
import threading
import time
import struct

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


class Agilent33220A:
    def __init__(self, address):
        rm = pyvisa.ResourceManager()
        self.wfg = rm.open_resource(address)

    def set_waveform(self, waveform="TRI"):
        self.wfg.write(f"FUNC {waveform}")

    def set_frequency(self, frequency=1000.0):
        self.wfg.write(f"FREQ {frequency}")

    def set_voltage(self, voltage=1.0):
        self.wfg.write(f"VOLT {voltage}")

    def set_voltage_unit(self, voltage_unit="VRMS"):
        # options VPP | VRMS | DBM
        self.wfg.write(f"VOLT:UNIT {voltage_unit}")

    def set_dc_offset(self, offset=0):
        self.wfg.write(f"VOLT:OFFS {offset}")

    def set_output(self, output="OFF"):
        self.wfg.write(f"OUTP {output}")

    def set_output_load(self, output="INF"):
        self.wfg.write(f"OUTP:LOAD {output}")

    def close(self):
        self.wfg.close()


class Rigol4204:
    def __init__(self, address):
        rm = pyvisa.ResourceManager()
        self.scope = rm.open_resource(address)
        self.scope.timeout = 100000.0
        self.scope.write(":TIM:HREF:MODE CENT")
        self.scope.write(":TRIG:NREJ ON")

    def init_scope_defaults(self):
        self.set_memory_depth()
        self.set_acquisition_type()
        self.set_number_of_averages()
        self.set_offset()
        self.set_scale()
        self.set_mode()
        self.set_coupling_mode()
        self.set_holdoff_time()
        self.set_trigger_type()
        self.set_trigger_slope()
        self.set_trigger_level()
        self.set_trigger_channel()
        self.set_trigger_mode()


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
        # self.scope.write(":STOP")
        # if channel display is 'off', then don't do anything and just return.
        if int(self.scope.query(":CHAN{channel}:DISP?").strip()) == 0:
            return

        self.scope.write(f":WAV:SOUR CHAN{channel}")
        self.scope.write(":WAV:FORM ASC;:WAV:MODE MAX")
        x_increment = float(self.scope.query("WAV:XINC?"))
        y_increment = float(self.scope.query("WAV:YINC?"))
        y_reference = float(self.scope.query("WAV:YREF?"))
        start_time = float(self.scope.query("WAV:XOR?"))

        self.scope.query(":WAV:DATA?")
        data = self.scope.read()
        if self.scope.query("WAV:MODE?").strip() == "NORM":
            y_reference = y_reference * y_increment
        data = [(float(x) - y_reference) *
                y_increment for x in data.strip().split(',')]
        times = [start_time+(x_increment * x) for x in range(len(data))]

        return times, data

    def close(self):
        self.scope.close()

# operation order for RIGOL (from "Main_program_v1_18_RIGOL.vi"):
# Connect
# set memory depth, offset, scale and mode
class Instec:
    def __init__(self, address):
        rm = pyvisa.ResourceManager()
        self.stage = rm.open_resource(address)
        self.stage.write_termination = ""
        self.stage.read_termination = ""

        self.T = 25.0


    def write_message(self, message):

        print(message)
        
    
        time.sleep(0.05)
        self.stage.write_raw(message)
        time.sleep(0.05)
        response = self.stage.read_raw(55)

        print(response)

        int_list = list(response)

        head_checksum_calculated = (int_list[0] + int_list[1] + int_list[2]) & 0xFF
        data_checksum_calculated = (sum(int_list[4:-1])) & 0xFF

        verify_checksum = head_checksum_calculated == int_list[3] and data_checksum_calculated == int_list[-1]    

        
        # if verify_checksum:
        #     print("Valid response")
        # else: 
        #     print("Invalid response")


        # if int_list[4] == 4:
        #     print("Command Successful")
        # elif int_list[5] == 5:
        #     print("Command Unsuccessful")

        return response


    def write_register(self, register, input):
        head = b"\x7f\x01\x07"
        checksum_1 =  bytes([sum(head) & 0xFF])
        data = b"\x01" + register.to_bytes(1,'big') + b"\x04" + struct.pack('f', input)
        checksum_2 = bytes([sum(data) & 0xFF])

        message = head + checksum_1 + data + checksum_2

        self.write_message(message)
        
    def exec_command(self,command):
        head = b"\x7f\x01\x04"
        checksum_1 =  bytes([sum(head) & 0xFF])
        data = b"\x01\x01\x01" + command.to_bytes(1, 'big')
        checksum_2 = bytes([sum(data) & 0xFF])

        message = head + checksum_1 + data + checksum_2
        self.write_message(message)

    def read_register(self, register):
        head = b"\x7f\x01\x03"
        checksum_1 =  bytes([sum(head) & 0xFF])
        data = b"\x02" + register.to_bytes(1,'big') + b"\x05"
        checksum_2 = bytes([sum(data) & 0xFF])
        message = head + checksum_1 + data + checksum_2

        response = self.write_message(message)
        return response

    def get_temperature(self):

        
        response = self.read_register(4)
        # for some reason, the response to reading a register can be a 'hang-on' from the previous command... 
        # let's cheat and just ignore responses < 8 bytes and throw back the previous T instead.
        if len(response) >= 8:
            self.T = struct.unpack('f',response[7:11])[0]
        
        return self.T
   
    def reset(self):
        self.exec_command(6) # 2 types of reset... this is for comm?
    
    def pause(self):
        self.exec_command(3)

    def hold(self, T):
        self.write_register(8, 25.0) # set TF to T
        self.exec_command(1) # Hold

    def ramp(self, T, rate):
        self.write_register(8, T) # set TF register to T
        self.write_register(18, rate) #set rate register to rate 
        self.exec_command(2) # Ramp

    def stop(self):
        self.exec_command(5) # Stop

    def interpret_response(self, byte_response):
        int_list = list(byte_response)
        response = {}
        
        response['head_flag'] = int_list[0]
        response['slave_board_address'] = int_list[1]
        response['data_length'] = int_list[2]
        response['head_checksum'] = int_list[3]
        response['action'] = int_list[4]
        response['register_address'] = int_list[5]
        response['register_structure_length'] = int_list[6]
        
        # Extract the 5 bytes of register structure content
        register_structure_content = int_list[7:12]
        response['register_structure_content'] = register_structure_content

        # Convert the first 4 bytes of the register structure content to a float
        temp_bytes = bytes(register_structure_content[:4])
        response['temperature'] = struct.unpack('f', temp_bytes)[0]

        # Extract the remaining part of the register structure content
        response['sensor_type'] = register_structure_content[4]

        response['data_checksum'] = int_list[12]
        response['additional_data'] = int_list[13:]
        
        head_checksum_calculated = (int_list[0] + int_list[1] + int_list[2]) & 0xFF
        data_checksum_calculated = (int_list[4] + int_list[5] + int_list[6] + int_list[7] + int_list[8] + int_list[9] + int_list[10] + int_list[11]) & 0xFF
        
        response['head_checksum_valid'] = head_checksum_calculated == int_list[3]
        response['data_checksum_valid'] = data_checksum_calculated == int_list[12]
        
        return response

    def close(self):
        self.stage.close()
