"""Reusable Qt worker for non-GUI functions."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    succeeded = Signal(object)
    failed = Signal(object)
    finished = Signal()


class FunctionWorker(QRunnable):
    """Run one callable on a QThreadPool and report its result to Qt."""

    def __init__(self, function: Callable[[], Any]):
        super().__init__()
        self.function = function
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.function()
        except Exception as error:  # Worker boundary must forward all failures to the UI.
            logger.exception("Background task failed")
            self.signals.failed.emit(error)
        else:
            self.signals.succeeded.emit(result)
        finally:
            self.signals.finished.emit()
