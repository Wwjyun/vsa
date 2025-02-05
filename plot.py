import sys
import os
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
from PIL import Image
from io import BytesIO
import base64
import threading
import dash.exceptions
from flask import Flask
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Signal
import tempfile
import random


class PlotWindow(QMainWindow):
    url_signal = Signal(str)  # 信号，用于更新动态视图

    def __init__(self, csv_path, image_folder_path, current_button_name, port, image_url, number, code, option):
        super().__init__()
        self.csv_path = csv_path
        self.image_folder_path = image_folder_path
        self.current_button_name = current_button_name
        self.port = port
        self.image_url = image_url
        self.number = number
        self.code = code
        self.option = option
        self.dynamic_folders = ["MT", "DC2", "INN1", "RDL", "INN2", "EMC"]
        self.dash_thread = None

        self.initUI()
        self.prepare_data_and_plot()

    def initUI(self):
        self.setWindowTitle(f"Plotly Hover Image Example - {self.current_button_name}")
        self.setGeometry(100, 100, 1600, 1200)

        # 主布局
        self.main_layout = QVBoxLayout()

        # 第一行布局：左侧 Dash 图表和右侧两个动态视图
        self.top_layout = QHBoxLayout()

        # 左侧 Dash 图表
        self.web_view_left = QWebEngineView()
        self.web_view_left.setFixedSize(1300, 900)

        # 第一个动态视图
        self.web_view_right_1 = QWebEngineView()
        self.web_view_right_1.setFixedSize(330, 330)

        # 第二个固定动态视图
        self.web_view_right_2 = QWebEngineView()
        self.web_view_right_2.setFixedSize(330, 330)

        # 加载固定图片到第二个动态视图
        if self.image_url and os.path.exists(self.image_url):
            html_path = self.create_temp_html(self.image_url)
            self.web_view_right_2.setUrl(QUrl.fromLocalFile(html_path))
        else:
            print(f"Error: Invalid image URL or file not found: {self.image_url}")

        self.top_layout.addWidget(self.web_view_left)
        self.top_layout.addWidget(self.web_view_right_1)
        self.top_layout.addWidget(self.web_view_right_2)

        # 第二行布局：六个动态视图
        self.bottom_layout = QHBoxLayout()
        self.dynamic_views = []
        for i, folder in enumerate(self.dynamic_folders):
            dynamic_view = QWebEngineView()
            dynamic_view.setFixedSize(330, 330)
            self.bottom_layout.addWidget(dynamic_view)
            self.dynamic_views.append(dynamic_view)

        # 将布局加入到主窗口
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.bottom_layout)

        # 设置主布局
        self.container = QWidget()
        self.container.setLayout(self.main_layout)
        self.setCentralWidget(self.container)

        # 连接点击事件信号
        self.url_signal.connect(self.update_views)

    def prepare_data_and_plot(self):
        df = pd.read_csv(self.csv_path)

        # 过滤掉 DefectType 为 'ok' 的行
        df = df[df['DefectType'] != 'ok']

        # 动态添加 Image 列
        df['Image'] = df['No'].apply(lambda x: f'{x}.tiff')

        # 自动生成 DefectType 的颜色
        defect_types = df['DefectType'].unique()
        color_map = {defect: f"rgb({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)})" for defect in defect_types}

        fig = make_subplots(rows=1, cols=1)
        hover_texts = []
        click_urls = []

        for i, row in df.iterrows():
            image_path = os.path.join(self.image_folder_path, row['Image']).replace("\\", "/")
            hover_text = f"<b>DefectType:</b> {row['DefectType']}<br><b>Col:</b> {row['Col']}<br><b>Row:</b> {row['Row']}<br><b>No:</b> {row['No']}"
            hover_texts.append(hover_text)
            click_urls.append(image_path)

        scatter = go.Scatter(
            x=df['Col'],
            y=df['Row'],
            mode='markers',
            marker=dict(size=3, color=[color_map[defect_type] for defect_type in df['DefectType']]),
            text=hover_texts,
            customdata=click_urls,
            hoverinfo='text',
        )


        fig.add_trace(scatter)
        fig.update_layout(
            title=f"Scatter Plot - {self.current_button_name}",
            xaxis_title="Col",
            yaxis_title="Row",
            hovermode="closest",
            margin=dict(l=0, r=0, t=0, b=0),
            width=1200,
            height=900,
        )
        fig.update_yaxes(autorange="reversed")

        server = Flask(__name__)
        self.app = Dash(__name__, server=server)
        self.app.layout = html.Div([dcc.Graph(id="scatter-plot", figure=fig, config={"displayModeBar": False})])

        @self.app.callback(
            Output("scatter-plot", "figure"),
            Input("scatter-plot", "clickData"),
            State("scatter-plot", "figure"),
        )
        def open_url(clickData, current_fig):
            if clickData is None:
                raise dash.exceptions.PreventUpdate
            else:
                image_path = clickData["points"][0]["customdata"]
                if os.path.exists(image_path):
                    html_path = self.create_temp_html(image_path)
                    self.url_signal.emit(image_path)
                else:
                    print(f"Error: File not found: {image_path}")
            return current_fig

        self.run_dash_app()

    def create_temp_html(self, image_path):
        if not os.path.exists(image_path):
            print(f"File not found: {image_path}")
            return ""
        pil_img = Image.open(image_path).resize((300, 300))
        buff = BytesIO()
        pil_img.save(buff, format="PNG")
        img_str = base64.b64encode(buff.getvalue()).decode("utf-8")
        img_tag = f'<img src="data:image/png;base64,{img_str}" style="width:300px;height:300px;">'

        temp_html = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        with open(temp_html.name, "w") as f:
            f.write(f"<html><body>{img_tag}</body></html>")
        return temp_html.name

    def run_dash_app(self):
        def run():
            self.app.run_server(debug=False, use_reloader=False, port=self.port)

        self.dash_thread = threading.Thread(target=run)
        self.dash_thread.start()
        self.web_view_left.setUrl(QUrl(f"http://127.0.0.1:{self.port}"))

    def update_views(self, url):
        """
        更新所有动态视图
        """
        if url:
            
            url = url.replace("\\", "/")

            
            if os.path.exists(url):
                html_path = self.create_temp_html(url)  
                self.web_view_right_1.setUrl(QUrl.fromLocalFile(html_path))  
            else:
                print(f"Error: File not found for first dynamic view: {url}")

            
            base_filename = os.path.basename(url)

            
            for i, folder in enumerate(self.dynamic_folders):
                try:
                    folder_path = f"D:/Database-PC/{self.option}/roi/{self.number}/{folder}/{self.code}/{base_filename}"
                    folder_path = folder_path.replace("\\", "/")  

                    if os.path.exists(folder_path):
                        html_path = self.create_temp_html(folder_path)
                        self.dynamic_views[i].setUrl(QUrl.fromLocalFile(html_path))
                    else:
                        print(f"File not found for folder {folder}: {folder_path}")
                except Exception as e:
                    print(f"Error updating view {i}: {e}")


    def closeEvent(self, event):
        if self.dash_thread and self.dash_thread.is_alive():
            self.dash_thread.join(timeout=1)
        event.accept()
