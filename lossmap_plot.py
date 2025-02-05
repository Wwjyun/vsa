import pandas as pd
import plotly.graph_objects as go
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QDialog, QVBoxLayout, QCheckBox, QPushButton, QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QUrl, Signal, Slot, QObject
import os
import tempfile
import shutil
from flip import flip_csv_files

def select_defects(defect_types, title):
    app = QApplication.instance() or QApplication([])  # Check if there's an existing instance
    dialog = QDialog()
    dialog.setWindowTitle(title)
    layout = QVBoxLayout()

    checkboxes = {str(defect): QCheckBox(str(defect)) for defect in defect_types}

    for checkbox in checkboxes.values():
        layout.addWidget(checkbox)

    button = QPushButton("Confirm")
    layout.addWidget(button)
    dialog.setLayout(layout)

    selected_defects = []

    def on_confirm():
        nonlocal selected_defects
        selected_defects = [defect for defect, checkbox in checkboxes.items() if checkbox.isChecked()]
        dialog.accept()

    button.clicked.connect(on_confirm)
    dialog.exec()

    return selected_defects

def preprocess_csv(file_path, selection_type="good", flip=False):
    print(f"Reading CSV file: {file_path}")
    defect_data = pd.read_csv(file_path)
    defect_types = defect_data['DefectType'].unique()
    title = "Select Good Defects" if selection_type == "good" else "Select Bad Defects"
    selected_defects = select_defects(defect_types, title)
    print(f"Selected {'good' if selection_type == 'good' else 'bad'} defects: {selected_defects}")

    if selection_type == "good":
        defect_data['ConvertedDefectType'] = defect_data['DefectType'].apply(
            lambda x: 1 if x in selected_defects else 0)
    else:
        defect_data['ConvertedDefectType'] = defect_data['DefectType'].apply(
            lambda x: 0 if x in selected_defects else 1)
    
    if flip:
        defect_data['Col'] = defect_data['Col'].max() - defect_data['Col']

    return defect_data

