"""Application entry point."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from vsa.logging_config import configure_logging
from vsa.ui.theme import apply_theme
from vsa.views.main_window import MainWindow


def main(argv: Sequence[str] | None = None) -> int:
    """Start the VSA Qt application and return its exit code."""

    configure_logging()
    arguments = list(argv) if argv is not None else list(sys.argv)
    smoke_test = "--smoke-test" in arguments
    arguments = [argument for argument in arguments if argument != "--smoke-test"]
    app = QApplication.instance() or QApplication(arguments)
    app.setStyle("Fusion")  # predictable base for the stylesheet across Windows themes
    apply_theme(app)
    window = MainWindow()
    window.show()
    if smoke_test:
        QTimer.singleShot(1000, app.quit)
    return app.exec()
