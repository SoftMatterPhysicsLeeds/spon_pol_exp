from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from importlib.resources import files
from pathlib import Path
from smponpol.dataclasses import State, Instruments
import sys

from smponpol.ui_qt import MainWindow
from smponpol.utils import connect_to_instruments_callback


def main():
    app = QApplication()
    main_window = MainWindow()
    state = State()
    instruments = Instruments()

    main_window.equipment_init.initialise_button.clicked.connect(
        lambda: connect_to_instruments_callback(main_window, instruments, state)
    )

    MODULE_PATH = files(__package__)

    icon = QIcon(str(Path(MODULE_PATH / "assets/LCD_icon.ico")))
    main_window.setWindowIcon(icon)
    main_window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
