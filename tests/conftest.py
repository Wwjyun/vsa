import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-gpu --disable-software-rasterizer",
)

import pytest  # noqa: E402  (Qt environment must be configured before Qt is imported)
from PySide6.QtCore import QEvent  # noqa: E402


@pytest.fixture(autouse=True)
def release_qt_widgets(qapp):
    """Destroy every widget while the application is still alive.

    QtWebEngine spawns Chromium child processes per page. If a page outlives the
    test session, teardown happens during interpreter shutdown and the process
    can exit non-zero even though every test passed.
    """

    yield
    for widget in qapp.topLevelWidgets():
        widget.close()
    qapp.sendPostedEvents(None, QEvent.DeferredDelete)
    qapp.processEvents()
