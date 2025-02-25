from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QGridLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
    QListWidget,
    QDialog,
    QVBoxLayout,
    QDialogButtonBox,
    QComboBox,
)

import pyqtgraph as pg

# need:
# status window
# temperature selector
# voltage selector
# instrument initialiser
# frequency set, waveform set.
# graph.


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMPontaneous Polarisation")
        self.setGeometry(100, 100, 1280, 850)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)

        self.status_widget = StatusWidget()
        self.temperature_selector = ValueListWidget(
            "Temperature", min_value=10, max_value=300
        )
        self.voltage_selector = ValueListWidget("Voltage", min_value=0, max_value=20)
        self.control_box = ControlWidget()
        self.results_window = ResultsWidget()

        layout.addWidget(self.status_widget, 0, 0, 1, 3)
        layout.addWidget(self.control_box, 1, 0)
        layout.addWidget(self.voltage_selector, 1, 1)
        layout.addWidget(self.temperature_selector, 1, 2)
        layout.addWidget(self.results_window, 3, 0, 1, 3)


class StatusWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        group_box = QGroupBox("Status")
        group_layout = QVBoxLayout()
        group_box.setLayout(group_layout)

        self.status_label = QLabel("Idle")
        group_layout.addWidget(self.status_label)

        self.layout.addWidget(group_box)


class ControlWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.layout: QGridLayout = QGridLayout()
        self.setLayout(self.layout)

        group_box = QGroupBox("Control Parameters")
        group_layout = QGridLayout()
        group_box.setLayout(group_layout)

        group_layout.addWidget(QLabel("Frequency (Hz): "), 0, 0)
        self.frequency_selector = QDoubleSpinBox()
        self.frequency_selector.setRange(10, 20000)
        self.frequency_selector.setDecimals(2)
        self.frequency_selector.setValue(1000)
        group_layout.addWidget(self.frequency_selector, 0, 1)

        group_layout.addWidget(QLabel("Waveform"), 1, 0)
        self.selected_waveform = QComboBox()
        self.selected_waveform.addItems(["Sine", "Square", "Triangle", "User"])
        self.selected_waveform.setCurrentIndex(2)
        group_layout.addWidget(self.selected_waveform, 1, 1)

        self.layout.addWidget(group_box)


class ResultsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout: QGridLayout = QGridLayout()
        self.setLayout(self.layout)

        group_box = QGroupBox("Results")
        group_layout = QGridLayout()
        group_box.setLayout(group_layout)

        self.plot_widget = pg.PlotWidget()
        group_layout.addWidget(self.plot_widget)

        self.x = [1, 2, 3, 4, 5]
        self.y = [1, 2, 3, 4, 5]

        self.plot_widget.plot(self.x, self.y, pen="b")
        self.plot_widget.setLabel("left", "Value", units="V")
        self.plot_widget.setLabel("bottom", "Time", units="s")
        self.plot_widget.showGrid(x=True, y=True)

        self.layout.addWidget(group_box)


class ValueListWidget(QWidget):
    def __init__(self, variable_name="Frequency", min_value=20, max_value=2e6):
        super().__init__()
        self.main_layout = QGridLayout()
        self.setLayout(self.main_layout)

        self.min_value = min_value
        self.max_value = max_value

        group_box = QGroupBox(variable_name + " List")
        self.layout = QGridLayout()
        group_box.setLayout(self.layout)

        self.setup_ui()
        self.setup_connections()

        self.main_layout.addWidget(group_box)

    def setup_ui(self):
        self.value_list = QListWidget()
        self.value_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.layout.addWidget(self.value_list, 0, 0, 4, 1)

        self.value_spinner = QDoubleSpinBox()
        self.value_spinner.setRange(self.min_value, self.max_value)
        self.value_spinner.setDecimals(3)
        self.value_spinner.setValue(self.min_value)
        self.layout.addWidget(self.value_spinner, 0, 1)

        self.add_button = QPushButton("Add")
        self.layout.addWidget(self.add_button, 1, 1)

        self.delete_button = QPushButton("Delete")
        self.layout.addWidget(self.delete_button, 2, 1)

        self.range_button = QPushButton("Range...")
        self.layout.addWidget(self.range_button, 3, 1)

    def setup_connections(self):
        self.add_button.clicked.connect(self.add_value)
        self.delete_button.clicked.connect(self.delete_selected)
        self.range_button.clicked.connect(self.show_range_dialog)

    def add_value(self):
        value = self.value_spinner.value()
        next_index = self.value_list.count() + 1
        self.value_list.addItem(f"{next_index}: {value}")

    def delete_selected(self):
        # Get all selected items
        selected_items = self.value_list.selectedItems()

        # Remove the selected items
        for item in selected_items:
            self.value_list.takeItem(self.value_list.row(item))

        # Renumber remaining items
        self.renumber_items()

    def renumber_items(self):
        # Go through all items and renumber them
        for i in range(self.value_list.count()):
            item = self.value_list.item(i)
            # Get the value part after the colon
            old_text = item.text()
            value = old_text.split(": ")[1]
            # Set new numbered text
            item.setText(f"{i + 1}: {value}")

    def get_values(self):
        """Returns a list of just the values without the numbering"""
        values = []
        for i in range(self.value_list.count()):
            item = self.value_list.item(i)
            value = float(item.text().split(": ")[1])
            values.append(value)
        return values

    def show_range_dialog(self):
        dialog = RangeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            min_val, max_val, step = dialog.get_values()
            current = min_val
            while current <= max_val:
                next_index = self.value_list.count() + 1
                self.value_list.addItem(f"{next_index}: {current}")
                current += step


class RangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Range")
        self.setup_ui(parent)

    def setup_ui(self, parent):
        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Minimum:"))
        self.min_spinner = QDoubleSpinBox()
        self.min_spinner.setRange(parent.min_value, parent.max_value)
        self.min_spinner.setDecimals(3)
        self.min_spinner.setValue(parent.min_value)
        layout.addWidget(self.min_spinner)

        layout.addWidget(QLabel("Maximum:"))
        self.max_spinner = QDoubleSpinBox()
        self.max_spinner.setRange(parent.min_value, parent.max_value)
        self.max_spinner.setDecimals(3)
        self.max_spinner.setValue(parent.max_value)
        layout.addWidget(self.max_spinner)

        layout.addWidget(QLabel("Step:"))
        self.step_spinner = QDoubleSpinBox()
        self.step_spinner.setRange(parent.min_value, parent.max_value)
        self.step_spinner.setDecimals(3)
        self.step_spinner.setValue(1.0)
        layout.addWidget(self.step_spinner)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self):
        return (
            self.min_spinner.value(),
            self.max_spinner.value(),
            self.step_spinner.value(),
        )
