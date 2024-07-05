import numpy as np
import dearpygui.dearpygui as dpg
from smponpol.dataclasses import (
    range_selector_window,
    variable_list,
)
import tkinter as tk
from tkinter import filedialog
import json


VIEWPORT_WIDTH = 1280
DRAW_HEIGHT = 850  # titlebar is approximately 40px
VIEWPORT_HEIGHT = DRAW_HEIGHT - 40
VERTICAL_WIDGET_NUMBER = 4
HEIGHT_DISCREPANCY = int(VIEWPORT_HEIGHT / VERTICAL_WIDGET_NUMBER)


class lcd_ui:
    def __init__(self):
        self.status = "Idle"
        self.linkam_status = "Not Connected"
        self.agilent_status = "Not Connected"
        self.oscilloscope_status = "Not Connected"
        self._make_control_window()
        self._make_graph_windows()
        self.draw_children(VIEWPORT_WIDTH, DRAW_HEIGHT)

        with dpg.theme() as START_THEME:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(
                    dpg.mvThemeCol_Button, (0, 100, 0), category=dpg.mvThemeCat_Core
                )
        with dpg.theme() as STOP_THEME:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(
                    dpg.mvThemeCol_Button, (204, 36, 29), category=dpg.mvThemeCat_Core
                )

        dpg.bind_item_theme(self.start_button, START_THEME)
        dpg.bind_item_theme(self.stop_button, STOP_THEME)

    def draw_children(self, width, height):

        dpg.configure_item(
            self.results_graph, pos=[width / 2, 0], width=width / 2, height=height / 2
        )
        dpg.configure_item(
            self.temperature_log_graph,
            pos=[width / 2, height / 2],
            width=width / 2,
            height=height / 2,
        )

        height_mod = height
        dpg.configure_item(
            self.control_window,
            pos=[0, 0],
            width=width / 2,
            height=0.17 * height_mod,
        )
        dpg.configure_item(
            self.measurement_settings_window,
            pos=[0, 0.17 * height_mod],
            width=width / 2,
            height=0.20 * height_mod,
        )
        dpg.configure_item(
            self.frequency_list_window,
            width=width / 4,
            pos=[0, 0.37 * height_mod],
            height=0.25 * height_mod,
        )
        dpg.configure_item(
            self.voltage_list_window,
            width=width / 4,
            pos=[width / 4, 0.37 * height_mod],
            height=0.25 * height_mod,
        )
        dpg.configure_item(
            self.temperature_list_window,
            width=width / 2,
            height=0.25 * height_mod,
            pos=[0, 0.62 * height_mod],
        )

        dpg.configure_item(
            self.start_stop_button_window,
            pos=[0, 0.87 * height_mod],
            width=width / 2,
            height=0.13 * height_mod,
        )

        dpg.configure_item(
            self.start_button, width=width / 4 - 10, height=-1
        )
        dpg.configure_item(
            self.stop_button, width=width / 4 - 10, height=-1
        )
        dpg.configure_item(self.results_plot_window, height=-1, width=-1)

        dpg.configure_item(
            self.temperature_log_plot_window,
            height=-1,
            width=-1,
        )

    def _make_graph_windows(self):
        with dpg.window(
            label="Results",
            no_collapse=True,
            no_close=True,
            no_resize=True
        ) as self.results_graph:
            with dpg.plot(
                anti_aliased=True,
            ) as self.results_plot_window:
                self.results_V_axis = dpg.add_plot_axis(
                    dpg.mvXAxis, label="voltage (V)", tag="V_axis"
                )
                self.results_Cp_axis = dpg.add_plot_axis(
                    dpg.mvYAxis, label="C_p", tag="Cp_axis"
                )
                # series belong to a y axis. Note the tag name is used in the update
                # function update_data

                self.results_plot = dpg.add_scatter_series(
                    x=[], y=[], label="Temp", parent="Cp_axis", tag="results_plot"
                )
        with dpg.window(
            label="Temperature Log",
            no_collapse=True,
            no_close=True,
            no_resize=True
        ) as self.temperature_log_graph:
            with dpg.plot(
                anti_aliased=True,
            ) as self.temperature_log_plot_window:
                self.temperature_log_time_axis = dpg.add_plot_axis(
                    dpg.mvXAxis, label="time (s)", tag="time_axis"
                )
                self.temperature_log_T_axis = dpg.add_plot_axis(
                    dpg.mvYAxis, label="T (°C)", tag="T_axis"
                )
                # series belong to a y axis. Note the tag name is used in the update
                # function update_data
                self.temperature_log = dpg.add_line_series(
                    x=[], y=[], label="Temp", parent="T_axis", tag="temperature_log"
                )

    def _make_control_window(self):
        with dpg.window(
            label="Status", no_collapse=True, no_close=True, no_title_bar=True, no_resize=True
        ) as self.control_window:

            with dpg.group(tag="status_window"):
                with dpg.group(horizontal=True):
                    self.status_label = dpg.add_text("Status: ")
                    self.measurement_status = dpg.add_text(
                        f"{self.status}", tag="status_display"
                    )
            with dpg.table(header_row=False):
                dpg.add_table_column()
                dpg.add_table_column()
                dpg.add_table_column()
                dpg.add_table_column()

                with dpg.table_row():
                    dpg.add_text("Linkam: ")
                    self.linkam_status = dpg.add_text(
                        f"{self.linkam_status}", tag="linkam_status_display"
                    )

                    self.linkam_com_selector = dpg.add_combo(width=-1)
                    self.linkam_initialise = dpg.add_button(
                        label="Initialise", width=-1
                    )

                with dpg.table_row():
                    dpg.add_text("Agilent: ")
                    self.agilent_status = dpg.add_text(
                        f"{self.agilent_status}", tag="agilent_status_display"
                    )

                    self.agilent_com_selector = dpg.add_combo(width=-1)
                    self.agilent_initialise = dpg.add_button(
                        label="Initialise", width=-1
                    )
                    
                with dpg.table_row():
                    dpg.add_text("Oscilloscope: ")
                    self.oscilloscope_status = dpg.add_text(
                        f"{self.oscilloscope_status}", tag="oscilloscope_status_display"
                    )

                    self.oscilloscope_com_selector = dpg.add_combo(width=-1)
                    self.oscilloscope_initialise = dpg.add_button(
                        label="Initialise", width=-1
                    )
                    
                with dpg.table_row():
                    self.num_averages_text = dpg.add_text("N: ", show=False)
                    self.num_averages = dpg.add_input_int(default_value=5, width=-1, step =0, step_fast=0, show=False)

               
            with dpg.window(
                label="Measurement Settings",
                no_collapse=True,
                no_close=True,
                no_resize=True
            ) as self.measurement_settings_window:
                with dpg.table(header_row=False):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    dpg.add_table_column()
                    dpg.add_table_column()

                    with dpg.table_row():
                        dpg.add_text("Delay time (s): ")
                        self.delay_time = dpg.add_input_double(
                            default_value=0.5, width=-1, step=0, step_fast=0, tag="delay_time"
                        )
                        dpg.add_text("Meas. Time Mode: ")
                        self.meas_time_mode_selector = dpg.add_combo(
                            ["SHOR", "MED", "LONG"], width=-1, default_value="SHOR", tag = "meas_time_mode"
                        )

                    with dpg.table_row():
                        dpg.add_text("Averaging Factor: ")
                        self.averaging_factor = dpg.add_input_int(
                            default_value=1, width=-1, step=0, step_fast=0, tag = "averaging_factor"
                        )
                        dpg.add_text("Bias Level (V)")
                        self.bias_level = dpg.add_combo(
                            [0, 1.5, 2], width=-1, default_value=0, tag = "bias_level"
                        )

                with dpg.group(horizontal=True):
                    dpg.add_text("Output file path: ")
                    with dpg.table(header_row=False):
                        dpg.add_table_column()
                        dpg.add_table_column()
                        with dpg.table_row():

                            self.output_file_path = dpg.add_input_text(
                                default_value="results.json", width = -1, tag = "output_file_path"
                            )
                            self.browse_button = dpg.add_button(
                                label="Browse",
                                callback=lambda: self.open_tkinter_saveas_file_picker("output"),
                                width=-1
                            )

                with dpg.table(header_row=False):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    with dpg.table_row():
                        self.save_setup_button = dpg.add_button(
                            label="Save Measurement Setup",
                            width=-1,
                            callback=self.save_measurement_settings,
                        )
                        self.load_setup_button = dpg.add_button(
                            label="Load Measurement Setup",
                            width=-1,
                            callback=self.load_measurement_settings,
                        )

            with dpg.window(
                label="Frequency List",
                no_collapse=True,
                no_close=True,
                no_resize=True
            ) as self.frequency_list_window:
                self.freq_list = variable_list(
                    *make_variable_list_frame(20.0, 20.0, 2e5)
                )

            with dpg.window(
                label="Voltage List",
                no_collapse=True,
                no_close=True,
                no_resize=True
            ) as self.voltage_list_window:
                self.volt_list = variable_list(*make_variable_list_frame(1.0, 0.01, 20))

            with dpg.window(
                label="Temperature List",
                no_collapse=True,
                no_close=True,
                no_resize=True
            ) as self.temperature_list_window:
                with dpg.group(horizontal=True):
                    self.temperature_list = variable_list(
                        *make_variable_list_frame(25.0, -40, 250)
                    )
                    with dpg.group():
                        with dpg.table(header_row=False):
                            dpg.add_table_column()
                            dpg.add_table_column()
                            with dpg.table_row():
                                self.go_to_temp_button = dpg.add_button(
                                    label="Go to (°C):"
                                )
                                self.go_to_temp_input = dpg.add_input_float(
                                    default_value=25, width=100, step=0, step_fast=0
                                )
                            with dpg.table_row():
                                dpg.add_text("Rate (°C/min): ")
                                self.T_rate = dpg.add_input_double(
                                    default_value=10, width=100, step=0, step_fast=0
                                )
                            with dpg.table_row():
                                dpg.add_text("Stab. Time (s)")
                                self.stab_time = dpg.add_input_double(
                                    default_value=1, width=100, step=0, step_fast=0
                                )

            with dpg.window(
                no_title_bar=True,
                no_resize=True
            ) as self.start_stop_button_window:
                with dpg.group(horizontal=True):
                    self.start_button = dpg.add_button(
                        label="Start",
                    )
                    self.stop_button = dpg.add_button(
                        label="Stop",
                    )

    def open_tkinter_saveas_file_picker(self, type, object_to_serialise=None):
        root = tk.Tk()
        root.withdraw()
        if type == "output":
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=(("JSON Files", "*.json"), ("All files", "*.*")),
            )
            dpg.set_value(self.output_file_path, filename)

        elif type == "settings":
            filename = filedialog.asksaveasfilename(
                defaultextension=".meas",
                filetypes=(("Measurement Setup Files", "*.meas"), ("All files", "*.*")),
            )
            with open(filename, "w") as f:
                json.dump(object_to_serialise, f)

        root.destroy()

    def save_measurement_settings(self):
        measurement_settings = {
            self.delay_time: dpg.get_value(self.delay_time),
            self.meas_time_mode_selector: dpg.get_value(self.meas_time_mode_selector),
            self.averaging_factor: dpg.get_value(self.averaging_factor),
            self.bias_level: dpg.get_value(self.bias_level),
            self.output_file_path: dpg.get_value(self.output_file_path),
            "freq_list": dpg.get_item_configuration(
                self.freq_list.list_handle
            )["items"],
            "volt_list": dpg.get_item_configuration(
                self.volt_list.list_handle
            )["items"],
            "temperature_list": dpg.get_item_configuration(
                self.temperature_list.list_handle
            )["items"],
        }

        # print(measurement_settings)
        self.open_tkinter_saveas_file_picker("settings", measurement_settings)

    def load_measurement_settings(self):
        root = tk.Tk()
        root.withdraw()
        filename = filedialog.askopenfilename(
            defaultextension=".meas",
            filetypes=(("Measurement Setup Files", "*.meas"), ("All files", "*.*")),
        )
        root.destroy()

        with open(filename, "r") as f:
            tmp = json.load(f)

        for key in tmp.keys():
            if key == "freq_list":
                dpg.configure_item(self.freq_list.list_handle, items=tmp[key])
            elif key == "volt_list": 
                dpg.configure_item(self.volt_list.list_handle, items=tmp[key])
            elif key == "temperature_list":
                dpg.configure_item(self.temperature_list.list_handle, items=tmp[key])
            else:
                dpg.set_value(key, tmp[key])


