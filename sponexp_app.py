import sys
from qtpy.QtWidgets import (
    QApplication,
    QWidget,
)

from sponexp_ui import init_ui


class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.layout = init_ui()
        self.setWindowTitle("SponPol")
        self.setLayout(self.layout)
    


def main():
    app = QApplication()
    main_app = MainWindow()
    main_app.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()