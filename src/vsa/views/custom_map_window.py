"""Window hosting the customizable defect map."""

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMainWindow, QMessageBox, QVBoxLayout, QWidget

from vsa.models import InspectionSelection
from vsa.paths import csv_path
from vsa.views.custom_map_plot import CustomMapWidget


class CustomizeMapWindow(QMainWindow):
    def __init__(self, selection: InspectionSelection, map_size=(1000, 1000)):
        super().__init__()
        self.setWindowTitle("Custom defect map")

        self.selection = selection
        self.file_path = csv_path(
            selection.product,
            selection.lot_id,
            selection.stage,
            selection.component_id,
        )

        self.plot_widget = CustomMapWidget(map_size=map_size)

        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)

        self.plot_data()

    @Slot()
    def plot_data(self):
        if not self.file_path.is_file():
            QMessageBox.warning(self, "Custom map error", f"CSV file not found: {self.file_path}")
            return

        output_path = self.plot_widget.plot_scatter(self.file_path)
        if output_path:
            self.plot_widget.load_html(output_path)
