"""Reusable widgets for the VSA interface.

Nothing here knows about data, paths, or exports — these are presentation
primitives the windows compose.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from vsa.ui.theme import COLORS, label_font, repolish

LOSS_PATTERN = re.compile(r"^LOSS[1-6]$")
ZOOM_STEPS = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0)


def is_loss_stage(name: str) -> bool:
    return bool(LOSS_PATTERN.match(name.strip().upper()))


class SectionLabel(QLabel):
    """Uppercase, letter-spaced group heading."""

    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setObjectName("sectionLabel")
        self.setFont(label_font(7.5))


class FieldLabel(QLabel):
    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setObjectName("fieldLabel")
        self.setFont(label_font(7.5))


class Separator(QFrame):
    def __init__(self, vertical: bool = True, length: int = 38, parent: QWidget | None = None):
        super().__init__(parent)
        if vertical:
            self.setObjectName("vSeparator")
            self.setFixedSize(1, length)
        else:
            self.setObjectName("hSeparator")
            self.setFixedHeight(1)


class LabeledField(QWidget):
    """A small-caps label stacked above any input widget."""

    def __init__(self, text: str, field: QWidget, width: int | None = None, parent=None):
        super().__init__(parent)
        self.field = field
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.label = FieldLabel(text, self)
        layout.addWidget(self.label)
        layout.addWidget(field)
        if width is not None:
            self.setFixedWidth(width)


class UnitField(QFrame):
    """Compact numeric input with a grey unit prefix (W / H / Point)."""

    def __init__(self, prefix: str, width: int = 96, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("unitField")
        self.setFixedWidth(width)
        self.setFixedHeight(36)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.prefix = QLabel(prefix, self)
        self.prefix.setObjectName("unitPrefix")
        self.prefix.setAlignment(Qt.AlignCenter)
        self.edit = QLineEdit(self)
        self.edit.setObjectName("unitInput")
        layout.addWidget(self.prefix)
        layout.addWidget(self.edit)
        self.edit.installEventFilter(self)

    def eventFilter(self, watched, event):  # noqa: N802 - Qt naming
        if watched is self.edit and event.type() in (event.Type.FocusIn, event.Type.FocusOut):
            self.setProperty("focused", "true" if event.type() == event.Type.FocusIn else "false")
            repolish(self)
        return super().eventFilter(watched, event)


class StatusPill(QFrame):
    """Rounded status readout; wraps the label the windows already write to."""

    def __init__(self, text: str = "Ready", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("statusPill")
        self.setFixedHeight(26)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 12, 0)
        layout.setSpacing(7)
        self.dot = QLabel(self)
        self.dot.setObjectName("statusDot")
        self.dot.setFixedSize(8, 8)
        self.label = QLabel(text, self)
        self.label.setObjectName("statusText")
        layout.addWidget(self.dot)
        layout.addWidget(self.label)

    def set_busy(self, busy: bool) -> None:
        self.dot.setProperty("state", "busy" if busy else "idle")
        repolish(self.dot)


class AppHeader(QFrame):
    """Top chrome: app mark, window name, subtitle, and a right-hand slot."""

    def __init__(self, name: str, subtitle: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(44)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(9)
        mark = QLabel("V", self)
        mark.setObjectName("appMark")
        mark.setFixedSize(20, 20)
        mark.setAlignment(Qt.AlignCenter)
        self.name_label = QLabel(name, self)
        self.name_label.setObjectName("appName")
        self.subtitle_label = QLabel(subtitle, self)
        self.subtitle_label.setObjectName("appSubtitle")
        layout.addWidget(mark)
        layout.addWidget(self.name_label)
        layout.addWidget(self.subtitle_label)
        layout.addStretch(1)
        self.trailing = QHBoxLayout()
        self.trailing.setContentsMargins(0, 0, 0, 0)
        self.trailing.setSpacing(8)
        layout.addLayout(self.trailing)

    def add_trailing(self, widget: QWidget) -> None:
        self.trailing.addWidget(widget)

    def set_subtitle(self, text: str) -> None:
        self.subtitle_label.setText(text)


class ActionButton(QPushButton):
    """Two-line button: bold action, quiet explanation."""

    def __init__(self, title: str, subtitle: str = "", variant: str = "default", parent=None):
        super().__init__(parent)
        self.setObjectName("actionButton")
        self.setProperty("variant", variant)
        self.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(1)
        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("actionTitle")
        self.subtitle_label = QLabel(subtitle, self)
        self.subtitle_label.setObjectName("actionSub")
        for label in (self.title_label, self.subtitle_label):
            label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        self.subtitle_label.setVisible(bool(subtitle))

    def set_subtitle(self, text: str) -> None:
        self.subtitle_label.setText(text)
        self.subtitle_label.setVisible(bool(text))


class StageButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setObjectName("stageButton")
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setCursor(Qt.PointingHandCursor)
        self.apply_kind()

    def setText(self, text: str) -> None:  # noqa: N802 - Qt naming
        super().setText(text)
        self.apply_kind()

    def apply_kind(self) -> None:
        self.setProperty("kind", "loss" if is_loss_stage(self.text()) else "stage")
        repolish(self)


class StageRail(QFrame):
    """The process pipeline: stage buttons threaded on a painted timeline.

    LOSS steps sit between the two stages they compare, which is what
    ``LOSS_STAGE_PAIRS`` actually means.
    """

    stage_selected = Signal(str)

    def __init__(self, count: int = 14, width: int = 262, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("rail")
        self.setFixedWidth(width)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        head = QWidget(self)
        head_layout = QHBoxLayout(head)
        head_layout.setContentsMargins(18, 16, 18, 10)
        head_layout.addWidget(SectionLabel("Process pipeline", head))
        head_layout.addStretch(1)
        self.count_label = QLabel(str(count), head)
        self.count_label.setObjectName("hint")
        head_layout.addWidget(self.count_label)
        outer.addWidget(head)

        body = QWidget(self)
        self.body_layout = QVBoxLayout(body)
        self.body_layout.setContentsMargins(46, 0, 14, 14)
        self.body_layout.setSpacing(2)
        self.buttons: list[StageButton] = []
        for index in range(count):
            button = StageButton(f"Button {index + 1}", body)
            button.clicked.connect(self._emit_selection)
            self.buttons.append(button)
            self.body_layout.addWidget(button)
        self.body_layout.addStretch(1)
        outer.addWidget(body, 1)
        self._body = body

    def _emit_selection(self) -> None:
        sender = self.sender()
        if isinstance(sender, StageButton):
            self.stage_selected.emit(sender.text())

    def set_names(self, names: Iterable[str]) -> None:
        names = list(names)
        for index, button in enumerate(self.buttons):
            button.setText(names[index] if index < len(names) else f"Button {index + 1}")
        self.update()

    def set_current(self, name: str) -> None:
        for button in self.buttons:
            if button.text() == name:
                button.setChecked(True)
                return

    def paintEvent(self, event):  # noqa: N802 - Qt naming
        super().paintEvent(event)
        if not self.buttons:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        axis = 28
        first = self.buttons[0]
        last = self.buttons[-1]
        top = first.mapTo(self, first.rect().center()).y()
        bottom = last.mapTo(self, last.rect().center()).y()
        painter.setPen(QPen(QColor(COLORS["line"]), 2))
        painter.drawLine(axis, top, axis, bottom)
        for button in self.buttons:
            loss = is_loss_stage(button.text())
            center = button.mapTo(self, button.rect().center()).y()
            radius = 3.5 if loss else 5.0
            if button.isChecked():
                fill = QColor(COLORS["loss"] if loss else COLORS["accent"])
                ring = QColor(COLORS["loss_line"] if loss else COLORS["accent_line"])
            else:
                fill = QColor(COLORS["dot_loss_idle"] if loss else COLORS["dot_idle"])
                ring = QColor(COLORS["line"])
            painter.setPen(QPen(ring, 2))
            painter.setBrush(fill)
            painter.drawEllipse(
                int(axis - radius), int(center - radius), int(radius * 2), int(radius * 2)
            )
        painter.end()


class PreviewPane(QWidget):
    """Map preview: stage chip, path, zoom controls, and the scrollable image."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QFrame(self)
        toolbar.setObjectName("previewToolbar")
        bar = QHBoxLayout(toolbar)
        bar.setContentsMargins(20, 12, 20, 12)
        bar.setSpacing(12)
        self.stage_chip = QLabel("—", toolbar)
        self.stage_chip.setObjectName("stageChip")
        self.chip_suffix = QLabel("no stage selected", toolbar)
        self.chip_suffix.setObjectName("chipSuffix")
        self.path_label = QLabel("", toolbar)
        self.path_label.setObjectName("pathLabel")
        bar.addWidget(self.stage_chip)
        bar.addWidget(self.chip_suffix)
        bar.addWidget(self.path_label)
        bar.addStretch(1)

        zoom_group = QFrame(toolbar)
        zoom_group.setObjectName("zoomGroup")
        zoom_layout = QHBoxLayout(zoom_group)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        zoom_layout.setSpacing(0)
        self.zoom_out_button = QPushButton("−", zoom_group)
        self.zoom_label = QLabel("Fit", zoom_group)
        self.zoom_label.setObjectName("statusText")
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setFixedWidth(46)
        self.zoom_in_button = QPushButton("+", zoom_group)
        self.fit_button = QPushButton("Fit", zoom_group)
        for button in (self.zoom_out_button, self.zoom_in_button, self.fit_button):
            button.setObjectName("zoomButton")
            button.setCursor(Qt.PointingHandCursor)
        zoom_layout.addWidget(self.zoom_out_button)
        zoom_layout.addWidget(self.zoom_label)
        zoom_layout.addWidget(self.zoom_in_button)
        zoom_layout.addWidget(Separator(True, 26, zoom_group))
        zoom_layout.addWidget(self.fit_button)
        bar.addWidget(zoom_group)
        layout.addWidget(toolbar)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName("previewArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.label = QLabel(self.scroll_area)
        self.label.setObjectName("previewLabel")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumSize(320, 240)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.setWidget(self.label)
        holder = QWidget(self)
        holder_layout = QVBoxLayout(holder)
        holder_layout.setContentsMargins(20, 20, 20, 20)
        holder_layout.addWidget(self.scroll_area)
        holder.setObjectName("previewHolder")
        layout.addWidget(holder, 1)

        self._source: QPixmap | None = None
        self._zoom: float | None = None  # None means "fit"
        self.zoom_in_button.clicked.connect(lambda: self._step_zoom(1))
        self.zoom_out_button.clicked.connect(lambda: self._step_zoom(-1))
        self.fit_button.clicked.connect(self.fit)
        self.show_message("Select a product, enter Lot ID and Component ID, then press Search.")

    # -- content ---------------------------------------------------------
    def show_pixmap(self, pixmap: QPixmap) -> None:
        self._source = pixmap
        self._zoom = None
        self._render()

    def show_message(self, text: str) -> None:
        self._source = None
        self.label.setPixmap(QPixmap())
        self.label.setText(text)

    def set_stage(self, name: str, description: str = "") -> None:
        self.stage_chip.setText(name or "—")
        self.stage_chip.setProperty("kind", "loss" if is_loss_stage(name) else "stage")
        repolish(self.stage_chip)
        self.chip_suffix.setText(description)

    def set_path(self, text: str) -> None:
        self.path_label.setText(text)

    # -- zoom ------------------------------------------------------------
    def fit(self) -> None:
        self._zoom = None
        self._render()

    def _step_zoom(self, direction: int) -> None:
        current = self._zoom or 1.0
        steps = list(ZOOM_STEPS)
        index = min(range(len(steps)), key=lambda i: abs(steps[i] - current))
        index = max(0, min(len(steps) - 1, index + direction))
        self._zoom = steps[index]
        self._render()

    def _render(self) -> None:
        if self._source is None or self._source.isNull():
            return
        if self._zoom is None:
            target = self.scroll_area.viewport().size() - QSize(8, 8)
            scaled = self._source.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.zoom_label.setText("Fit")
        else:
            scaled = self._source.scaled(
                self._source.size() * self._zoom, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.zoom_label.setText(f"{int(self._zoom * 100)}%")
        self.label.setText("")
        self.label.setPixmap(scaled)
        self.label.adjustSize()

    def resizeEvent(self, event):  # noqa: N802 - Qt naming
        super().resizeEvent(event)
        if self._zoom is None:
            self._render()


class DataRow(QFrame):
    """Mono key / value row used by Diagnostics and the side panels."""

    def __init__(self, key: str, value: str, boxed: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("dataRow" if boxed else "plainRow")
        layout = QHBoxLayout(self)
        if boxed:
            layout.setContentsMargins(11, 8, 11, 8)
        else:
            layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(12)
        self.key_label = QLabel(key, self)
        self.key_label.setObjectName("dataKey")
        self.value_label = QLabel(value, self)
        self.value_label.setObjectName("dataValue")
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.key_label)
        layout.addStretch(1)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class MetricCard(QFrame):
    """Big number + caption, used for the loss rate and red-point ratio."""

    def __init__(self, value: str, caption: str, alert: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("cardAlert" if alert else "card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        self.value_label = QLabel(value, self)
        self.value_label.setObjectName("metricValue")
        self.caption_label = QLabel(caption, self)
        self.caption_label.setObjectName("cardCaption")
        self.caption_label.setWordWrap(True)
        layout.addWidget(self.value_label)
        layout.addWidget(self.caption_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def set_caption(self, caption: str) -> None:
        self.caption_label.setText(caption)


class SidePanel(QFrame):
    """Right-hand column with section headings; the windows fill it."""

    def __init__(self, width: int = 272, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("sidePanel")
        self.setFixedWidth(width)
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(16, 16, 16, 16)
        self.layout_.setSpacing(10)

    def add_section(self, title: str) -> None:
        if self.layout_.count():
            self.layout_.addSpacing(10)
        self.layout_.addWidget(SectionLabel(title, self))

    def add(self, widget: QWidget) -> QWidget:
        self.layout_.addWidget(widget)
        return widget

    def add_layout(self, layout) -> None:
        self.layout_.addLayout(layout)

    def add_stretch(self) -> None:
        self.layout_.addStretch(1)


class LegendRow(QFrame):
    """Clickable defect-type row: swatch, name, count. Emits the type name."""

    toggled = Signal(str)

    def __init__(self, name: str, count: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("legendRow")
        self.setProperty("selected", "false")
        self.setCursor(Qt.PointingHandCursor)
        self._name = name
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 9, 10, 9)
        layout.setSpacing(9)
        self.swatch = QLabel(self)
        self.swatch.setFixedSize(10, 10)
        self.swatch.setStyleSheet(
            f"border-radius:5px;background:{COLORS['muted_light']};border:1px solid #2F4F4F;"
        )
        self.name_label = QLabel(name, self)
        self.name_label.setObjectName("dataValue")
        self.count_label = QLabel(f"{count:,}", self)
        self.count_label.setObjectName("dataKey")
        layout.addWidget(self.swatch)
        layout.addWidget(self.name_label, 1)
        layout.addWidget(self.count_label)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", "true" if selected else "false")
        color = COLORS["danger"] if selected else COLORS["muted_light"]
        self.swatch.setStyleSheet(f"border-radius:5px;background:{color};border:1px solid #2F4F4F;")
        repolish(self)

    def mouseReleaseEvent(self, event):  # noqa: N802 - Qt naming
        if event.button() == Qt.LeftButton:
            self.toggled.emit(self._name)
        super().mouseReleaseEvent(event)


def soft_shadow(widget: QWidget, blur: int = 10, alpha: int = 26) -> None:
    """The one place shadows come from — QSS has no box-shadow."""

    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, 1)
    effect.setColor(QColor(16, 20, 26, alpha))
    widget.setGraphicsEffect(effect)
