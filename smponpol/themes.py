import dearpygui.dearpygui as dpg

def generate_global_theme():
    with dpg.theme() as global_theme:

        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (40,40,40), category = dpg.mvThemeCat_Core )

    return global_theme
    
