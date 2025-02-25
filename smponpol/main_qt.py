from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from importlib.resources import files
from pathlib import Path
import sys

from smponpol.ui_qt import MainWindow


def main():
    app = QApplication()
    main_window = MainWindow()

    MODULE_PATH = files(__package__)

    icon = QIcon(str(Path(MODULE_PATH / "assets/LCD_icon.ico")))
    main_window.setWindowIcon(icon)
    main_window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
