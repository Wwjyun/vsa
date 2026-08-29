from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget

from vsa.views.loss_map_plot import LossMapPlotController


class LossMapWindow(QWidget):
    def __init__(self, main_ui):
        super().__init__()
        self.main_ui = main_ui
        self.setWindowTitle("Loss map")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Preview window
        self.web_view = QWebEngineView(self)
        layout.addWidget(self.web_view)

        self.setLayout(layout)
        self.plot_data()

    def plot_data(self):
        self.plot_window = LossMapPlotController(
            self.main_ui, self.web_view, **self.main_ui.plot_options()
        )

    def get_current_button_name(self):
        return self.main_ui.current_button_name

    def closeEvent(self, event):
        if hasattr(self, "plot_window"):
            self.plot_window.close()
        super().closeEvent(event)
