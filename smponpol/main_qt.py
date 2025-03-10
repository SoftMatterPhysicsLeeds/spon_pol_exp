from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from importlib.resources import files
from pathlib import Path
from smponpol.experiment import Instruments
from smponpol.instruments import Agilent33220A, Rigol4204, Instec
import sys
import threading

from smponpol.ui_qt import MainWindow
from smponpol.experiment import ExperimentController


def init_agilent(frontend: MainWindow, instruments: Instruments) -> None:
    if instruments.agilent:
        instruments.agilent.close()

    agilent = Agilent33220A(frontend.equipment_init.agilent_combo.currentText())
    agilent.set_output("OFF")
    instruments.agilent = agilent


def init_oscilloscope(frontend: MainWindow, instruments: Instruments) -> None:
    if instruments.oscilloscope:
        instruments.oscilloscope.close()

    instruments.oscilloscope = Rigol4204(
        frontend.equipment_init.oscilloscope_combo.currentText()
    )


def init_hotstage(
    frontend: MainWindow,
    instruments: Instruments,
    experiment: ExperimentController,
) -> None:
    hotstage = Instec(frontend.equipment_init.hotstage_combo.currentText())
    try:
        hotstage.get_temperature()
        instruments.hotstage = hotstage
        with open("address.dat", "w") as f:
            f.write(frontend.equipment_init.hotstage_combo.currentText())
        experiment.start_reading_temperature.emit()

    except pyvisa.errors.VisaIOError:
        print("Couldn't connect to hotstage")


def connect_to_instruments_callback(
    main_window: MainWindow,
    instruments: Instruments,
    experiment: ExperimentController,
):
    hotstage_thread = threading.Thread(
        target=init_hotstage,
        args=(main_window, instruments, experiment),
    )

    hotstage_thread.daemon = True
    hotstage_thread.start()

    agilent_thread = threading.Thread(
        target=init_agilent,
        args=(
            main_window,
            instruments,
        ),
    )

    agilent_thread.daemon = True
    agilent_thread.start()

    oscilloscope_thread = threading.Thread(
        target=init_oscilloscope,
        args=(main_window, instruments),
    )

    oscilloscope_thread.daemon = True
    oscilloscope_thread.start()

    main_window.equipment_init.setVisible(False)
    main_window.control_box.setVisible(True)


def main():
    app = QApplication()
    main_window = MainWindow()
    instruments = Instruments()
    experiment = ExperimentController(instruments)

    main_window.equipment_init.initialise_button.clicked.connect(
        lambda: connect_to_instruments_callback(main_window, instruments, experiment)
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
            [instruments.hotstage_temperature],
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

    experiment.instrument_worker.current_temperature.connect(
        main_window.status_widget.change_temperature
    )
    experiment.instrument_worker.current_temperature.connect(
        instruments.set_hotstage_temperature
    )

    MODULE_PATH = files(__package__)

    icon = QIcon(str(Path(MODULE_PATH / "assets/LCD_icon.ico")))
    main_window.setWindowIcon(icon)
    main_window.showMaximized()

    experiment.instrument_worker.find_instruments()

    app.aboutToQuit.connect(experiment.stop_and_cleanup)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
