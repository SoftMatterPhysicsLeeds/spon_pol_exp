import dearpygui.dearpygui as dpg
from smponpol.ui import lcd_ui
from smponpol.excel_writer import make_excel
from smponpol.dataclasses import lcd_instruments, lcd_state, Status, OutputType
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
        print(f"Could not write {command_string} to {instrument}: ",e) 



def start_measurement(
    state: lcd_state, frontend: lcd_ui, instruments: lcd_instruments
) -> None:

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

    state.T_list = [round(x, 1) for x in state.T_list]

    instruments.agilent.set_waveform() # default is triangle
    instruments.agilent.set_voltage_unit() # default is VRMS
    instruments.agilent.set_output_load() # default is INF
    instruments.agilent.set_voltage(dpg.get_value(frontend.voltage_input))
    instruments.agilent.set_frequency(dpg.get_value(frontend.frequency_input))
    instruments.agilent.set_symmetry()
    instruments.agilent.set_output('ON')




    state.T_step = 0 

    T_str =f"{state.T_step + 1}: {state.T_list[state.T_step]}"

    state.resultsDict[T_str] = dict()
    state.resultsDict[T_str]["time"] = []
    state.resultsDict[T_str]["channel1"] = []
    state.resultsDict[T_str]["channel2"] = []
    

    state.measurement_status = Status.SET_TEMPERATURE
    state.xdata = []
    state.ydata = []


def stop_measurement(instruments: lcd_instruments, state: lcd_state, frontend: lcd_ui) -> None:
    instruments.hotstage.stop()
    state.measurement_status = Status.IDLE


def init_agilent(
    frontend: lcd_ui, instruments: lcd_instruments, state: lcd_state
) -> None:
    if instruments.agilent:
        instruments.agilent.close()
    agilent = Agilent33220A(dpg.get_value(frontend.agilent_com_selector))
    dpg.set_value(frontend.agilent_status, "Connected")
    dpg.configure_item(frontend.agilent_initialise, label = "Reconnect")
    instruments.agilent = agilent
    state.agilent_connection_status = "Connected"

def init_oscilloscope(
    frontend: lcd_ui, instruments: lcd_instruments, state: lcd_state
) -> None:
    if instruments.oscilloscope:
        instruments.oscilloscope.close()

    instruments.oscilloscope = Rigol4204(dpg.get_value(frontend.oscilloscope_com_selector))
    dpg.set_value(frontend.oscilloscope_status, "Connected")
    dpg.configure_item(frontend.oscilloscope_initialise, label = "Reconnect")
    
    state.oscilloscope_connection_status = "Connected"
    # oscilloscope.write(":AUToscale")
    instruments.oscilloscope.init_scope_defaults()

def init_hotstage(
    frontend: lcd_ui, instruments: lcd_instruments, state: lcd_state
) -> None:
    hotstage = Instec(dpg.get_value(frontend.hotstage_com_selector))
    try:
        hotstage.get_temperature()
        dpg.set_value(frontend.hotstage_status, "Connected")
        dpg.hide_item(frontend.hotstage_initialise)
        instruments.hotstage = hotstage
        state.hotstage_connection_status = "Connected"
        with open("address.dat", "w") as f:
            f.write(dpg.get_value(frontend.hotstage_com_selector))

    except pyvisa.errors.VisaIOError:
        dpg.set_value(frontend.hotstage_status, "Couldn't connect")


def connect_to_instrument_callback(sender, app_data, user_data):
    if user_data["instrument"] == "hotstage":
        thread = threading.Thread(
            target=init_hotstage,
            args=(user_data["frontend"], user_data["instruments"], user_data["state"]),
        )
    elif user_data["instrument"] == "agilent":
        thread = threading.Thread(
            target=init_agilent,
            args=(user_data["frontend"], user_data["instruments"], user_data["state"]),
        )

    elif user_data["instrument"] == 'oscilloscope':
        thread = threading.Thread(
            target=init_oscilloscope,
            args=(user_data["frontend"], user_data["instruments"], user_data["state"]),
        )

    thread.daemon = True
    thread.start()


def handle_measurement_status(
    state: lcd_state, frontend: lcd_ui, instruments: lcd_instruments
):
    current_wait = 0
    if state.measurement_status == Status.IDLE:
        dpg.set_value(frontend.measurement_status, "Idle")
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
            frontend.measurement_status, f"Going to {state.T_list[state.T_step]} C"
        )
    elif state.measurement_status == Status.GOING_TO_TEMPERATURE and (
        state.hotstage_temperature > state.T_list[state.T_step] - 0.1
        and state.hotstage_temperature < state.T_list[state.T_step] + 0.1
    ):
        state.t_stable_start = time.time()
        state.measurement_status = Status.STABILISING_TEMPERATURE

    elif state.measurement_status == Status.STABILISING_TEMPERATURE:
        current_wait = time.time() - state.t_stable_start
        dpg.set_value(
            frontend.measurement_status,
            f"Stabilising temperature for {current_wait:.2f}/{dpg.get_value(frontend.stab_time)}s",
        )
        if current_wait >= dpg.get_value(frontend.stab_time):
            state.measurement_status = Status.TEMPERATURE_STABILISED

    elif state.measurement_status == Status.TEMPERATURE_STABILISED:
        state.measurement_status = Status.COLLECTING_DATA
        take_data(frontend, instruments, state)

    elif state.measurement_status == Status.COLLECTING_DATA:

       
            dpg.set_value(
                frontend.measurement_status,
                "Taking data"
            )

        

    elif state.measurement_status == Status.FINISHED:
        instruments.hotstage.stop()
        instruments.agilent.set_output('OFF')
        state.measurement_status = Status.IDLE
        dpg.set_value(frontend.measurement_status, "Idle")


