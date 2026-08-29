"""Diagnostics as a styled panel instead of a plain QMessageBox."""

from __future__ import annotations

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from vsa.diagnostics import diagnostic_summary
from vsa.ui.widgets import AppHeader, DataRow, SectionLabel


class DiagnosticsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("window")
        self.setWindowTitle("VSA diagnostics")
        self.setFixedWidth(460)

        self._summary = diagnostic_summary()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = AppHeader("VSA diagnostics", "", self)
        copy_button = QPushButton("Copy", header)
        copy_button.setObjectName("ghost")
        copy_button.clicked.connect(self.copy_summary)
        header.add_trailing(copy_button)
        layout.addWidget(header)

        body = QFrame(self)
        body.setObjectName("queryBar")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 16, 20, 16)
        body_layout.setSpacing(6)
        body_layout.addWidget(SectionLabel("Environment", body))
        for line in self._summary.splitlines():
            key, _, value = line.partition(":")
            body_layout.addWidget(DataRow(key.strip(), value.strip(), parent=body))
        layout.addWidget(body)

        footer = QFrame(self)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 14, 20, 14)
        note = QLabel("No paths, hostnames or identifiers — safe to paste into an issue.", footer)
        note.setObjectName("hint")
        note.setWordWrap(True)
        footer_layout.addWidget(note)
        close_button = QPushButton("Close", footer)
        close_button.clicked.connect(self.accept)
        footer_layout.addWidget(close_button)
        layout.addWidget(footer)

    def copy_summary(self) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._summary)
