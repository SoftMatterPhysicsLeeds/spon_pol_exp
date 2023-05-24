from qtpy.QtWidgets import (
    QFrame,
    QLabel,
    QGridLayout,
    QComboBox,
    QLineEdit,
    QGroupBox,
    QListWidget,
    QPushButton,
    QListWidgetItem,
    QWidget,
    QAbstractItemView,
)

import numpy as np

class ValueSelectorWindow(QWidget):
    """
    Popout window that will allow the user to select a range of
    frequencies/voltages /temperatures to add to the relevant list.
    """

    def __init__(
        self,
        value_list: QListWidget,
        start_val: float,
        end_val: float,
        logspace: bool = True,
    ):
        super().__init__()
        self.value_list = value_list
        self.logspace = logspace
        self.setWindowTitle("Add values")

        layout = QGridLayout()

        if logspace:
            layout.addWidget(QLabel("Number of Points"), 0, 0, 1, 2)
            self.points = QLineEdit("10")
        else:
            self.combo = QComboBox()
            self.points = QLineEdit("0.1")
            self.combo.currentIndexChanged.connect(self.comboChanged)
            layout.addWidget(self.combo, 0, 0, 1, 2)
            self.combo.addItem("Step Size")
            self.combo.addItem("Number of Points")

        layout.addWidget(self.points, 1, 0, 1, 2)
        self.points.editingFinished.connect(lambda: limits(self.points, 201, 10))

        layout.addWidget(QLabel("Start"), 2, 0, 1, 2)
        self.start = QLineEdit(f"{start_val}")
        layout.addWidget(self.start, 3, 0, 1, 2)
        self.start.editingFinished.connect(
            lambda: limits(self.start, start_val, start_val, False)
        )
        self.start.editingFinished.connect(
            lambda: limits(self.start, end_val, start_val)
        )

        layout.addWidget(QLabel("End"), 4, 0, 1, 2)
        self.end = QLineEdit(f"{end_val}")
        layout.addWidget(self.end, 5, 0, 1, 2)
        self.end.editingFinished.connect(
            lambda: limits(self.end, start_val, start_val, False)
        )
        self.end.editingFinished.connect(lambda: limits(self.end, end_val, start_val))

        self.add_button = QPushButton("Append")
        layout.addWidget(self.add_button, 6, 0)
        self.add_button.clicked.connect(self.append)

        self.add_button = QPushButton("Replace")
        layout.addWidget(self.add_button, 6, 1)
        self.add_button.clicked.connect(self.replace)

        self.setLayout(layout)

    def comboChanged(self):
        if self.combo.currentText() == "Number of Points":
            self.points.setText("10")
        else:
            self.points.setText("0.1")

    def replace(self):
        self.value_list.clear()
        self.append()

    def append(self):
        start_val = float(self.start.text())
        end_val = float(self.end.text())
        points = float(self.points.text())

        if self.logspace:
            val_list = [
                f"{x:.2f}"
                for x in list(
                    np.logspace(np.log10(start_val), np.log10(end_val), int(points))
                )
            ]
        else:
            if self.combo.currentText() == "Number of Points":
                val_list = [
                    f"{x:.2f}"
                    for x in list(np.linspace(start_val, end_val, int(points)))
                ]
            else:
                if start_val <= end_val:
                    val_list = [
                        f"{x:.2f}"
                        for x in list(np.arange(start_val, end_val + points, points))
                    ]
                else:
                    val_list = [
                        f"{x:.2f}"
                        for x in list(np.arange(start_val, end_val - points, -points))
                    ]

        for val in val_list:
            addValuesToList(self.value_list, val)

        self.close()


def addValuesToList(list_widget: QListWidget, value: str) -> None:
    item = QListWidgetItem(value, list_widget)
    list_widget.setCurrentItem(item)

def removeValuesFromList(list_widget: QListWidget) -> None:
    items = list_widget.selectedItems()
    for item in items:
        list_widget.takeItem(list_widget.row(item))

        
def createMultiValueWindow(
    list_widget: QListWidget,
    min_val: float,
    max_val: float,
    logspace: bool = True,
) -> None:
    sw = ValueSelectorWindow(list_widget, min_val, max_val, logspace)
    sw.show()


