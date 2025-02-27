from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from importlib.resources import files
from pathlib import Path
from smponpol.dataclasses import State, Instruments
import sys

from smponpol.ui_qt import MainWindow
from smponpol.utils import connect_to_instruments_callback
from smponpol.experiment import ExperimentController


def main():
    app = QApplication()
    main_window = MainWindow()
    state = State()
    instruments = Instruments()
    experiment = ExperimentController(instruments, state)

    main_window.equipment_init.initialise_button.clicked.connect(
        lambda: connect_to_instruments_callback(
            main_window, instruments, state, experiment
        )
    )

    main_window.control_buttons.start_button.clicked.connect(
        lambda: experiment.start_experiment.emit(
            main_window.temperature_selector.get_values(),
            main_window.voltage_selector.get_values(),
            main_window.control_box.frequency_selector.value(),
            main_window.control_box.file_path.text(),
            main_window.control_box.selected_waveform.currentText(),
        )
    )

    main_window.control_buttons.stop_button.clicked.connect(experiment.stop_experiment)

    main_window.control_buttons.single_shot_measurement.clicked.connect(
        lambda: experiment.start_experiment.emit(
            [state.hotstage_temperature],
            [main_window.voltage_selector.get_values()[0]],
            main_window.control_box.frequency_selector.value(),
            main_window.control_box.file_path.text(),
        )
    )

    experiment.update_graph.connect(main_window.results_window.update)

    experiment.worker.status_changed.connect(main_window.status_widget.change_status)
    experiment.instrument_worker.instruments_found.connect(
        main_window.equipment_init.add_instrument_addresses
    )

    experiment.instrument_worker.current_temperature.connect(main_window.status_widget.change_temperature)
    experiment.instrument_worker.current_temperature.connect(state.set_hotstage_temperature)

    MODULE_PATH = files(__package__)

    icon = QIcon(str(Path(MODULE_PATH / "assets/LCD_icon.ico")))
    main_window.setWindowIcon(icon)
    main_window.showMaximized()

    experiment.instrument_worker.find_instruments()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
