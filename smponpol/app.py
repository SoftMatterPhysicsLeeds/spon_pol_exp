import dearpygui.dearpygui as dpg
from smponpol.ui import VIEWPORT_WIDTH, DRAW_HEIGHT, SMPonpolUI
from pathlib import Path

def main():
    font_path = Path("./assets/IosevkaNerdFont-Regular.ttf")
    dpg.create_context()

    with dpg.font_registry():
        default_font = dpg.add_font(
            font_path, 18)
    dpg.bind_font(default_font)
    dpg.create_viewport(
        title="SMPontaneous Polarisation",
        width=VIEWPORT_WIDTH,
        height=DRAW_HEIGHT,
    )

    dpg.setup_dearpygui()
    dpg.show_viewport()

    ui = SMPonpolUI()

    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


if __name__ == "__main__":
    main()