def find_instruments(frontend: lcd_ui):
    dpg.set_value(frontend.measurement_status, "Finding Instruments...")
    rm = pyvisa.ResourceManager()
    visa_resources = rm.list_resources('?*')
    

    usb_selector = [x for x in visa_resources if x.split("::")[0] == "USB0"]

    rigol_addresses = [x for x in usb_selector if x.split("::")[1] == "0x1AB1"]
    agilent_addresses = [x for x in usb_selector if x.split("::")[1] == "0x0957"]
    instec_addresses = [x for x in usb_selector if x.split("::")[1] == "0x03EB"]

    dpg.configure_item(frontend.hotstage_com_selector, items=instec_addresses)
    dpg.configure_item(frontend.agilent_com_selector, items=agilent_addresses)
    dpg.configure_item(frontend.oscilloscope_com_selector, items=rigol_addresses)

    dpg.set_value(frontend.hotstage_com_selector, instec_addresses[0])
    dpg.set_value(frontend.agilent_com_selector,agilent_addresses[0] )
    dpg.set_value(frontend.oscilloscope_com_selector,rigol_addresses[0])

    dpg.set_value(frontend.measurement_status, "Found instruments!")
    dpg.set_value(frontend.measurement_status, "Idle")


def take_data(
    frontend: lcd_ui, instruments: lcd_instruments, state: lcd_state
) -> None:
    thread = threading.Thread(
        target=run_experiment, args=(frontend, instruments, state)
    )
    thread.daemon = True
    thread.start()


def run_experiment(frontend: lcd_ui, instruments: lcd_state, state: lcd_state):
    result = dict()

    time.sleep(2)

    depth = dpg.get_value(frontend.memory_depth_selector)
    averages = dpg.get_value(frontend.num_averages)

    # depth = "10k"
    # averages = 64
    
    # instruments.oscilloscope.initialise_channel(channel=1)
    # instruments.oscilloscope.initialise_channel(channel=2)

    times, data = instruments.oscilloscope.get_channel_trace(1,averages,depth)
    _, data2 =  instruments.oscilloscope.get_channel_trace(2,averages,depth)

    result["time"] = times
    result["channel1"] = data
    result["channel2"] = data2
    
    get_result(result, state, frontend, instruments) 


def read_temperature(frontend: lcd_ui, instruments: lcd_instruments, state: lcd_state):
    log_time = 0
    time_step = 0.05
    while True:
        temperature = instruments.hotstage.get_temperature()
        
        state.hotstage_temperature = temperature
        dpg.set_value(
            frontend.hotstage_status, f"T: {temperature:.2f}"
        )
        state.T_log_time.append(log_time)
        state.T_log_T.append(temperature)

        if len(state.T_log_T) == 1000:
            state.T_log_T = state.T_log_T[1:]
            state.T_log_time = state.T_log_time[1:]

        # state.hotstage_action = status
        time.sleep(time_step)
        log_time += time_step


def export_data_file(frontend: lcd_ui, state: lcd_state, times, channel1, channel2):
    output_filename = frontend.output_filename + f"{dpg.get_value(frontend.voltage_input)} Volts" + \
        f"{dpg.get_value(frontend.frequency_input)} Hz" + \
        f"{state.temperature_list[state.temperature_step]} C.dat"

    with open(output_filename, 'w') as f:
        f.write("time\tChannel1\tChannel2\n")
        for time_inc, channel1, channel2 in zip(times, channel1, channel2):
            f.write(f"{time_inc}\t{channel1}\t{channel2}\n")

def get_result(
    result: dict, state: lcd_state, frontend: lcd_ui, instruments: lcd_instruments
) -> None:
    parse_result(result, state, frontend)

    if state.measurement_status == Status.IDLE:
        pass

    else:
        
        

        with open(dpg.get_value(frontend.output_file_path), "w") as write_file:
            json.dump(state.resultsDict, write_file, indent=4)
        
        
        
        if (
            state.T_step == len(state.T_list) - 1
            
        ):
            state.measurement_status = Status.FINISHED

        else:
            if (
                state.volt_step == len(state.voltage_list) - 1
                and state.freq_step == len(state.freq_list) - 1
            ):
                state.T_step += 1
                T_str =f"{state.T_step + 1}: {state.T_list[state.T_step]}"
    
                state.resultsDict[T_str] = dict()
                state.resultsDict[T_str]["time"] = []
                state.resultsDict[T_str]["channel1"] = []
                state.resultsDict[T_str]["channel2"] = []
                
                state.measurement_status = Status.SET_TEMPERATURE


def parse_result(result: dict, state: lcd_state, frontend: lcd_ui) -> None:
    T_str =f"{state.T_step + 1}: {state.T_list[state.T_step]}"
    state.resultsDict[T_str]["time"] = result["time"]
    state.resultsDict[T_str]["channel1"] = result["channel1"]
    state.resultsDict[T_str]["channel2"] = result["channel2"]


    dpg.set_value(frontend.results_plot, [result["time"], result["channel1"]])
    dpg.set_value(frontend.results_plot2, [result["time"], result["channel2"]])
    
    

    # dpg.set_axis_limits(
    #     frontend.results_V_axis,
    #     min(result["channel2"]) - 0.1 * min(result["channel2"]),
    #     max(result["channel2"]) + 0.1 * max(result["channel2"]),
    # )
    # dpg.set_axis_limits(
    #     frontend.results_time_axis,
    #     min(result["time"]) - 0.1,
    #     max(result["time"]) + 0.1,
    # )
