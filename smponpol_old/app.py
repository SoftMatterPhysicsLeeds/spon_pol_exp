import dearpygui.dearpygui as dpg
from smponpol.ui import VIEWPORT_WIDTH, DRAW_HEIGHT, SMPonpolUI
from smponpol.dataclasses import SponState, SponInstruments
from smponpol.utils import find_instruments
from pathlib import Path
import threading


def main():
    dpg.create_context()

    font_path = Path("./assets/IosevkaNerdFont-Regular.ttf")
    with dpg.font_registry():
        default_font = dpg.add_font(
            font_path, 18)
    dpg.bind_font(default_font)
    dpg.create_viewport(
        title="SMPontaneous Polarisation",
        width=VIEWPORT_WIDTH,
        height=DRAW_HEIGHT,
        x_pos=0,
        y_pos=0
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
    viewport_width = dpg.get_viewport_client_width()
    viewport_height = dpg.get_viewport_client_height()
    while dpg.is_dearpygui_running():
        # check if viewport has been resized. If it has, redraw windows
        if viewport_width != dpg.get_viewport_client_width() or viewport_height != dpg.get_viewport_client_height():
            # redraw_windows.
            viewport_width = dpg.get_viewport_client_width()
            viewport_height = dpg.get_viewport_client_height()
            ui.redraw_windows(viewport_height, viewport_width)
        dpg.render_dearpygui_frame()

    dpg.destroy_context()

    if instruments.linkam:
        instruments.linkam.close()
    if instruments.agilent:
        instruments.agilent.close()
    if instruments.rigol:
        instruments.rigol.close()


if __name__ == "__main__":
    main()
