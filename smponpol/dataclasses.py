from dataclasses import dataclass, field
from smponpol.instruments import Instec, Agilent33220A
from enum import Enum
from pyvisa.resources import Resource
from PySide6.QtCore import Slot


class OutputType(Enum):
    SINGLE_VOLT = 1
    SINGLE_FREQ = 2
    SINGLE_VOLT_FREQ = 3
    MULTI_VOLT_FREQ = 4


class Status(Enum):
    IDLE = 1
    SET_TEMPERATURE = 2
    GOING_TO_TEMPERATURE = 3
    STABILISING_TEMPERATURE = 4
    TEMPERATURE_STABILISED = 5
    COLLECTING_DATA = 6
    FINISHED = 7


@dataclass
class range_selector_window:
    window_tag: str | int
    spacing_combo: str | int
    number_of_points_input: str | int
    spacing_input: (
        str | int
    )  # number of points or spacing depending on the spacing combo value
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
class State:
    resultsDict: dict = field(default_factory=dict)
    measurement_status: Status = Status.IDLE
    stabilisation_time: float = 30.0
    voltage_list_mode: bool = False
    spectrometer_running: bool = True
    hotstage_connection_status: str = "Disconnected"
    agilent_connection_status: str = "Disconnected"
    oscilloscope_connection_status: str = "Disconnected"
    scope_run_number: int = 1
    hotstage_action: str = "Idle"
    hotstage_temperature: float = 25.0
    T_list: list = field(default_factory=list)
    # freq_list: list = field(default_factory=list)
    voltage_list: list = field(default_factory=list)
    xdata: list = field(default_factory=list)
    ydata: list = field(default_factory=list)
    T_step: int = 0
    voltage_step: int = 0
    T_log_time: list = field(default_factory=list)
    T_log_T: list = field(default_factory=list)

    Slot(float)
    def set_hotstage_temperature(self, T: float):
        self.hotstage_temperature = T



@dataclass
class Instruments:
    hotstage: Instec | None = None
    agilent: Agilent33220A | None = None
    oscilloscope: Resource | None = None
