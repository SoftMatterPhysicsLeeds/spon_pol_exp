from dataclasses import dataclass, field
from smponpol.instruments import LinkamHotstage, Agilent33220A, Rigol4204


@dataclass
class SponState:
    linkam_connection_status: str = "Disconnected"
    linkam_action: str = "Idle"
    agilent_connection_status: str = "Disconnected"
    rigol_connection_status: str = "Disconnected"
    measurement_status: str = "Idle"
    temperature_list: list = field(default_factory=list)
    freq_list: list = field(default_factory=list)
    voltage_list: list = field(default_factory=list)
    temperature_step: int = 0
    frequency_step: int = 0
    voltage_step: int = 0
    temperature_log_time: list = field(default_factory=list)
    temperature_log_temperature: list = field(default_factory=list)
    temperature_stable_timer: float = 0.0
    output_filename: str = ""


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
    agilent: Agilent33220A | None = None
    rigol: Rigol4204 | None = None