class PlotWindow(QMainWindow):
    point_selected = Signal(str)

    def __init__(self, main_ui, web_view, custom_color_map=None, plot_width=1000, plot_height=800, point_size=2):
        super().__init__()
        self.main_ui = main_ui
        self.web_view = web_view
        self.custom_color_map = custom_color_map
        self.plot_width = plot_width
        self.plot_height = plot_height
        self.point_size = point_size
        self.initUI()

    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        self.channel = QWebChannel()
        self.handler = WebEnginePageHandler(self)
        self.channel.registerObject('handler', self.handler)
        self.web_view.page().setWebChannel(self.channel)

        self.plot()

    def get_csv_paths(self):
        number = self.main_ui.input_number.text()
        code = self.main_ui.input_code1.text() if self.main_ui.current_button_name == 'MT' else self.main_ui.input_code1.text()
        current_button_name = self.main_ui.current_button_name
        option = self.main_ui.combo.currentText()
        csv_paths = {
            "LOSS1": [f"D:/Database-PC/{option}/csv/{number}/MT/{code}.csv", f"D:/Database-PC/{option}/csv/{number}/DC2/{code}.csv"],
            "LOSS2": [f"D:/Database-PC/{option}/csv/{number}/DC2/{code}.csv", f"D:/Database-PC/{option}/csv/{number}/INNER1/{code}.csv"],
            "LOSS3": [f"D:/Database-PC/{option}/csv/{number}/INNER1/{code}.csv", f"D:/Database-PC/{option}/csv/{number}/RDL/{code}.csv"],
            "LOSS4": [f"D:/Database-PC/{option}/csv/{number}/RDL/{code}.csv", f"D:/Database-PC/{option}/csv/{number}/INNER2/{code}.csv"],
            "LOSS5": [f"D:/Database-PC/{option}/csv/{number}/INNER2/{code}.csv", f"D:/Database-PC/{option}/csv/{number}/CU/{code}.csv"],
            "LOSS6": [f"D:/Database-PC/{option}/csv/{number}/CU/{code}.csv", f"D:/Database-PC/{option}/csv/{number}/EMC/{code}.csv"]
        }

        print(f"CSV paths: {csv_paths.get(current_button_name, [])}")
        return csv_paths.get(current_button_name, [])

    def plot(self):
        csv_paths = self.get_csv_paths()
        if not csv_paths or len(csv_paths) != 2:
            print(f"Invalid CSV paths for {self.main_ui.current_button_name}")
            return

        try:
            temp_dir = tempfile.mkdtemp()

            # Process first CSV (Good Defects)
            temp_file1 = os.path.join(temp_dir, "temp1.csv")
            flip_first_csv = self.main_ui.current_button_name == 'LOSS1'
            defect_data1 = preprocess_csv(csv_paths[0], selection_type="good", flip=flip_first_csv)
            defect_data1.to_csv(temp_file1, index=False)

            # Process second CSV (Bad Defects)
            temp_file2 = os.path.join(temp_dir, "temp2.csv")
            defect_data2 = preprocess_csv(csv_paths[1], selection_type="bad")
            defect_data2.to_csv(temp_file2, index=False)

            df1 = pd.read_csv(temp_file1)
            df2 = pd.read_csv(temp_file2)

            print("DF1 head:")
            print(df1.head())
            print("DF2 head:")
            print(df2.head())

            print("DF1 Row and Col unique values:")
            print(df1[['Row', 'Col']].drop_duplicates())
            print("DF2 Row and Col unique values:")
            print(df2[['Row', 'Col']].drop_duplicates())

        except Exception as e:
            print(f"Error reading CSV files: {e}")
            shutil.rmtree(temp_dir)
            return

        # Combine dataframes and calculate the difference
        try:
            df_merged = pd.merge(df1, df2, on=['Row', 'Col'], suffixes=('_good', '_bad'))
            df_merged['Difference'] = df_merged['ConvertedDefectType_good'] - df_merged['ConvertedDefectType_bad']
            df_merged['Color'] = df_merged['Difference'].apply(lambda x: 'red' if x == 1 else 'gray')

            print("Merged DF head:")
            print(df_merged.head())
        except Exception as e:
            print(f"Error merging dataframes: {e}")
            shutil.rmtree(temp_dir)
            return

        fig = go.Figure()

        fig.add_trace(go.Scattergl(
            x=df_merged['Col'],
            y=df_merged['Row'],
            mode='markers',
            marker=dict(
                color=df_merged['Color'],
                size=self.point_size,
                opacity=0.6
            )
        ))

        fig.update_layout(
            title=f'Map of Defects - {self.main_ui.current_button_name}',
            title_font=dict(size=20),
            xaxis_title='Col Coordinate',
            yaxis_title='Row Coordinate',
            yaxis=dict(autorange='reversed'),
            margin=dict(l=70, r=30, t=70, b=30),
            plot_bgcolor='black',
            paper_bgcolor='black',
            font=dict(color='white')
        )

        fig.update_xaxes(showgrid=True, gridcolor='gray')
        fig.update_yaxes(showgrid=True, gridcolor='gray')

        # Save the plot as an HTML file and display it
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as temp_file:
            fig.write_html(temp_file.name)

            with open(temp_file.name, 'a') as f:
                f.write('''
                    <script>
                        document.querySelectorAll('g.point').forEach(function(point) {
                            point.addEventListener('dblclick', function(event) {
                                var pointData = event.target.__data__;
                                if (pointData && pointData.customdata && pointData.customdata.length > 0) {
                                    var no = pointData.customdata[0];
                                    new QWebChannel(qt.webChannelTransport, function(channel) {
                                        var handler = channel.objects.handler;
                                        handler.receivePoint(no);
                                    });
                                }
                            });
                        });
                    </script>
                ''')

            self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(temp_file.name)))

        shutil.rmtree(temp_dir)

    @Slot(str)
    def receivePoint(self, no):
        self.main_ui.update_search_field(no)
        self.point_selected.emit(no)

class WebEnginePageHandler(QObject):
    def __init__(self, plot_window):
        super().__init__()
        self.plot_window = plot_window

    @Slot(str)
    def receivePoint(self, no):
        self.plot_window.receivePoint(no)
