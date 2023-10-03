import pyvisa
import threading
from smponpol.dataclasses import variable_list, range_selector_window
import numpy as np
import dearpygui.dearpygui as dpg

from smponpol.instruments import LinkamHotstage, Agilent33220A, Rigol4204
from smponpol.dataclasses import SponState, SponInstruments
VIEWPORT_WIDTH = 1920
DRAW_HEIGHT = 1080-40
VIEWPORT_HEIGHT = DRAW_HEIGHT - 40


class SMPonpolUI:
    def __init__(self):
        self.output_file_window = OutputFileWindow()
        self.temperature_window = TemperatureWindow()
        self.frequency_window = FrequencyWindow()
        self.voltage_window = VoltageWindow()
        self.instrument_control_window = InstrumentControlWindow()
        self.results_window = ResultsWindow()
        self.temperature_log_window = TemperatureLogWindow()

    def redraw_windows(self, viewport_height, viewport_width):
        dpg.configure_item(self.output_file_window.output_file_window,
                           pos=[viewport_width/2, 0],
                           width=viewport_width/2,
                           height=viewport_height/7)

        dpg.configure_item(self.temperature_window.temperature_window,
                           pos=[0, viewport_height/4],
                           width=viewport_width/6,
                           height=viewport_height/4)

        dpg.configure_item(self.frequency_window.frequency_window,
                           pos=[viewport_width/6, viewport_height/4],
                           width=viewport_width/6,
                           height=viewport_height/4)




    def extra_config(self, state: SponState, instruments: SponInstruments):
        dpg.configure_item(
            self.instrument_control_window.linkam_initialise,
            callback=connect_to_instrument_callback,
            user_data={
                "instrument": "linkam",
                "frontend": self, "instruments": instruments,
                "state": state,
            },
        )
        dpg.configure_item(
            self.instrument_control_window.agilent_initialise,
            callback=connect_to_instrument_callback,
            user_data={
                "instrument": "agilent",
                "frontend": self,
                "instruments": instruments,
                "state": state,
            },
        )
        dpg.configure_item(
            self.instrument_control_window.rigol_initialise,
            callback=connect_to_instrument_callback,
            user_data={
                "instrument": "rigol",
                "frontend": self,
                "instruments": instruments,
                "state": state,
            },
        )


class InstrumentControlWindow:
    def __init__(self):
        self.linkam_status = "Disconnected"
        self.agilent_status = "Disconnected"
        self.rigol_status = "Disconnected"
        with dpg.window(label="Status Window",
                        pos=[0, 0],
                        width=VIEWPORT_WIDTH/2,
                        height=VIEWPORT_HEIGHT/4,
                        no_collapse=True,
                        no_close=True,):

            with dpg.group(horizontal=True):
                dpg.add_text("Linkam: ")
                self.linkam_status = dpg.add_text(
                    f"{self.linkam_status}", tag="linkam_status_display"
                )
                self.linkam_com_selector = dpg.add_combo(width=200)
                self.linkam_initialise = dpg.add_button(
                    label="Initialise",
                )

            with dpg.group(horizontal=True):
                dpg.add_text("Waveform generator: ")
                self.agilent_status = dpg.add_text(
                    f"{self.agilent_status}", tag="agilent_status_display"
                )
                self.agilent_com_selector = dpg.add_combo(width=200)
                self.agilent_initialise = dpg.add_button(
                    label="Initialise",
                )
            with dpg.group(horizontal=True):
                dpg.add_text("Oscilloscope (RIGOL): ")
                self.rigol_status = dpg.add_text(
                    f"{self.rigol_status}", tag="rigol_status_display"
                )
                self.rigol_com_selector = dpg.add_combo(width=200)
                self.rigol_initialise = dpg.add_button(
                    label="Initialise",
                )

        self.rigol_parameter_window = RigolParameterWindow()


