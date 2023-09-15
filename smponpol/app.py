import dearpygui.dearpygui as dpg
from smponpol.ui import VIEWPORT_WIDTH, DRAW_HEIGHT


def main():
    print("hello!")
    dpg.create_context()

    dpg.create_viewport(
        title="SMPontaneous Polarisation",
        width=VIEWPORT_WIDTH,
        height=DRAW_HEIGHT,
    )

    dpg.setup_dearpygui()
    dpg.show_viewport()

    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg.destroy_context()

if __name__ == "__main__":
    main()
