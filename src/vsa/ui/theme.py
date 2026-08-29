"""Design tokens and the application stylesheet.

The whole visual language lives here: colors, families, radii, and one QSS
string. No widget file hard-codes a color.
"""

from __future__ import annotations

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

COLORS = {
    "text": "#14181D",
    "text_soft": "#2B323B",
    "muted": "#656E7A",
    "muted_light": "#8B949F",
    "faint": "#A6ADB6",
    "line": "#EAECF0",
    "border": "#DCDFE4",
    "field_border": "#CDD2D9",
    "bg_app": "#F6F7F9",
    "bg_chrome": "#F0F2F5",
    "panel": "#FFFFFF",
    "accent": "#1A5FD4",
    "accent_hover": "#1750B6",
    "accent_press": "#133F92",
    "accent_tint": "#EAF1FD",
    "accent_line": "#C3D7F6",
    "loss": "#9A5B12",
    "loss_tint": "#FDF3E6",
    "loss_line": "#E9D0AB",
    "danger": "#C02B2B",
    "danger_tint": "#FDECEC",
    "danger_line": "#F2C8C8",
    "ok": "#157A44",
    "dot_idle": "#C4C9D1",
    "dot_loss_idle": "#DFE3E8",
    "plot_bg": "#0D0F12",
    "plot_line": "#24282E",
}

#: Preferred UI family, with a Windows-safe fallback chain.
UI_FAMILY = '"Inter Tight", "Inter", "Segoe UI", sans-serif'
MONO_FAMILY = '"JetBrains Mono", "Cascadia Mono", "Consolas", monospace'


def _first_installed(candidates: tuple[str, ...], fallback: str) -> str:
    families = set(QFontDatabase.families())
    for candidate in candidates:
        if candidate in families:
            return candidate
    return fallback


def resolved_ui_family() -> str:
    return _first_installed(("Inter Tight", "Inter", "Segoe UI"), "Segoe UI")


def resolved_mono_family() -> str:
    return _first_installed(("JetBrains Mono", "Cascadia Mono", "Consolas"), "Courier New")


def label_font(size: float = 10.0, *, mono: bool = True, weight: int = QFont.DemiBold) -> QFont:
    """Uppercase, letter-spaced section label font (QSS cannot express these)."""

    font = QFont(resolved_mono_family() if mono else resolved_ui_family())
    font.setPointSizeF(size)
    font.setWeight(weight)
    font.setLetterSpacing(QFont.PercentageSpacing, 108)
    font.setCapitalization(QFont.AllUppercase)
    return font


def mono_font(size: float = 12.0, weight: int = QFont.Medium) -> QFont:
    font = QFont(resolved_mono_family())
    font.setPointSizeF(size)
    font.setWeight(weight)
    return font


