from dataclasses import dataclass
from smponpol.instruments import LinkamHotstage


@dataclass
class SponState:
    linkam_connection_status: str = "Disconnected"
    linkam_action: str = "Idle"
    agilent_connection_status: str = "Disconnected"


@dataclass
class range_selector_window:
    window_tag: str | int
    spacing_combo: str | int
    number_of_points_input: str | int
    # number of points or spacing depending on the spacing combo value
    spacing_input: str | int
    spacing_label: str | int
    min_value_input: str | int
    max_value_input: str | int


@dataclass
class variable_list:
    list_handle: str | int
    add_text_handle: str | int
    add_button_handle: str | int
    add_range_handle: str | int
    del_button_handle: str | int
    range_selector: range_selector_window


@dataclass
class SponInstruments:
    linkam: LinkamHotstage | None = None
