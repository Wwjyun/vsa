"""Loss-map window: light chrome around the interactive Plotly canvas."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from vsa.config import LOSS_STAGE_PAIRS
from vsa.ui.widgets import (
    ActionButton,
    AppHeader,
    DataRow,
    FieldLabel,
    MetricCard,
    Separator,
    SidePanel,
    StatusPill,
)
from vsa.views.loss_map_plot import LossMapPlotController


class LossMapWindow(QWidget):
    def __init__(self, main_ui):
        super().__init__()
        self.setObjectName("window")
        self.main_ui = main_ui
        self.setWindowTitle("Loss map")
        self.setMinimumSize(960, 680)
        self.resize(1200, 800)
        self.setup_ui()

    # ------------------------------------------------------------------ UI
    def setup_ui(self):
        stage = self.get_current_button_name()
        pair = LOSS_STAGE_PAIRS.get(stage)
        pair_text = f"{stage} · {pair[0]} → {pair[1]}" if pair else stage

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = AppHeader("Loss map", pair_text, self)
        self.status_pill = StatusPill("Plot ready", header)
        header.add_trailing(self.status_pill)
        replot_button = QPushButton("Replot", header)
        replot_button.setObjectName("ghost")
        replot_button.clicked.connect(self.plot_data)
        header.add_trailing(replot_button)
        root.addWidget(header)
        root.addWidget(self._build_toolbar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        canvas = QWidget(self)
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(20, 20, 20, 20)
        self.web_view = QWebEngineView(canvas)
        canvas_layout.addWidget(self.web_view)
        body.addWidget(canvas, 1)
        body.addWidget(self._build_side_panel(pair))
        root.addLayout(body, 1)
        root.addWidget(self._build_footer_bar())

        self.plot_data()

    def _build_toolbar(self) -> QFrame:
        options = self.main_ui.plot_options()
        bar = QFrame(self)
        bar.setObjectName("queryBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(18)

        block = QWidget(bar)
        block_layout = QVBoxLayout(block)
        block_layout.setContentsMargins(0, 0, 0, 0)
        block_layout.setSpacing(6)
        block_layout.addWidget(FieldLabel("Classification", block))
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        self.good_button = QPushButton("Good defects", block)
        self.bad_button = QPushButton("Bad defects", block)
        for button in (self.good_button, self.bad_button):
            button.setFixedHeight(36)
            button.clicked.connect(self.plot_data)
            row.addWidget(button)
        block_layout.addLayout(row)
        layout.addWidget(block)
        layout.addWidget(Separator(True, 38, bar), 0, Qt.AlignBottom)

        readout = QWidget(bar)
        readout_layout = QVBoxLayout(readout)
        readout_layout.setContentsMargins(0, 0, 0, 0)
        readout_layout.setSpacing(6)
        readout_layout.addWidget(FieldLabel("Map options", readout))
        value = QLabel(
            f"{options['plot_width']} × {options['plot_height']} · point {options['point_size']}",
            readout,
        )
        value.setObjectName("dataValue")
        value.setFixedHeight(36)
        readout_layout.addWidget(value)
        layout.addWidget(readout)
        layout.addStretch(1)
        hint = QLabel("Double-click a point → PKG NO", bar)
        hint.setObjectName("hint")
        layout.addWidget(hint, 0, Qt.AlignBottom)
        return bar

    def _build_side_panel(self, pair) -> SidePanel:
        panel = SidePanel(272, self)
        panel.add_section("Loss result")
        caption = f"good at {pair[0]} → bad at {pair[1]}" if pair else "select a LOSS stage"
        self.loss_metric = MetricCard("—", caption, alert=True, parent=panel)
        panel.add(self.loss_metric)
        self.lost_row = DataRow("lost", "—", parent=panel)
        self.kept_row = DataRow("kept", "—", parent=panel)
        panel.add(self.lost_row)
        panel.add(self.kept_row)

        panel.add_section("Actions")
        reselect = ActionButton("Reselect defects", "Reopen good / bad pickers", parent=panel)
        reselect.clicked.connect(self.plot_data)
        panel.add(reselect)

        panel.add_stretch()
        panel.add(Separator(False, parent=panel))
        panel.add_section("Source")
        panel.add(
            DataRow("lot", self.main_ui.input_number.text() or "—", boxed=False, parent=panel)
        )
        panel.add(
            DataRow("component", self.main_ui.input_code1.text() or "—", boxed=False, parent=panel)
        )
        panel.add(DataRow("join", "inner · 1:1", boxed=False, parent=panel))
        return panel

    def _build_footer_bar(self) -> QFrame:
        bar = QFrame(self)
        bar.setObjectName("footerBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(12)
        self.pkg_field = QLineEdit(bar)
        self.pkg_field.setReadOnly(True)
        self.pkg_field.setPlaceholderText("—")
        hint = QLabel("sent from the plot over QWebChannel", bar)
        hint.setObjectName("hint")
        open_button = QPushButton("Open ROI image", bar)
        open_button.setObjectName("primary")
        open_button.setFixedHeight(36)
        open_button.clicked.connect(self.main_ui.search_image)
        layout.addWidget(FieldLabel("PKG NO", bar))
        layout.addWidget(self.pkg_field, 1)
        layout.addWidget(hint)
        layout.addWidget(open_button)
        return bar

    # ---------------------------------------------------------------- data
    def plot_data(self):
        if hasattr(self, "plot_window"):
            self.plot_window.close()
        self.status_pill.set_busy(True)
        self.status_pill.label.setText("Plotting…")
        self.plot_window = LossMapPlotController(
            self.main_ui, self.web_view, **self.main_ui.plot_options()
        )
        self.plot_window.point_selected.connect(self._on_point_selected)
        self._update_summary()
        self.status_pill.set_busy(False)
        self.status_pill.label.setText("Plot ready")

    def _on_point_selected(self, no: str) -> None:
        self.pkg_field.setText(no)

    def _update_summary(self) -> None:
        """Fill the side panel from the merged frame when the controller exposes it."""

        merged = getattr(self.plot_window, "merged", None)
        if merged is None or len(merged) == 0:
            return
        lost = int((merged["Color"] == "red").sum())
        total = int(len(merged))
        self.loss_metric.set_value(f"{lost / total * 100:.2f}%")
        self.lost_row.set_value(f"{lost:,}")
        self.kept_row.set_value(f"{total - lost:,}")

    def get_current_button_name(self):
        return self.main_ui.current_button_name

    def closeEvent(self, event):
        if hasattr(self, "plot_window"):
            self.plot_window.close()
        super().closeEvent(event)