QSS = """
* { outline: 0; }

QWidget {
    font-family: "Inter Tight", "Inter", "Segoe UI", sans-serif;
    font-size: 13px;
    color: #14181D;
}
QWidget#window, QDialog, QMainWindow { background: #F6F7F9; }

/* ---------- chrome bars ---------- */
QFrame#titleBar { background: #F0F2F5; border: none; border-bottom: 1px solid #DCDFE4; }
QFrame#queryBar, QFrame#footerBar, QFrame#previewToolbar,
QFrame#sidePanel, QFrame#rail { background: #FFFFFF; border: none; }
QFrame#queryBar { border-bottom: 1px solid #EAECF0; }
QFrame#footerBar { border-top: 1px solid #EAECF0; }
QFrame#previewToolbar { border-bottom: 1px solid #EAECF0; }
QFrame#sidePanel { border-left: 1px solid #EAECF0; }
QFrame#rail { border-right: 1px solid #EAECF0; }
QFrame#vSeparator { background: #EAECF0; max-width: 1px; }
QFrame#hSeparator { background: #EAECF0; max-height: 1px; }

QLabel#appMark {
    background: #14181D; color: #FFFFFF; border-radius: 5px;
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 9px; font-weight: 700;
}
QLabel#appName { font-size: 13px; font-weight: 600; color: #14181D; }
QLabel#appSubtitle { font-size: 13px; color: #8B949F; }
QLabel#sectionLabel { color: #8B949F; }
QLabel#fieldLabel { color: #8B949F; }
QLabel#hint { color: #A6ADB6; font-size: 11px; }
QLabel#pathLabel {
    color: #A6ADB6; font-size: 11px;
    font-family: "JetBrains Mono", "Consolas", monospace;
}
QLabel#metricValue {
    color: #C02B2B; font-size: 26px; font-weight: 600;
    font-family: "JetBrains Mono", "Consolas", monospace;
}

/* ---------- status pill ---------- */
QFrame#statusPill { background: #FFFFFF; border: 1px solid #DCDFE4; border-radius: 14px; }
QLabel#statusText { font-size: 11px; font-weight: 500; color: #3C444E; }
QLabel#statusDot { border-radius: 4px; background: #157A44; }
QLabel#statusDot[state="busy"] { background: #1A5FD4; }

/* ---------- inputs ---------- */
QLineEdit {
    background: #FFFFFF; border: 1px solid #CDD2D9; border-radius: 6px;
    padding: 0 10px; min-height: 34px;
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 13px; font-weight: 500;
    selection-background-color: #C3D7F6; selection-color: #14181D;
}
QLineEdit:focus { border: 1px solid #1A5FD4; }
QLineEdit:disabled { background: #F6F7F9; color: #A6ADB6; }

QComboBox {
    background: #FFFFFF; border: 1px solid #CDD2D9; border-radius: 6px;
    padding: 0 10px; min-height: 34px; font-size: 13px; font-weight: 500;
}
QComboBox:focus, QComboBox:on { border: 1px solid #1A5FD4; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox::down-arrow {
    image: none; border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid #8B949F; width: 0; height: 0; margin-right: 8px;
}
QComboBox QAbstractItemView {
    background: #FFFFFF; border: 1px solid #DCDFE4; border-radius: 6px;
    padding: 4px; selection-background-color: #EAF1FD; selection-color: #1A5FD4;
    outline: 0;
}

QFrame#unitField { background: #FFFFFF; border: 1px solid #CDD2D9; border-radius: 6px; }
QFrame#unitField[focused="true"] { border: 1px solid #1A5FD4; }
QLabel#unitPrefix {
    background: #F6F7F9; color: #8B949F; font-size: 11px; font-weight: 500;
    border-right: 1px solid #EAECF0;
    border-top-left-radius: 5px; border-bottom-left-radius: 5px;
    padding: 0 8px;
}
QLineEdit#unitInput { border: none; background: transparent; padding: 0 8px; min-height: 32px; }

/* ---------- buttons ---------- */
QPushButton {
    background: #FFFFFF; border: 1px solid #CDD2D9; border-radius: 6px;
    padding: 0 16px; min-height: 34px; font-size: 13px; font-weight: 500; color: #14181D;
}
QPushButton:hover { background: #F6F7F9; border-color: #A6ADB6; }
QPushButton:pressed { background: #EFF1F4; }
QPushButton:disabled { color: #A6ADB6; border-color: #E4E7EB; background: #FAFBFC; }

QPushButton#primary {
    background: #1A5FD4; border: 1px solid #1A5FD4; color: #FFFFFF;
    font-weight: 600; padding: 0 22px;
}
QPushButton#primary:hover { background: #1750B6; border-color: #1750B6; }
QPushButton#primary:pressed { background: #133F92; border-color: #133F92; }

QPushButton#ghost {
    background: #FFFFFF; border: 1px solid #DCDFE4; color: #3C444E;
    font-size: 12px; padding: 0 11px; min-height: 26px;
}
QPushButton#ghost:hover { background: #F6F7F9; border-color: #C4C9D1; }

QPushButton#zoomButton {
    background: transparent; border: none; border-radius: 0;
    min-height: 26px; min-width: 30px; padding: 0 8px; color: #3C444E; font-size: 12px;
}
QPushButton#zoomButton:hover { background: #EAECF0; }
QFrame#zoomGroup { background: #F6F7F9; border: 1px solid #E4E7EB; border-radius: 6px; }

/* ---------- stage rail ---------- */
QPushButton#stageButton {
    background: transparent; border: 1px solid transparent; border-radius: 7px;
    text-align: left; padding: 0 10px; min-height: 36px;
    font-family: "JetBrains Mono", "Consolas", monospace;
    font-size: 13px; font-weight: 500; color: #2B323B;
}
QPushButton#stageButton:hover { background: #F6F7F9; }
QPushButton#stageButton:checked {
    background: #EAF1FD; border-color: #C3D7F6; color: #1A5FD4; font-weight: 600;
}
QPushButton#stageButton[kind="loss"] {
    min-height: 30px; font-size: 12px; font-weight: 400; color: #8B949F;
}
QPushButton#stageButton[kind="loss"]:checked {
    background: #FDF3E6; border-color: #E9D0AB; color: #9A5B12; font-weight: 600;
}

/* ---------- action buttons (two-line) ---------- */
QPushButton#actionButton { text-align: left; padding: 8px 12px; min-height: 40px; }
QPushButton#actionButton[variant="primary"] {
    background: #1A5FD4; border-color: #1A5FD4;
}
QPushButton#actionButton[variant="primary"]:hover { background: #1750B6; border-color: #1750B6; }
QPushButton#actionButton QLabel { background: transparent; }
QPushButton#actionButton QLabel#actionTitle { font-size: 13px; font-weight: 600; color: #14181D; }
QPushButton#actionButton QLabel#actionSub { font-size: 11px; color: #8B949F; }
QPushButton#actionButton[variant="primary"] QLabel#actionTitle { color: #FFFFFF; }
QPushButton#actionButton[variant="primary"] QLabel#actionSub { color: #C9DBF7; }

QPushButton#gridButton { text-align: left; padding: 0 10px; min-height: 34px; font-size: 12px; }

/* ---------- stage chip ---------- */
QLabel#stageChip {
    background: #EAF1FD; border: 1px solid #C3D7F6; border-radius: 6px;
    color: #1A5FD4; padding: 4px 10px; font-weight: 600;
    font-family: "JetBrains Mono", "Consolas", monospace; font-size: 12px;
}
QLabel#stageChip[kind="loss"] { background: #FDF3E6; border-color: #E9D0AB; color: #9A5B12; }
QLabel#chipSuffix { color: #8B949F; font-size: 11px; }

/* ---------- preview ---------- */
QScrollArea#previewArea { background: #F6F7F9; border: none; }
QScrollArea#previewArea > QWidget > QWidget { background: #F6F7F9; }
QLabel#previewLabel {
    background: #FFFFFF; border: 1px solid #DCDFE4; border-radius: 10px;
    color: #656E7A; font-size: 12px;
}

/* ---------- data rows / cards ---------- */
QFrame#card { background: #FFFFFF; border: 1px solid #EAECF0; border-radius: 8px; }
QFrame#cardAlert { background: #FDECEC; border: 1px solid #F2C8C8; border-radius: 8px; }
QLabel#cardCaption { color: #B06060; font-size: 11px; }
QFrame#dataRow { background: #FFFFFF; border: 1px solid #EAECF0; border-radius: 7px; }
QLabel#dataKey {
    color: #8B949F; font-size: 12px;
    font-family: "JetBrains Mono", "Consolas", monospace;
}
QLabel#dataValue {
    color: #14181D; font-size: 12px; font-weight: 500;
    font-family: "JetBrains Mono", "Consolas", monospace;
}
QFrame#legendRow { background: #FFFFFF; border: 1px solid #EAECF0; border-radius: 7px; }
QFrame#legendRow[selected="true"] { background: #FDECEC; border-color: #F2C8C8; }
QFrame#legendRow:hover { border-color: #A6ADB6; }

/* ---------- scrollbars ---------- */
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #CDD2D9; border-radius: 5px; min-height: 28px; }
QScrollBar::handle:vertical:hover { background: #A6ADB6; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: #CDD2D9; border-radius: 5px; min-width: 28px; }
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {
    background: none; border: none; height: 0; width: 0;
}

/* ---------- dialogs / messages ---------- */
QMessageBox { background: #FFFFFF; }
QMessageBox QLabel { font-size: 13px; color: #2B323B; }
QMessageBox QPushButton { min-width: 76px; }
QCheckBox { spacing: 9px; font-size: 13px; }
QCheckBox::indicator {
    width: 16px; height: 16px; border: 1px solid #CDD2D9; border-radius: 4px; background: #FFFFFF;
}
QCheckBox::indicator:hover { border-color: #A6ADB6; }
QCheckBox::indicator:checked { background: #1A5FD4; border-color: #1A5FD4; }
QToolTip {
    background: #14181D; color: #FFFFFF; border: none; border-radius: 5px;
    padding: 5px 8px; font-size: 11px;
}
"""


def apply_theme(app: QApplication | None = None) -> None:
    """Install the stylesheet and base font on the application."""

    target = app or QApplication.instance()
    if target is None:
        raise RuntimeError("apply_theme requires a QApplication instance.")
    base = QFont(resolved_ui_family())
    base.setPointSizeF(9.75)
    target.setFont(base)
    target.setStyleSheet(QSS)


def repolish(widget) -> None:
    """Re-evaluate QSS property selectors after setProperty()."""

    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()
