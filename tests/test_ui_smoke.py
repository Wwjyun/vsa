from pathlib import Path

from vsa.views.main_window import MainWindow


def test_main_window_lists_the_stages_of_the_selected_product(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == "VSA"
    assert [button.text() for button in window.buttons[:4]] == [
        "STAGE1",
        "LOSS1",
        "STAGE2",
        "LOSS2",
    ]

    window.combo.setCurrentText("Product B")
    assert [button.text() for button in window.buttons[:4]] == [
        "STAGE1",
        "STAGE2",
        "STAGE3",
        "STAGE4",
    ]


def test_roi_image_search_passes_product_to_lookup(qtbot, monkeypatch):
    captured = {}

    def fake_roi_path(option, number, stage, code, package_no):
        captured["args"] = (option, number, code, package_no, stage)
        return Path("synthetic.tiff")

    monkeypatch.setattr("vsa.views.main_window.roi_image_path", fake_roi_path)
    monkeypatch.setattr("vsa.views.main_window.open_local_file", lambda path: path)
    window = MainWindow()
    qtbot.addWidget(window)
    window.input_number.setText("LOT-1")
    window.input_code1.setText("CMP-1")
    window.input_search.setText("42")
    window.current_button_name = "STAGE1"

    window.search_image()

    assert captured["args"] == ("Product A", "LOT-1", "CMP-1", "42", "STAGE1")


def test_plot_options_use_defaults_until_the_operator_overrides_them(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.plot_options() == {
        "plot_width": 1000,
        "plot_height": 800,
        "point_size": 2,
    }

    window.input_plot_width.setText("1200")
    window.input_point_size.setText("5")

    assert window.plot_options() == {
        "plot_width": 1200,
        "plot_height": 800,
        "point_size": 5,
    }


def test_plot_options_reach_the_loss_map_and_custom_map_windows(qtbot, monkeypatch):
    captured = {}

    class FakeSignal:
        def connect(self, slot):
            pass

    class FakeController:
        """Mirrors the parts of LossMapPlotController the window touches."""

        def __init__(self, main_ui, web_view, **kwargs):
            captured["loss"] = kwargs
            self.point_selected = FakeSignal()

        def close(self):
            pass

    class FakeCustomWindow:
        def __init__(self, selection, map_size):
            captured["custom"] = map_size

        def show(self):
            pass

    monkeypatch.setattr("vsa.views.loss_map_window.LossMapPlotController", FakeController)
    monkeypatch.setattr("vsa.views.main_window.CustomizeMapWindow", FakeCustomWindow)

    window = MainWindow()
    qtbot.addWidget(window)
    window.input_number.setText("LOT-1")
    window.input_code1.setText("CMP-1")
    window.current_button_name = "LOSS1"
    window.input_plot_width.setText("1200")
    window.input_plot_height.setText("900")
    window.input_point_size.setText("4")

    window.open_loss_custom_ui()
    window.open_customize_map_ui()

    assert captured["loss"] == {"plot_width": 1200, "plot_height": 900, "point_size": 4}
    assert captured["custom"] == (1200, 900)
