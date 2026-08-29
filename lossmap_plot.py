"""Interactive loss-map visualization backed by Qt WebChannel."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from data_processing import classify_defects, merge_loss_frames, validate_columns
from vsa_paths import LOSS_STAGE_PAIRS, csv_path


def select_defects(defect_types, title):
    dialog = QDialog()
    dialog.setWindowTitle(title)
    layout = QVBoxLayout(dialog)
    checkboxes = {str(defect): QCheckBox(str(defect)) for defect in defect_types}

    for checkbox in checkboxes.values():
        layout.addWidget(checkbox)

    button = QPushButton("Confirm")
    layout.addWidget(button)
    selected_defects = []

    def on_confirm():
        nonlocal selected_defects
        selected_defects = [
            defect for defect, checkbox in checkboxes.items() if checkbox.isChecked()
        ]
        dialog.accept()

    button.clicked.connect(on_confirm)
    dialog.exec()
    return selected_defects


def preprocess_csv(file_path, selection_type="good", flip=False, selector=select_defects):
    defect_data = pd.read_csv(file_path)
    validate_columns(defect_data)
    title = "Select Good Defects" if selection_type == "good" else "Select Bad Defects"
    selected_defects = selector(defect_data["DefectType"].unique(), title)
    return classify_defects(
        defect_data,
        selected_defects,
        selection_type,
        flip=flip,
    )


def build_loss_figure(merged, stage, point_size=2, width=1000, height=800):
    figure = go.Figure(
        go.Scattergl(
            x=merged["Col"],
            y=merged["Row"],
            mode="markers",
            customdata=merged["SelectedNo"].astype(str),
            text=merged["SelectedNo"].astype(str),
            hovertemplate="Col: %{x}<br>Row: %{y}<br>No: %{text}<extra></extra>",
            marker={"color": merged["Color"], "size": point_size, "opacity": 0.6},
        )
    )
    figure.update_layout(
        title=f"Map of Defects - {stage}",
        title_font={"size": 20},
        xaxis_title="Col Coordinate",
        yaxis_title="Row Coordinate",
        yaxis={"autorange": "reversed"},
        margin={"l": 70, "r": 30, "t": 70, "b": 30},
        plot_bgcolor="black",
        paper_bgcolor="black",
        font={"color": "white"},
        width=width,
        height=height,
    )
    figure.update_xaxes(showgrid=True, gridcolor="gray")
    figure.update_yaxes(showgrid=True, gridcolor="gray")
    return figure


def build_loss_html(figure):
    post_script = r"""
    (function () {
        const plot = document.getElementById('{plot_id}');
        let handler = null;
        let lastNumber = null;
        let lastClickAt = 0;

        new QWebChannel(qt.webChannelTransport, function (channel) {
            handler = channel.objects.handler;
        });

        plot.on('plotly_click', function (eventData) {
            if (!eventData.points || eventData.points.length === 0) return;
            const number = String(eventData.points[0].customdata);
            const now = Date.now();
            if (handler && number === lastNumber && now - lastClickAt <= 500) {
                handler.receivePoint(number);
                lastNumber = null;
                lastClickAt = 0;
                return;
            }
            lastNumber = number;
            lastClickAt = now;
        });
    }());
    """
    page_html = figure.to_html(
        full_html=True,
        include_plotlyjs=True,
        post_script=post_script,
    )
    return page_html.replace(
        "<head>",
        '<head><script src="qrc:///qtwebchannel/qwebchannel.js"></script>',
        1,
    )


class PlotWindow(QMainWindow):
    point_selected = Signal(str)

    def __init__(
        self,
        main_ui,
        web_view,
        custom_color_map=None,
        plot_width=1000,
        plot_height=800,
        point_size=2,
    ):
        super().__init__()
        self.main_ui = main_ui
        self.web_view = web_view
        self.custom_color_map = custom_color_map
        self.plot_width = plot_width
        self.plot_height = plot_height
        self.point_size = point_size
        self.temp_dir = tempfile.TemporaryDirectory(prefix="vsa-loss-")
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        QVBoxLayout(self.central_widget)

        self.channel = QWebChannel()
        self.handler = WebEnginePageHandler(self)
        self.channel.registerObject("handler", self.handler)
        self.web_view.page().setWebChannel(self.channel)
        self.plot()

    def get_csv_paths(self):
        number = self.main_ui.input_number.text().strip()
        code = self.main_ui.input_code1.text().strip()
        current_stage = self.main_ui.current_button_name
        option = self.main_ui.combo.currentText()
        stage_pair = LOSS_STAGE_PAIRS.get(current_stage)
        if stage_pair is None:
            raise ValueError("Select a LOSS stage first.")
        return tuple(csv_path(option, number, stage, code) for stage in stage_pair)

    def plot(self):
        try:
            first_csv, second_csv = self.get_csv_paths()
            for file_path in (first_csv, second_csv):
                if not file_path.is_file():
                    raise FileNotFoundError(f"CSV file not found: {file_path}")

            flip_first_csv = self.main_ui.current_button_name == "LOSS1"
            good_frame = preprocess_csv(first_csv, selection_type="good", flip=flip_first_csv)
            bad_frame = preprocess_csv(second_csv, selection_type="bad")
            merged = merge_loss_frames(good_frame, bad_frame)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self.main_ui, "Loss map error", str(error))
            return

        figure = build_loss_figure(
            merged,
            self.main_ui.current_button_name,
            self.point_size,
            self.plot_width,
            self.plot_height,
        )
        page_html = build_loss_html(figure)
        output_path = Path(self.temp_dir.name) / "loss-map.html"
        output_path.write_text(page_html, encoding="utf-8")
        self.web_view.setUrl(QUrl.fromLocalFile(str(output_path)))

    @Slot(str)
    def receivePoint(self, no):
        self.main_ui.update_search_field(no)
        self.point_selected.emit(no)

    def closeEvent(self, event):
        self.web_view.setUrl(QUrl("about:blank"))
        self.temp_dir.cleanup()
        super().closeEvent(event)


class WebEnginePageHandler(QObject):
    def __init__(self, plot_window):
        super().__init__()
        self.plot_window = plot_window

    @Slot(str)
    def receivePoint(self, no):
        self.plot_window.receivePoint(no)
