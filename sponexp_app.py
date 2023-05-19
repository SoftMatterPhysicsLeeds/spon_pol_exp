import sys
from qtpy.QtWidgets import (
    QApplication,
    QWidget,
)


class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("SponPol")

    


def main():
    app = QApplication()
    main_app = MainWindow()
    main_app.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()