class FrequencyWindow:
    def __init__(self):
        with dpg.window(
            label="Frequency List",
            width=VIEWPORT_WIDTH / 6,
            height=VIEWPORT_HEIGHT / 4,
            pos=[VIEWPORT_WIDTH/6, VIEWPORT_HEIGHT/4],
            no_collapse=True,
            no_close=True,
        ) as self.frequency_window:
            with dpg.group(horizontal=True):
                self.frequency_list = variable_list(
                    *make_variable_list_frame(1000.0, 1e-6, 20e6)
                )


class VoltageWindow:
    def __init__(self):
        with dpg.window(
            label="Voltage List",
            width=VIEWPORT_WIDTH/6,
            height=VIEWPORT_HEIGHT/4,
            pos=[2*VIEWPORT_WIDTH/6, VIEWPORT_HEIGHT/4],
            no_collapse=True,
            no_close=True,
        ) as self.voltage_window:

            with dpg.group(horizontal=True):
                self.voltage_list = variable_list(
                    *make_variable_list_frame(0.01, 0.01, 10))


class TemperatureWindow:
    def __init__(self):

        with dpg.window(
            label="Temperature List",
            width=VIEWPORT_WIDTH / 6,
            height=VIEWPORT_HEIGHT / 4,
            pos=[0, VIEWPORT_HEIGHT/4],
            no_collapse=True,
            no_close=True,
        ) as self.temperature_window:
            with dpg.group(horizontal=True):
                self.temperature_list = variable_list(
                    *make_variable_list_frame(25.0, -40, 250)
                )
                # with dpg.group():
                #     with dpg.group(horizontal=True):
                #         self.go_to_temp_button = dpg.add_button(label="Go to:")
                #         self.go_to_temp_input = dpg.add_input_float(
                #             default_value=25, width=150
                #         )
                #         dpg.add_text("°C")
                #     with dpg.group(horizontal=True):
                #         dpg.add_text("Rate (°C/min): ")
                #         self.T_rate = dpg.add_input_double(
                #             default_value=10, width=150
                #         )
                #     with dpg.group(horizontal=True):
                #         dpg.add_text("Stab. Time (s)")
                #         self.stab_time = dpg.add_input_double(
                #             default_value=1, width=150
                #         )


