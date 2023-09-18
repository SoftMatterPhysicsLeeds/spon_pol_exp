import dearpygui.dearpygui as dpg
from smponpol.ui import VIEWPORT_WIDTH, DRAW_HEIGHT, SMPonpolUI
from smponpol.dataclasses import SponState, SponInstruments
from smponpol.utils import find_instruments
from pathlib import Path
import threading


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
        decorated=False
    )

    dpg.setup_dearpygui()
    dpg.show_viewport()

    ui = SMPonpolUI()
    instruments = SponInstruments()
    state = SponState()
    ui.extra_config(state, instruments)

    thread = threading.Thread(target=find_instruments, args=(ui,))
    thread.daemon = True
    thread.start()

    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


if __name__ == "__main__":
    main()
