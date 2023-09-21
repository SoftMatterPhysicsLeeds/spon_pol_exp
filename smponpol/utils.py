from smponpol.ui import SMPonpolUI
from smponpol.dataclasses import SponState, SponInstruments
import dearpygui.dearpygui as dpg
import pyvisa


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


def start_measurement(state: SponState, frontend: SMPonpolUI, instruments: SponInstruments):
    state.freq_list = [
        float(x.split("\t")[1])
        for x in dpg.get_item_configuration(frontend.frequency_window.frequency_list.list_handle)["items"]
    ]
    state.voltage_list = [
        float(x.split("\t")[1])
        for x in dpg.get_item_configuration(frontend.voltage_window.voltage_list.list_handle)["items"]
    ]
    state.T_list = [
        float(x.split("\t")[1])
        for x in dpg.get_item_configuration(frontend.temperature_window.temperature_list.list_handle)[
            "items"
        ]
    ]

    state.T_list = [round(x,2) for x in state.T_list]
