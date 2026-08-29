# customize_map_ui.py

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMainWindow, QMessageBox, QVBoxLayout, QWidget

from customize_map_plot import PlotWidget
from vsa_paths import csv_path


class CustomizeMapUI(QMainWindow):
    def __init__(self, option, number, current_button_name, code):
        super().__init__()
        self.setWindowTitle("Scatter Plot with Plotly and PySide6")

        self.number = number
        self.current_button_name = current_button_name
        self.code = code
        self.option = option
        self.file_path = csv_path(option, number, self.current_button_name, code)

        self.plot_widget = PlotWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.setGeometry(100, 100, 1200, 800)  # Set the window size

        self.plot_data()

    @Slot()
    def plot_data(self):
        if not self.file_path.is_file():
            QMessageBox.warning(self, "錯誤", f"CSV檔案不存在：{self.file_path}")
            return

        output_path = self.plot_widget.plot_scatter(self.file_path)
        if output_path:
            self.plot_widget.load_html(output_path)
