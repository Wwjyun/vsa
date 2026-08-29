"""Customizable defect map with legend-driven red-point ratio."""

import tempfile
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QVBoxLayout, QWidget

from vsa.services.data import read_defect_csv, validate_defect_frame
from vsa.services.plotly_assets import PLOTLY_BUNDLE_NAME, write_plotly_bundle


def load_data_from_file(file_path):
    return read_defect_csv(file_path)


def generate_map(df, output_path, map_size=(1000, 1000), title_fontsize=20, margin=None):
    """Write an interactive defect map. ``map_size`` is (width, height) in pixels."""

    if map_size[0] < 100 or map_size[1] < 100:
        raise ValueError("Map width and height must be at least 100 pixels.")
    if title_fontsize < 1:
        raise ValueError("Title font size must be positive.")
    df = validate_defect_frame(df)
    margin = margin or dict(l=70, r=30, b=70, t=70)
    # Filter out rows where DefectType is "ok"
    df_filtered = df[df["DefectType"] != "ok"]
    df_sorted = df_filtered.sort_values(by=["Col", "Row"])

    fig = go.Figure()

    total_points = len(df_filtered)

    for defect_type in df_filtered["DefectType"].unique():
        subset = df_sorted[df_sorted["DefectType"] == defect_type]
        fig.add_trace(
            go.Scatter(
                x=subset["Col"],
                y=subset["Row"],
                mode="markers",
                marker=dict(size=5, color="grey", line=dict(width=1, color="DarkSlateGrey")),
                name=defect_type,
            )
        )

    fig.update_layout(
        title="Map of Defects",
        xaxis_title="Col Coordinate",
        yaxis_title="Row Coordinate",
        yaxis=dict(scaleanchor="x", scaleratio=1, autorange="reversed"),
        legend_title="Defect Type",
        legend=dict(itemsizing="constant"),
        width=map_size[0],
        height=map_size[1],
        margin=margin,  # Adjust margins
        plot_bgcolor="white",  # Set background color to white
        paper_bgcolor="white",  # Set paper background color to white
    )

    fig.update_annotations(font_size=title_fontsize)

    # Add JavaScript for changing color on legend click and updating ratio
    js_code = f"""
    <script>
    var total_points = {total_points};
    var myPlot = document.getElementsByClassName('plotly-graph-div')[0];
    var percentageDiv = document.createElement('div');
    percentageDiv.style.position = 'absolute';
    percentageDiv.style.top = '95%';
    percentageDiv.style.left = '80%';
    percentageDiv.style.fontSize = '{title_fontsize}px';
    percentageDiv.id = 'red_points_percentage';
    percentageDiv.innerHTML = 'Red Points: 0.00%';
    document.body.appendChild(percentageDiv);

    myPlot.on('plotly_legendclick', function(data) {{
        var update = {{}};
        var trace = data.curveNumber;
        var legendItem = myPlot.data[trace];
        var red_points = 0;

        if (legendItem.marker.color === 'grey') {{
            update['marker.color'] = 'red';
        }} else {{
            update['marker.color'] = 'grey';
        }}
        
        Plotly.restyle(myPlot, update, [trace]);

        // Update the count of red points
        myPlot.data.forEach((trace) => {{
            if (trace.marker.color === 'red') {{
                red_points += trace.x.length;
            }}
        }});

        var percentage = total_points === 0 ? '0.00' : (red_points / total_points * 100).toFixed(2);
        var ratioText = `Red Points: ${{percentage}}%`;
        document.getElementById('red_points_percentage').innerText = ratioText;

        return false;
    }});
    </script>
    """

    output = Path(output_path)
    write_plotly_bundle(output.parent)
    fig_html = pio.to_html(fig, full_html=False, include_plotlyjs=PLOTLY_BUNDLE_NAME)
    output.write_text(fig_html + js_code, encoding="utf-8")
    return output


class CustomMapWidget(QWidget):
    def __init__(self, map_size=(1000, 1000)):
        super().__init__()
        self.map_size = map_size
        self.view = QWebEngineView()
        self.temp_dir = tempfile.TemporaryDirectory(prefix="vsa-custom-map-")

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

    def plot_scatter(self, file_path):
        df = load_data_from_file(file_path)
        if df.empty:
            return None

        output_path = Path(self.temp_dir.name) / "custom-map.html"
        generate_map(df, output_path, map_size=self.map_size)
        return output_path

    def load_html(self, file_path):
        url = QUrl.fromLocalFile(str(Path(file_path).resolve()))
        self.view.setUrl(url)

    def closeEvent(self, event):
        self.view.setUrl(QUrl("about:blank"))
        self.temp_dir.cleanup()
        super().closeEvent(event)
