import pandas as pd
from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView

from lossmap_plot import build_loss_figure, build_loss_html


class Receiver(QObject):
    point_received = Signal(str)

    @Slot(str)
    def receivePoint(self, value):
        self.point_received.emit(value)


def test_loss_map_html_contains_webchannel_double_click_bridge():
    merged = pd.DataFrame(
        {
            "Col": [1],
            "Row": [2],
            "SelectedNo": ["42"],
            "Color": ["red"],
        }
    )

    figure = build_loss_figure(merged, "LOSS1")
    page_html = build_loss_html(figure)

    assert list(figure.data[0].customdata) == ["42"]
    assert "qrc:///qtwebchannel/qwebchannel.js" in page_html
    assert "plotly_click" in page_html
    assert "handler.receivePoint(number)" in page_html


def test_loss_map_double_click_reaches_qt_webchannel(qtbot, tmp_path):
    merged = pd.DataFrame({"Col": [1], "Row": [2], "SelectedNo": ["42"], "Color": ["red"]})
    page_path = tmp_path / "loss-map.html"
    page_path.write_text(
        build_loss_html(build_loss_figure(merged, "LOSS1")),
        encoding="utf-8",
    )

    view = QWebEngineView()
    qtbot.addWidget(view)
    channel = QWebChannel(view.page())
    receiver = Receiver()
    channel.registerObject("handler", receiver)
    view.page().setWebChannel(channel)

    with qtbot.waitSignal(view.loadFinished, timeout=15000) as loaded:
        view.setUrl(QUrl.fromLocalFile(str(page_path)))
    assert loaded.args == [True]

    javascript = """
        const plot = document.getElementsByClassName('plotly-graph-div')[0];
        const eventData = {points: [{customdata: '42'}]};
        plot.emit('plotly_click', eventData);
        plot.emit('plotly_click', eventData);
    """
    with qtbot.waitSignal(receiver.point_received, timeout=5000) as received:
        view.page().runJavaScript(javascript)
    assert received.args == ["42"]