class RigolParameterWindow:
    def __init__(self):
        with dpg.window(
            label="RIGOL parameters",
            width=VIEWPORT_WIDTH/4,
            height=VIEWPORT_HEIGHT/4,
            pos=[0, VIEWPORT_HEIGHT/4-125],
            collapsed=True
        ):
            with dpg.group(horizontal=True):
                dpg.add_text("Memory Depth: ")
                self.memory_depth_combo = dpg.add_combo(items=["1k", "10k", "100k", "1M", "10M", "25M", "50M", "100M", "125M"],
                                                        default_value="10k")

            with dpg.group(horizontal=True):
                dpg.add_text("Acquisition Type: ")
                self.acquisition_type_combo = dpg.add_combo(items=["Normal", "Average", "Peak Detect", "High Resolution"],
                                                            default_value="Average")

            with dpg.group(horizontal=True):
                dpg.add_text("Number of Averages: ")
                self.averages_combo = dpg.add_combo(items=[2**n for n in range(1, 17, 1)],
                                                    default_value=64)

            with dpg.group(horizontal=True):
                dpg.add_text("Mode: ")
                self.mode_combo = dpg.add_combo(items=["Main", "XY", "Roll"],
                                                default_value="Main")

            with dpg.group(horizontal=True):
                dpg.add_text("Timebase: ")
                self.timebase_input = dpg.add_input_float(default_value=0.0)

            with dpg.group(horizontal=True):
                dpg.add_text("Time Position (ms): ")
                self.time_postion_input = dpg.add_input_float(
                    default_value=0.0)

        with dpg.window(
                label="RIGOL Trigger Settings",
                width=VIEWPORT_WIDTH/4,
                height=VIEWPORT_HEIGHT/4,
                pos=[0, VIEWPORT_HEIGHT/4-100],
                collapsed=True):
            with dpg.group(horizontal=True):
                dpg.add_text("Coupling Mode: ")
                self.coupling_mode_combo = dpg.add_combo(items=["AC", "DC", "LF Reject",
                                                                "HF Reject"], default_value="DC")
            with dpg.group(horizontal=True):
                dpg.add_text("Holdoff time: ")
                self.holdoff_time_combo = dpg.add_input_float(
                    default_value=1e-7)

            with dpg.group(horizontal=True):
                dpg.add_text("Trigger Type: ")
                self.trigger_type_combo = dpg.add_combo(items=["Edge", "Pulse", "Runt", "Windows", "Nth Edge", "Slope", "Video",
                                                               "Pattern", "Delay", "Timeout", "Duration", "Setup/Hold", "RS232", "SPI"],
                                                        default_value="Edge")

            with dpg.group(horizontal=True):
                dpg.add_text("Trigger Mode: ")
                self.trigger_mode_combo = dpg.add_combo(items=["Auto", "Normal", "Single"],
                                                        default_value="Auto")

            with dpg.group(horizontal=True):
                dpg.add_text("Trigger Channel: ")
                self.trigger_channel_combo = dpg.add_combo(items=["Channel 1", "Channel 2",
                                                                  "Channel 3", "Channel 4"], default_value="Channel 1")

            with dpg.group(horizontal=True):
                dpg.add_text("Trigger Level (V): ")
                self.trigger_level_input = dpg.add_input_float(
                    default_value=0.0)

            with dpg.group(horizontal=True):
                dpg.add_text("Trigger Slope: ")
                self.trigger_slope_combo = dpg.add_combo(items=["Rising", "Falling",
                                                                "Either"], default_value="Rising")
        self.channel_windows = []
        for i in range(4):
            self.channel_windows.append(RigolChannelWindow(i))


class RigolChannelWindow:
    def __init__(self, channel):
        with dpg.window(label=f"RIGOL Channel {channel+1}",
                        width=VIEWPORT_WIDTH/8,
                        height=VIEWPORT_HEIGHT/4,
                        pos=[channel*VIEWPORT_WIDTH/8, 3*VIEWPORT_HEIGHT/4]):
            dpg.add_text("Coupling Mode:")
            dpg.add_combo(items=["DC", "GND", "AC"], default_value="DC")
            dpg.add_text("Probe Attenuation:")
            dpg.add_combo(items=[0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5,
                          10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000], default_value=1)
            dpg.add_text("Vertical Range:")
            dpg.add_input_float(default_value=0.0)
            dpg.add_text("Vertical Offset:")
            dpg.add_input_float(default_value=0.0)
            dpg.add_button(label="Enable")


class OutputFileWindow:
    def __init__(self):
        with dpg.window(label="Output File Settings",
                        pos=[VIEWPORT_WIDTH/2, 0],
                        width=VIEWPORT_WIDTH/2,
                        height=VIEWPORT_HEIGHT/7,
                        no_collapse=True,
                        no_close=True,) as self.output_file_window:
            with dpg.group(horizontal=True):
                dpg.add_text(f"{'Folder':>15}: ")
                self.output_folder = dpg.add_input_text(
                    default_value=".\\Data")
                dpg.add_button(label="Browse",
                               callback=lambda: dpg.show_item("folder_dialog"))
            with dpg.group(horizontal=True):
                dpg.add_text(f"{'Sample Name':>15}: ")
                self.sample_name = dpg.add_input_text(default_value="Sample 1")
            with dpg.group(horizontal=True):
                dpg.add_text(f"{'Cell Type':>15}: ")
                self.cell_type = dpg.add_input_text(default_value="HG")
            with dpg.group(horizontal=True):
                dpg.add_text(f"{'Cell Thickness':>15}: ")
                self.cell_thickness = dpg.add_input_text(default_value="5um")

        dpg.add_file_dialog(
            directory_selector=True,
            show=False,
            callback=saveas_folder_callback,
            user_data=self.output_folder,
            id="folder_dialog",
            width=700,
            height=400
        )


