import pyvisa
import struct
import time


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
