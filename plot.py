"""Interactive ROI plot window with deterministic cleanup."""

from __future__ import annotations

import base64
import tempfile
import threading
from io import BytesIO
from pathlib import Path

import dash.exceptions
import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
from flask import Flask
from PIL import Image
from plotly.colors import qualitative
from PySide6.QtCore import QUrl, Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QVBoxLayout, QWidget
from werkzeug.serving import make_server

from data_processing import validate_columns
from vsa_paths import DYNAMIC_STAGES, roi_folder


def _image_filename(value: object) -> str:
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{value}.tiff"


class PlotWindow(QMainWindow):
    url_signal = Signal(str)

    def __init__(
        self,
        csv_path,
        image_folder_path,
        current_button_name,
        image_url,
        number,
        code,
        option,
    ):
        super().__init__()
        self.csv_path = Path(csv_path)
        self.image_folder_path = Path(image_folder_path)
        self.current_button_name = current_button_name
        self.image_url = Path(image_url)
        self.number = number
        self.code = code
        self.option = option
        self.dynamic_folders = DYNAMIC_STAGES
        self.http_server = None
        self.dash_thread = None
        self.temp_dir = tempfile.TemporaryDirectory(prefix="vsa-roi-")

        self.init_ui()
        self.prepare_data_and_plot()

    def init_ui(self):
        self.setWindowTitle(f"ROI inspection - {self.current_button_name}")
        self.setGeometry(100, 100, 1600, 1200)

        self.main_layout = QVBoxLayout()
        self.top_layout = QHBoxLayout()

        self.web_view_left = QWebEngineView()
        self.web_view_left.setFixedSize(1300, 900)
        self.web_view_right_1 = QWebEngineView()
        self.web_view_right_1.setFixedSize(330, 330)
        self.web_view_right_2 = QWebEngineView()
        self.web_view_right_2.setFixedSize(330, 330)

        if self.image_url.is_file():
            html_path = self.create_temp_html(self.image_url)
            self.web_view_right_2.setUrl(QUrl.fromLocalFile(str(html_path)))

        self.top_layout.addWidget(self.web_view_left)
        self.top_layout.addWidget(self.web_view_right_1)
        self.top_layout.addWidget(self.web_view_right_2)

        self.bottom_layout = QHBoxLayout()
        self.dynamic_views = []
        for _folder in self.dynamic_folders:
            dynamic_view = QWebEngineView()
            dynamic_view.setFixedSize(330, 330)
            self.bottom_layout.addWidget(dynamic_view)
            self.dynamic_views.append(dynamic_view)

        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.bottom_layout)

        self.container = QWidget()
        self.container.setLayout(self.main_layout)
        self.setCentralWidget(self.container)
        self.url_signal.connect(self.update_views)

    def prepare_data_and_plot(self):
        defect_data = pd.read_csv(self.csv_path)
        validate_columns(defect_data)
        defect_data = defect_data.loc[defect_data["DefectType"] != "ok"].copy()
        defect_data["Image"] = defect_data["No"].map(_image_filename)

        defect_types = sorted(defect_data["DefectType"].astype(str).unique())
        color_map = {
            defect: qualitative.Plotly[index % len(qualitative.Plotly)]
            for index, defect in enumerate(defect_types)
        }
        colors = defect_data["DefectType"].astype(str).map(color_map)
        hover_texts = (
            "<b>DefectType:</b> "
            + defect_data["DefectType"].astype(str)
            + "<br><b>Col:</b> "
            + defect_data["Col"].astype(str)
            + "<br><b>Row:</b> "
            + defect_data["Row"].astype(str)
            + "<br><b>No:</b> "
            + defect_data["No"].astype(str)
        )
        click_urls = [
            str(self.image_folder_path / image_name) for image_name in defect_data["Image"]
        ]

        figure = go.Figure(
            go.Scatter(
                x=defect_data["Col"],
                y=defect_data["Row"],
                mode="markers",
                marker={"size": 3, "color": colors},
                text=hover_texts,
                customdata=click_urls,
                hoverinfo="text",
            )
        )
        figure.update_layout(
            title=f"Scatter Plot - {self.current_button_name}",
            xaxis_title="Col",
            yaxis_title="Row",
            hovermode="closest",
            margin={"l": 0, "r": 0, "t": 40, "b": 0},
            width=1200,
            height=900,
        )
        figure.update_yaxes(autorange="reversed")

        flask_server = Flask(f"vsa_plot_{id(self)}")
        self.app = Dash(f"vsa_plot_{id(self)}", server=flask_server)
        self.app.layout = html.Div(
            [dcc.Graph(id="scatter-plot", figure=figure, config={"displayModeBar": False})]
        )

        @self.app.callback(
            Output("scatter-plot", "figure"),
            Input("scatter-plot", "clickData"),
            State("scatter-plot", "figure"),
        )
        def open_url(click_data, current_figure):
            if click_data is None:
                raise dash.exceptions.PreventUpdate
            image_path = Path(click_data["points"][0]["customdata"])
            if image_path.is_file():
                self.url_signal.emit(str(image_path))
            return current_figure

        self.run_dash_app()

    def create_temp_html(self, image_path: str | Path) -> Path:
        image_path = Path(image_path)
        if not image_path.is_file():
            raise FileNotFoundError(f"Image not found: {image_path}")

        with Image.open(image_path) as source_image:
            preview = source_image.convert("RGB").resize((300, 300))
            buffer = BytesIO()
            preview.save(buffer, format="PNG")
        image_data = base64.b64encode(buffer.getvalue()).decode("ascii")
        image_tag = (
            f'<img src="data:image/png;base64,{image_data}" '
            'style="width:300px;height:300px;object-fit:contain;">'
        )

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            suffix=".html",
            dir=self.temp_dir.name,
        ) as temp_html:
            temp_html.write(f"<html><body>{image_tag}</body></html>")
            return Path(temp_html.name)

    def run_dash_app(self):
        self.http_server = make_server("127.0.0.1", 0, self.app.server, threaded=True)
        port = self.http_server.server_port
        self.dash_thread = threading.Thread(
            target=self.http_server.serve_forever,
            name=f"vsa-dash-{port}",
            daemon=True,
        )
        self.dash_thread.start()
        self.web_view_left.setUrl(QUrl(f"http://127.0.0.1:{port}"))

    def update_views(self, url):
        image_path = Path(url)
        if not image_path.is_file():
            return

        html_path = self.create_temp_html(image_path)
        self.web_view_right_1.setUrl(QUrl.fromLocalFile(str(html_path)))

        for index, folder in enumerate(self.dynamic_folders):
            related_image = (
                roi_folder(
                    self.option,
                    self.number,
                    folder,
                    self.code,
                )
                / image_path.name
            )
            if related_image.is_file():
                related_html = self.create_temp_html(related_image)
                self.dynamic_views[index].setUrl(QUrl.fromLocalFile(str(related_html)))
            else:
                self.dynamic_views[index].setHtml(f"<p>Image not found for {folder}</p>")

    def closeEvent(self, event):
        if self.http_server is not None:
            self.http_server.shutdown()
            self.http_server.server_close()
        if self.dash_thread is not None and self.dash_thread.is_alive():
            self.dash_thread.join(timeout=3)

        for web_view in [
            self.web_view_left,
            self.web_view_right_1,
            self.web_view_right_2,
            *self.dynamic_views,
        ]:
            web_view.setUrl(QUrl("about:blank"))
        self.temp_dir.cleanup()
        super().closeEvent(event)
