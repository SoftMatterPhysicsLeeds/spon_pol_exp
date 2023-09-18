import pyvisa
import threading
from smponpol.dataclasses import variable_list, range_selector_window
import numpy as np
import dearpygui.dearpygui as dpg

from smponpol.instruments import LinkamHotstage
from smponpol.dataclasses import SponState, SponInstruments
VIEWPORT_WIDTH = 1280
DRAW_HEIGHT = 850
VIEWPORT_HEIGHT = DRAW_HEIGHT - 40


class SMPonpolUI:
    def __init__(self):
        self.output_file_window = OutputFileWindow()
        self.temperature_window = TemperatureWindow()
        self.instrument_control_window = InstrumentControlWindow()

    def extra_config(self, state: SponState, instruments: SponInstruments):
        dpg.configure_item(
            self.linkam_initialise,
            callback=connect_to_instrument_callback,
            user_data={
                "instrument": "linkam",
                "frontend": self,
                "instruments": instruments,
                "state": state,
            },
        )


class InstrumentControlWindow:
    def __init__(self):
        self.linkam_status = "Idle"
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


class OutputFileWindow:
    def __init__(self):
        with dpg.window(label="Output File Settings",
                        pos=[VIEWPORT_WIDTH/2, 0],
                        width=VIEWPORT_WIDTH/2,
                        height=VIEWPORT_HEIGHT/4,
                        no_collapse=True,
                        no_close=True,):
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
                self.sample_name = dpg.add_input_text(default_value="HG")
            with dpg.group(horizontal=True):
                dpg.add_text(f"{'Cell Thickness':>15}: ")
                self.sample_name = dpg.add_input_text(default_value="5um")

        dpg.add_file_dialog(
            directory_selector=True,
            show=False,
            callback=saveas_folder_callback,
            user_data=self.output_folder,
            id="folder_dialog",
            width=700,
            height=400
        )


class TemperatureWindow:
    def __init__(self):

        with dpg.window(
            label="Temperature List",
            width=VIEWPORT_WIDTH / 2,
            height=VIEWPORT_HEIGHT / 4,
            pos=[0, VIEWPORT_HEIGHT/4],
            no_collapse=True,
            no_close=True,
        ):
            with dpg.group(horizontal=True):
                self.temperature_list = variable_list(
                    *make_variable_list_frame(25.0, -40, 250)
                )
                with dpg.group():
                    with dpg.group(horizontal=True):
                        self.go_to_temp_button = dpg.add_button(label="Go to:")
                        self.go_to_temp_input = dpg.add_input_float(
                            default_value=25, width=150
                        )
                        dpg.add_text("°C")
                    with dpg.group(horizontal=True):
                        dpg.add_text("Rate (°C/min): ")
                        self.T_rate = dpg.add_input_double(
                            default_value=10, width=150
                        )
                    with dpg.group(horizontal=True):
                        dpg.add_text("Stab. Time (s)")
                        self.stab_time = dpg.add_input_double(
                            default_value=1, width=150
                        )


def init_linkam(
    frontend: SMPonpolUI,
    instruments: SponInstruments,
    state: SponState
) -> None:
    linkam = LinkamHotstage(dpg.get_value(frontend.linkam_com_selector))
    try:
        linkam.current_temperature()
        dpg.set_value(frontend.linkam_status, "Connected")
        dpg.hide_item(frontend.linkam_initialise)
        instruments.linkam = linkam

        state.linkam_connection_status = "Connected"
        with open("address.dat", "w") as f:
            f.write(dpg.get_value(frontend.linkam_com_selector))

    except pyvisa.errors.VisaIOError:
        dpg.set_value(frontend.linkam_status, "Couldn't connect")


def connect_to_instrument_callback(sender, app_data, user_data):
    if user_data["instrument"] == "linkam":
        thread = threading.Thread(
            target=init_linkam,
            args=(user_data["frontend"],
                  user_data["instruments"], user_data["state"]),
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