class ResultsWindow:
    def __init__(self):
        with dpg.window(label="Results",
                        width=VIEWPORT_WIDTH/2,
                        height=3*VIEWPORT_HEIGHT/7,
                        pos=[VIEWPORT_WIDTH/2, VIEWPORT_HEIGHT/7]):

            with dpg.plot(height=3*VIEWPORT_HEIGHT/7,
                          width=VIEWPORT_WIDTH/2,
                          anti_aliased=True):
                self.time_axis = dpg.add_plot_axis(
                    dpg.mvXAxis, label="time (s)")
                self.voltage_axis = dpg.add_plot_axis(
                    dpg.mvYAxis, label="V")

                self.results = dpg.add_scatter_series(
                    x=[], y=[], parent=self.voltage_axis)


class TemperatureLogWindow:
    def __init__(self):
        with dpg.window(label="Temperature Log",
                        width=VIEWPORT_WIDTH/2,
                        height=3*VIEWPORT_HEIGHT/7,
                        pos=[VIEWPORT_WIDTH/2, 4*VIEWPORT_HEIGHT/7]):
            with dpg.plot(height=3*VIEWPORT_HEIGHT/7,
                          width=VIEWPORT_WIDTH/2,
                          anti_aliased=True):
                self.time_axis = dpg.add_plot_axis(
                    dpg.mvXAxis, label="time (s)")
                self.temperature_axis = dpg.add_plot_axis(
                    dpg.mvYAxis, label="Temperature (C)")
                self.temperature_log = dpg.add_line_series(
                    x=[], y=[], parent=self.temperature_axis)


def init_linkam(
    frontend: SMPonpolUI,
    instruments: SponInstruments,
    state: SponState
) -> None:
    linkam = LinkamHotstage(dpg.get_value(
        frontend.instrument_control_window.linkam_com_selector))
    try:
        linkam.current_temperature()
        dpg.set_value(frontend.linkam_status, "Connected")
        dpg.hide_item(frontend.linkam_initialise)
        instruments.linkam = linkam

        state.linkam_connection_status = "Connected"
        with open("address.dat", "w") as f:
            f.write(dpg.get_value(
                frontend.instrument_control_window.linkam_com_selector))

    except pyvisa.errors.VisaIOError:
        dpg.set_value(frontend.linkam_status, "Couldn't connect")


def init_agilent(
    frontend: SMPonpolUI, instruments: SponInstruments, state: SponState
) -> None:
    agilent = Agilent33220A(dpg.get_value(
        frontend.instrument_control_window.agilent_com_selector))
    dpg.set_value(
        frontend.instrument_control_window.agilent_status, "Connected")
    dpg.hide_item(frontend.instrument_control_window.agilent_initialise)
    instruments.agilent = agilent
    state.agilent_connection_status = "Connected"


def init_rigol(
    frontend: SMPonpolUI, instruments: SponInstruments, state: SponState
) -> None:
    rigol = Rigol4204(dpg.get_value(
        frontend.instrument_control_window.rigol_com_selector))
    dpg.set_value(frontend.instrument_control_window.rigol_status, "Connected")
    dpg.hide_item(frontend.instrument_control_window.rigol_initialise)
    instruments.rigol = rigol
    state.rigol_connection_status = "Connected"


def connect_to_instrument_callback(sender, app_data, user_data):
    if user_data["instrument"] == "linkam":
        thread = threading.Thread(
            target=init_linkam,
            args=(user_data["frontend"],
                  user_data["instruments"], user_data["state"]),
        )
    elif user_data["instrument"] == "agilent":
        thread = threading.Thread(
            target=init_agilent,
            args=(user_data["frontend"],
                  user_data["instruments"], user_data["state"])
        )
    elif user_data["instrument"] == "rigol":
        thread = threading.Thread(
            target=init_rigol,
            args=(user_data["frontend"],
                  user_data["instruments"], user_data["state"])
        )

    thread.daemon = True
    thread.start()