def add_value_to_list_callback(sender, app_data, user_data):
    current_list = dpg.get_item_configuration(user_data["listbox_handle"])["items"]
    if len(current_list) == 0:
        new_item_number = 1
    else:
        new_item_number = int(current_list[-1].split(":")[0]) + 1
    current_list.append(
        f"{new_item_number}:\t" + str(dpg.get_value(user_data["add_text"]))
    )
    dpg.configure_item(user_data["listbox_handle"], items=current_list)


def del_value_from_list_callback(sender, app_data, user_data):
    current_list = dpg.get_item_configuration(user_data["listbox_handle"])["items"]
    if len(current_list) == 0:
        return
    selected_item = dpg.get_value(user_data["listbox_handle"])
    current_list.remove(selected_item)
    new_list = [f"{i+1}:{x.split(':')[1]}" for i, x in enumerate(current_list)]
    dpg.configure_item(user_data["listbox_handle"], items=new_list)


def append_range_to_list_callback(sender, app_data, user_data):
    current_list = dpg.get_item_configuration(user_data["listbox_handle"])["items"]

    if (
        dpg.get_value(user_data["range_selector"].spacing_combo)
        == "Number of Points (Linear)"
    ):
        values_to_add = list(
            np.linspace(
                dpg.get_value(user_data["range_selector"].min_value_input),
                dpg.get_value(user_data["range_selector"].max_value_input),
                dpg.get_value(user_data["range_selector"].number_of_points_input),
            )
        )

    elif (
        dpg.get_value(user_data["range_selector"].spacing_combo)
        == "Number of Points (Log)"
    ):
        values_to_add = list(
            np.logspace(
                np.log10(dpg.get_value(user_data["range_selector"].min_value_input)),
                np.log10(dpg.get_value(user_data["range_selector"].max_value_input)),
                dpg.get_value(user_data["range_selector"].number_of_points_input),
            )
        )

    else:
        values_to_add = list(
            np.arange(
                dpg.get_value(user_data["range_selector"].min_value_input),
                dpg.get_value(user_data["range_selector"].max_value_input)
                + dpg.get_value(user_data["range_selector"].spacing_input),
                dpg.get_value(user_data["range_selector"].spacing_input),
            )
        )

    new_list = current_list + [
        f"{i+1+len(current_list)}:\t{x}" for i, x in enumerate(values_to_add)
    ]

    dpg.configure_item(user_data["listbox_handle"], items=new_list)