def init_ui():
    layout = QGridLayout()

    wfg_frame = init_wfg_layout()
    temp_frame=  init_temperature_settings()
    layout.addWidget(wfg_frame, 0, 0)
    layout.addWidget(temp_frame, 1, 0)

    return layout


def init_wfg_layout():
    frame = QGroupBox()
    frame.setTitle("Waveform Generator")
    layout = QGridLayout(frame)

    wfg_label = QLabel("Agilent 33220A")
    layout.addWidget(wfg_label, 0, 0)

    layout.addWidget(QLabel("Waveform:"), 0, 1)
    waveform_selector = QComboBox()
    waveform_selector.addItem("SIN")
    waveform_selector.addItem("SQUARE")
    waveform_selector.addItem("RAMP")
    layout.addWidget(waveform_selector, 0, 2)

    layout.addWidget(QLabel("Frequency: "), 0, 3)
    frequency_edit = QLineEdit("1000.0")
    layout.addWidget(frequency_edit, 0, 4)

    layout.addWidget(QLabel("Voltage: "), 0, 5)
    frequency_edit = QLineEdit("1.0")
    layout.addWidget(frequency_edit, 0, 6)

    layout.addWidget(QLabel("Voltage Offset: "), 0, 7)
    frequency_edit = QLineEdit("0")
    layout.addWidget(frequency_edit, 0, 8)

    return frame


def populateVariableFrame(
    frame: QGroupBox,
    list_box: QListWidget,
    default_val: float,
    min_val: float,
    max_val: float,
    logspace: bool = True,
) -> QGridLayout:
    layout = QGridLayout(frame)

    frame.setFrame = True  # type: ignore

    list_box.setFixedWidth(150)
    layout.addWidget(list_box, 0, 0, 4, 1)
    list_box.setSelectionMode(QAbstractItemView.ExtendedSelection)
    QListWidgetItem(f"{default_val}", list_box)

    add_edit = QLineEdit(f"{default_val}")
    add_edit.setFixedWidth(100)
    layout.addWidget(add_edit, 0, 1)
    add_edit.editingFinished.connect(lambda: limits(add_edit, min_val, min_val, False))
    add_edit.editingFinished.connect(lambda: limits(add_edit, max_val, min_val))

    add_button = QPushButton("Add")
    add_button.setFixedWidth(100)
    layout.addWidget(add_button, 1, 1)
    add_button.clicked.connect(lambda: addValuesToList(list_box, add_edit.text()))

    multi_button = QPushButton("Add range")
    multi_button.setFixedWidth(100)
    layout.addWidget(multi_button, 2, 1)
    multi_button.clicked.connect(
        lambda: createMultiValueWindow(list_box, min_val, max_val, logspace)
    )

    delete_button = QPushButton("Delete")
    delete_button.setFixedWidth(100)
    layout.addWidget(delete_button, 3, 1)
    delete_button.clicked.connect(lambda: removeValuesFromList(list_box))

    return layout

def init_temperature_settings() -> (
    tuple[QGroupBox, QPushButton, QLineEdit, QLineEdit, QLineEdit, QListWidget]
):
    temperature_settings_frame = QGroupBox()
    temperature_settings_frame.setTitle("Temperature List (°C)")
    temp_list_widget = QListWidget()

    layout = populateVariableFrame(
        temperature_settings_frame,
        temp_list_widget,
        25,
        -40,
        350,
        False,
    )

    go_to_temp_button = QPushButton("Go to:")
    layout.addWidget(go_to_temp_button, 0, 2)

    go_to_temp = QLineEdit("25")
    layout.addWidget(go_to_temp, 0, 3)
    layout.addWidget(QLabel("°C"), 0, 4)

    layout.addWidget(QLabel("Rate (°C/min)"), 1, 2)
    temp_rate = QLineEdit("10")
    layout.addWidget(temp_rate, 1, 3)

    layout.addWidget(QLabel("Stab. Time (s)"), 2, 2)
    stab_time = QLineEdit("1")
    layout.addWidget(stab_time, 2, 3)

    return temperature_settings_frame

def limits(thing, limit: float, default: float, max_val=True) -> None:
    try:
        if thing.text() == "":
            pass
        elif (
            max_val is True
            and float(thing.text()) > limit
            or max_val is False
            and float(thing.text()) < limit
        ):
            thing.setText(f"{limit}")
    except ValueError:
        thing.setText(f"{default}")
