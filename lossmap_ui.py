from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from lossmap_plot import PlotWindow

class LossMapUI(QWidget):
    def __init__(self, main_ui):
        super().__init__()
        self.main_ui = main_ui
        self.setWindowTitle("CSV and Image Processor")
        self.setGeometry(100, 100, 1200, 800)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Preview window
        self.web_view = QWebEngineView(self)
        layout.addWidget(self.web_view)

        self.setLayout(layout)
        self.plot_data()

    def plot_data(self):
        self.plot_window = PlotWindow(self.main_ui, self.web_view)
        self.plot_window.show()

    def get_current_button_name(self):
        return self.main_ui.current_button_name
