from smponpol.ui import SMPonpolUI
from smponpol.dataclasses import SponState, SponInstruments
import dearpygui.dearpygui as dpg
import pyvisa
import time
import threading


def find_instruments(frontend: SMPonpolUI):
    # com_selector = [x.__str__() for x  in list_ports.comports()]

    #    dpg.set_value(frontend.measurement_status, "Finding Instruments...")
    rm = pyvisa.ResourceManager()
    visa_resources = rm.list_resources()

    com_selector = [x for x in visa_resources if x.split("::")[
        0][0:4] == "ASRL"]
    usb_selector = [x for x in visa_resources if x.split("::")[
        0][0:3] == "USB"]

    dpg.configure_item(
        frontend.instrument_control_window.linkam_com_selector, items=com_selector)
    dpg.configure_item(
        frontend.instrument_control_window.agilent_com_selector, items=usb_selector)
    dpg.configure_item(
        frontend.instrument_control_window.rigol_com_selector, items=usb_selector)

    # dpg.set_value(frontend.measurement_status, "Found instruments!")
    # dpg.set_value(frontend.measurement_status, "Idle")


def read_temperature(frontend: SMPonpolUI, instruments: SponInstruments, state: SponState):
    log_time = 0
    time_step = 0.05
    while True:
        temperature, status = instruments.linkam.current_temperature()
        if temperature == 0.0:
            continue
        dpg.set_value(
            frontend.instrument_control_window.linkam_status, f"T: {str(temperature)}, Status: {status}"
        )
        state.temperature_log_time.append(log_time)
        state.temperature_log_temperature.append(temperature)

        if len(state.T_log_T) == 1000:
            state.temperature_log_temperature = state.temperature_log_temperature[1:]
            state.temperature_log_time = state.temperature_log_time[1:]

        dpg.set_value(frontend.temperature_log, [
                      state.temperature_log_time, state.temperature_log_temperature])
        dpg.set_axis_limits(
            frontend.temperature_log_window.temperature_axis,
            min(state.T_log_T) - 0.2,
            max(state.T_log_T) + 0.2,
        )
        dpg.fit_axis_data(frontend.temperature_log_window.time_axis)

        state.linkam_action = status
        time.sleep(time_step)
        log_time += time_step


def start_measurement(state: SponState, frontend: SMPonpolUI, instruments: SponInstruments):
    state.freq_list = [
        float(x.split("\t")[1])
        for x in dpg.get_item_configuration(frontend.frequency_window.frequency_list.list_handle)["items"]
    ]
    state.voltage_list = [
        float(x.split("\t")[1])
        for x in dpg.get_item_configuration(frontend.voltage_window.voltage_list.list_handle)["items"]
    ]
    state.temperature_list = [
        float(x.split("\t")[1])
        for x in dpg.get_item_configuration(frontend.temperature_window.temperature_list.list_handle)[
            "items"
        ]
    ]

    state.temperature_list = [round(x, 2) for x in state.temperature_list]

    state.measurement_status = "Setting temperature"


def update_measurement(state: SponState, frontend: SMPonpolUI, instruments: SponInstruments):

    if state.measurement_status == "Setting temperature" and (state.linkam_action == "Stopped" or state.linkam_action == "Holding"):
        instruments.linkam.set_temperature(
            state.temperature_list[state.temperature_step], 10
        )
        state.measurement_status = f"Going to T: {state.temperature_list[state.temperature_step]}"

    elif (
            state.measurement_status == f"Going to T: {state.temperature_list[state.temperature_step]}" and state.linkam_action == "Holding"):

        state.measurement_status = (
            "Stabilising temperature for 10s"
        )

    elif state.measurement_status == "Stabilising temperature for 10s":
        wait_time = time.time() - state.temperature_stable_timer

        if wait_time > 10:
            state.measurement_status = "Temperature Stabilised"
            state.temperature_stable_timer = 0.0
        state.temperature_stable_timer = time.time()

    elif state.measurement_status == "Temperature Stabilised":
        state.measurement_status = "Collecting Data"
        setup_and_run_measurement()


def setup_and_run_measurement(state: SponState, frontend: SMPonpolUI, instruments: SponInstruments):
    thread = threading.Thread(
        target=run_measurement, args=(state, frontend, instruments)
    )
    thread.daemon = True
    thread.start()


def run_measurement(state: SponState, frontend: SMPonpolUI, instruments: SponInstruments):
    instruments.agilent.set_voltage(state.voltage_list[state.voltage_step])
    instruments.agilent.set_frequency(
        state.freq_list[state.frequency_step])
    