def saveas_folder_callback(sender, app_data, output_file_path):
    dpg.set_value(output_file_path, app_data["file_path_name"])


def make_variable_list_frame(default_val, min_val, max_val, logspace=False):
    window_height = 300
    window_width = 250
    with dpg.window(
        label="Range Selector",
        height=window_height,
        width=window_width,
        modal=True,
        pos=[
            (VIEWPORT_WIDTH - window_width) / 2,
            (VIEWPORT_HEIGHT - window_height) / 2,
        ],
    ) as window_tag:
        with dpg.group() as range_selector_group:
            dpg.add_text("Mode:")
            spacing_combo = dpg.add_combo(
                ["Step Size",
                    "Number of Points (Linear)", "Number of Points (Log)"],
                default_value="Number of Points (Linear)",
            )
            spacing_label = dpg.add_text("Number of Points:")
            number_of_points_input = dpg.add_input_int(default_value=10)
            spacing_input = dpg.add_input_double(default_value=0.1)
            dpg.add_text("Minimum Value:")
            min_value_input = dpg.add_input_double(default_value=min_val)
            dpg.add_text("Maximum Value:")
            max_value_input = dpg.add_input_double(default_value=max_val)

            dpg.hide_item(spacing_input)

            dpg.configure_item(
                spacing_combo,
                callback=change_spacing_callback,
                user_data={
                    "spacing_label": spacing_label,
                    "number_of_points_input": number_of_points_input,
                    "spacing_input": spacing_input,
                },
            )

            range_selector = range_selector_window(
                window_tag,
                spacing_combo,
                number_of_points_input,
                spacing_input,
                spacing_label,
                min_value_input,
                max_value_input,
            )

    dpg.hide_item(window_tag)

    with dpg.group(horizontal=True):
        listbox_handle = dpg.add_listbox(
            ["1:\t" + str(default_val)], width=150, num_items=10
        )
        with dpg.group():
            add_text = dpg.add_input_float(
                default_value=default_val, width=150)
            add_button = dpg.add_button(
                label="Add",
                callback=add_value_to_list_callback,
                user_data={"listbox_handle": listbox_handle,
                           "add_text": add_text},
            )
            add_range_button = dpg.add_button(
                label="Add Range", callback=lambda: dpg.show_item(window_tag)
            )
            delete_button = dpg.add_button(
                label="Delete",
                callback=del_value_from_list_callback,
                user_data={"listbox_handle": listbox_handle,
                           "add_text": add_text},
            )

    with dpg.group(parent=range_selector_group, horizontal=True):
        dpg.add_button(
            label="Append",
            callback=append_range_to_list_callback,
            user_data={
                "range_selector": range_selector,
                "listbox_handle": listbox_handle,
            },
        )
        dpg.add_button(
            label="Replace",
            callback=replace_list_callback,
            user_data={
                "range_selector": range_selector,
                "listbox_handle": listbox_handle,
            },
        )

    return (
        listbox_handle,
        add_text,
        add_button,
        add_range_button,
        delete_button,
        range_selector,
    )


def change_spacing_callback(sender, app_data, user_data):
    if dpg.get_value(sender) == "Step Size":
        dpg.set_value(user_data["spacing_label"], "Step Size:")
        dpg.show_item(user_data["spacing_input"])
        dpg.hide_item(user_data["number_of_points_input"])

    elif (
        dpg.get_value(sender) == "Number of Points (Linear)"
        or dpg.get_value(sender) == "Number of Points (Log)"
    ):
        dpg.set_value(user_data["spacing_label"], "Number of Points:")
        dpg.hide_item(user_data["spacing_input"])
        dpg.show_item(user_data["number_of_points_input"])


