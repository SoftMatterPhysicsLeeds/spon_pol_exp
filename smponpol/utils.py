from smponpol.ui import SMPonpolUI
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