def replace_list_callback(sender, app_data, user_data):
    if (
        dpg.get_value(user_data["range_selector"].spacing_combo)
        == "Number of Points (Linear)"
    ):
        values_to_add = list(
            np.linspace(
                dpg.get_value(user_data["range_selector"].min_value_input),
                dpg.get_value(user_data["range_selector"].max_value_input),
                dpg.get_value(user_data["range_selector"].number_of_points_input),
            )
        )

    elif (
        dpg.get_value(user_data["range_selector"].spacing_combo)
        == "Number of Points (Log)"
    ):
        values_to_add = list(
            np.logspace(
                np.log10(dpg.get_value(user_data["range_selector"].min_value_input)),
                np.log10(dpg.get_value(user_data["range_selector"].max_value_input)),
                dpg.get_value(user_data["range_selector"].number_of_points_input),
            )
        )
    else:
        values_to_add = list(
            np.arange(
                dpg.get_value(user_data["range_selector"].min_value_input),
                dpg.get_value(user_data["range_selector"].max_value_input)
                + dpg.get_value(user_data["range_selector"].spacing_input),
                dpg.get_value(user_data["range_selector"].spacing_input),
            )
        )

    new_list_numbered = [f"{i+1}:\t{x}" for i, x in enumerate(values_to_add)]

    dpg.configure_item(user_data["listbox_handle"], items=new_list_numbered)


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
                ["Step Size", "Number of Points (Linear)", "Number of Points (Log)"],
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
            ["1:\t" + str(default_val)],
            width=150,
            num_items=6,
        )
        with dpg.group():
            add_text = dpg.add_input_float(
                default_value=default_val, width=100, step=0, step_fast=0
            )
            add_button = dpg.add_button(
                label="Add",
                width=100,
                callback=add_value_to_list_callback,
                user_data={"listbox_handle": listbox_handle, "add_text": add_text},
            )
            add_range_button = dpg.add_button(
                label="Add Range", width=100, callback=lambda: dpg.show_item(window_tag)
            )
            delete_button = dpg.add_button(
                label="Delete",
                width=100,
                callback=del_value_from_list_callback,
                user_data={"listbox_handle": listbox_handle, "add_text": add_text},
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