def add_value_to_list_callback(sender, app_data, user_data):
    current_list = dpg.get_item_configuration(
        user_data["listbox_handle"])["items"]
    if len(current_list) == 0:
        new_item_number = 1
    else:
        new_item_number = int(current_list[-1].split(":")[0]) + 1
    current_list.append(
        f"{new_item_number}:\t" + str(dpg.get_value(user_data["add_text"]))
    )
    dpg.configure_item(user_data["listbox_handle"], items=current_list)


def replace_list_callback(sender, app_data, user_data):
    if (
        dpg.get_value(user_data["range_selector"].spacing_combo)
        == "Number of Points (Linear)"
    ):
        values_to_add = list(
            np.linspace(
                dpg.get_value(user_data["range_selector"].min_value_input),
                dpg.get_value(user_data["range_selector"].max_value_input),
                dpg.get_value(
                    user_data["range_selector"].number_of_points_input),
            )
        )

    elif (
        dpg.get_value(user_data["range_selector"].spacing_combo)
        == "Number of Points (Log)"
    ):
        values_to_add = list(
            np.logspace(
                np.log10(dpg.get_value(
                    user_data["range_selector"].min_value_input)),
                np.log10(dpg.get_value(
                    user_data["range_selector"].max_value_input)),
                dpg.get_value(
                    user_data["range_selector"].number_of_points_input),
            )
        )
    else:
        values_to_add = list(
            np.arange(
                dpg.get_value(user_data["range_selector"].min_value_input),
                dpg.get_value(
                    user_data["range_selector"].max_value_input)
                + dpg.get_value(user_data["range_selector"].spacing_input),
                dpg.get_value(user_data["range_selector"].spacing_input),
            )
        )

    new_list_numbered = [f"{i+1}:\t{x}" for i, x in enumerate(values_to_add)]

    dpg.configure_item(user_data["listbox_handle"], items=new_list_numbered)


def append_range_to_list_callback(sender, app_data, user_data):
    current_list = dpg.get_item_configuration(
        user_data["listbox_handle"])["items"]

    if (
        dpg.get_value(user_data["range_selector"].spacing_combo)
        == "Number of Points (Linear)"
    ):
        values_to_add = list(
            np.linspace(
                dpg.get_value(user_data["range_selector"].min_value_input),
                dpg.get_value(user_data["range_selector"].max_value_input),
                dpg.get_value(
                    user_data["range_selector"].number_of_points_input),
            )
        )

    elif (
        dpg.get_value(user_data["range_selector"].spacing_combo)
        == "Number of Points (Log)"
    ):
        values_to_add = list(
            np.logspace(
                np.log10(dpg.get_value(
                    user_data["range_selector"].min_value_input)),
                np.log10(dpg.get_value(
                    user_data["range_selector"].max_value_input)),
                dpg.get_value(
                    user_data["range_selector"].number_of_points_input),
            )
        )

    else:
        values_to_add = list(
            np.arange(
                dpg.get_value(user_data["range_selector"].min_value_input),
                dpg.get_value(
                    user_data["range_selector"].max_value_input)
                + dpg.get_value(user_data["range_selector"].spacing_input),
                dpg.get_value(user_data["range_selector"].spacing_input),
            )
        )

    new_list = current_list + [
        f"{i+1+len(current_list)}:\t{x}" for i, x in enumerate(values_to_add)
    ]

    dpg.configure_item(user_data["listbox_handle"], items=new_list)


def del_value_from_list_callback(sender, app_data, user_data):
    current_list = dpg.get_item_configuration(
        user_data["listbox_handle"])["items"]
    if len(current_list) == 0:
        return
    selected_item = dpg.get_value(user_data["listbox_handle"])
    current_list.remove(selected_item)
    new_list = [f"{i+1}:{x.split(':')[1]}" for i, x in enumerate(current_list)]
    dpg.configure_item(user_data["listbox_handle"], items=new_list)
