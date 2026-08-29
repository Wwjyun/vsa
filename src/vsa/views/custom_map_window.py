"""Window hosting the customizable defect map."""

from __future__ import annotations

import json

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from vsa.models import InspectionSelection
from vsa.paths import csv_path
from vsa.services.data import read_defect_csv
from vsa.ui.widgets import (
    ActionButton,
    AppHeader,
    FieldLabel,
    LegendRow,
    Separator,
    SidePanel,
    StatusPill,
)
from vsa.views.custom_map_plot import CustomMapWidget

_TOGGLE_JS = """
(function () {
    var gd = document.getElementsByClassName('plotly-graph-div')[0];
    if (!gd) { return; }
    var index = gd.data.findIndex(function (trace) { return trace.name === %s; });
    if (index < 0) { return; }
    Plotly.restyle(gd, {'marker.color': %s}, [index]);
    var readout = document.getElementById('red_points_percentage');
    if (readout) { readout.style.display = 'none'; }
}());
"""


class CustomizeMapWindow(QMainWindow):
    def __init__(self, selection: InspectionSelection, map_size=(1000, 1000)):
        super().__init__()
        self.setWindowTitle("Custom defect map")

        self.selection = selection
        self.map_size = map_size
        self.file_path = csv_path(
            selection.product,
            selection.lot_id,
            selection.stage,
            selection.component_id,
        )
        self._red_types: set[str] = set()
        self._counts: dict[str, int] = {}

        self.plot_widget = CustomMapWidget(map_size=map_size)
        self.setCentralWidget(self._build_body())
        self.setMinimumSize(960, 680)
        self.resize(1200, 800)

        self.plot_data()

    # ------------------------------------------------------------------ UI
    def _build_body(self) -> QWidget:
        container = QWidget(self)
        container.setObjectName("window")
        root = QVBoxLayout(container)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        subtitle = (
            f"{self.selection.lot_id} · {self.selection.stage} · {self.selection.component_id}"
        )
        header = AppHeader("Custom defect map", subtitle, container)
        self.status_pill = StatusPill("Plot ready", header)
        header.add_trailing(self.status_pill)
        reset_button = QPushButton("Reset colors", header)
        reset_button.setObjectName("ghost")
        reset_button.clicked.connect(self.reset_colors)
        header.add_trailing(reset_button)
        root.addWidget(header)
        root.addWidget(self._build_toolbar(container))

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        canvas = QWidget(container)
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(20, 20, 20, 20)
        canvas_layout.addWidget(self.plot_widget)
        body.addWidget(canvas, 1)
        self.side_panel = SidePanel(272, container)
        body.addWidget(self.side_panel)
        root.addLayout(body, 1)
        return container

    def _build_toolbar(self, parent: QWidget) -> QFrame:
        bar = QFrame(parent)
        bar.setObjectName("queryBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(18)

        ratio_block = QWidget(bar)
        ratio_layout = QVBoxLayout(ratio_block)
        ratio_layout.setContentsMargins(0, 0, 0, 0)
        ratio_layout.setSpacing(6)
        ratio_layout.addWidget(FieldLabel("Red point ratio", ratio_block))
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        self.ratio_label = QLabel("0.00%", ratio_block)
        self.ratio_label.setObjectName("metricValue")
        self.ratio_hint = QLabel("of 0 defect points", ratio_block)
        self.ratio_hint.setObjectName("hint")
        row.addWidget(self.ratio_label)
        row.addWidget(self.ratio_hint, 0, Qt.AlignBottom)
        ratio_layout.addLayout(row)
        layout.addWidget(ratio_block)
        layout.addWidget(Separator(True, 38, bar), 0, Qt.AlignBottom)

        size_block = QWidget(bar)
        size_layout = QVBoxLayout(size_block)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(6)
        size_layout.addWidget(FieldLabel("Map size", size_block))
        size_value = QLabel(f"{self.map_size[0]} × {self.map_size[1]}", size_block)
        size_value.setObjectName("dataValue")
        size_value.setFixedHeight(36)
        size_layout.addWidget(size_value)
        layout.addWidget(size_block)
        layout.addStretch(1)
        note = QLabel('"ok" rows are filtered out before plotting', bar)
        note.setObjectName("hint")
        layout.addWidget(note, 0, Qt.AlignBottom)
        return bar

    def _build_legend(self) -> None:
        self.side_panel.add_section("Defect type")
        self.legend_rows: dict[str, LegendRow] = {}
        for name, count in sorted(self._counts.items(), key=lambda item: -item[1]):
            row = LegendRow(name, count, parent=self.side_panel)
            row.toggled.connect(self.toggle_defect)
            self.legend_rows[name] = self.side_panel.add(row)
        self.side_panel.add_section("Actions")
        export_button = ActionButton(
            "Export this map",
            f"PNG at {self.map_size[0]} × {self.map_size[1]}",
            parent=self.side_panel,
        )
        export_button.clicked.connect(self.export_map)
        self.side_panel.add(export_button)
        self.side_panel.add_stretch()
        note = QLabel(
            "Click a type to mark it red — same behaviour as the legend, with a persistent "
            "ratio readout.",
            self.side_panel,
        )
        note.setObjectName("hint")
        note.setWordWrap(True)
        self.side_panel.add(Separator(False, parent=self.side_panel))
        self.side_panel.add(note)

    # ---------------------------------------------------------------- data
    @Slot()
    def plot_data(self):
        if not self.file_path.is_file():
            QMessageBox.warning(self, "Custom map error", f"CSV file not found: {self.file_path}")
            return

        frame = read_defect_csv(self.file_path)
        frame = frame[frame["DefectType"] != "ok"]
        self._counts = {
            str(name): int(count) for name, count in frame["DefectType"].value_counts().items()
        }
        self._build_legend()
        self._update_ratio()

        output_path = self.plot_widget.plot_scatter(self.file_path)
        if output_path:
            self.plot_widget.load_html(output_path)

    @Slot(str)
    def toggle_defect(self, name: str) -> None:
        if name in self._red_types:
            self._red_types.discard(name)
            color = "grey"
        else:
            self._red_types.add(name)
            color = "red"
        row = self.legend_rows.get(name)
        if row is not None:
            row.set_selected(name in self._red_types)
        script = _TOGGLE_JS % (json.dumps(name), json.dumps(color))
        self.plot_widget.view.page().runJavaScript(script)
        self._update_ratio()

    def reset_colors(self) -> None:
        for name in list(self._red_types):
            self.toggle_defect(name)

    def _update_ratio(self) -> None:
        total = sum(self._counts.values())
        red = sum(self._counts.get(name, 0) for name in self._red_types)
        ratio = (red / total * 100) if total else 0.0
        self.ratio_label.setText(f"{ratio:.2f}%")
        self.ratio_hint.setText(f"of {total:,} defect points")

    def export_map(self) -> None:
        QMessageBox.information(
            self,
            "Export",
            "Use the Plotly toolbar's camera icon, or Export Map in the main window.",
        )
