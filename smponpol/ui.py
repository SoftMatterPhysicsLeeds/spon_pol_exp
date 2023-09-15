import dearpygui.dearpygui as dpg
VIEWPORT_WIDTH = 1280
DRAW_HEIGHT = 850
VIEWPORT_HEIGHT = DRAW_HEIGHT - 40


class SMPonpolUI:
    def __init__(self):
        self.output_file_window = OutputFileWindow()


class OutputFileWindow:
    def __init__(self):
        with dpg.window(label="Output File Settings",
                        pos=[0, 0],
                        width=VIEWPORT_WIDTH/2,
                        height=VIEWPORT_HEIGHT/4):
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


def saveas_folder_callback(sender, app_data, output_file_path):
    dpg.set_value(output_file_path, app_data["file_path_name"])
