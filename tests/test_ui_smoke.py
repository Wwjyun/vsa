from ui import MyApp


def test_main_window_starts_with_cartier_stage_names(qtbot):
    window = MyApp()
    qtbot.addWidget(window)

    assert window.windowTitle() == "VSA"
    assert [button.text() for button in window.buttons[:4]] == [
        "MT",
        "LOSS1",
        "DC2",
        "LOSS2",
    ]

    window.combo.setCurrentText("Product B")
    assert [button.text() for button in window.buttons[:4]] == [
        "MTLED",
        "RDLLED",
        "MTIC",
        "RDLIC",
    ]


def test_roi_image_search_passes_product_to_lookup(qtbot, monkeypatch):
    captured = {}

    def fake_open_image(option, number, code, package_no, stage):
        captured["args"] = (option, number, code, package_no, stage)

    monkeypatch.setattr("ui.open_image_from_search", fake_open_image)
    window = MyApp()
    qtbot.addWidget(window)
    window.input_number.setText("LOT-1")
    window.input_code1.setText("CMP-1")
    window.input_search.setText("42")
    window.current_button_name = "MT"

    window.search_image()

    assert captured["args"] == ("Product A", "LOT-1", "CMP-1", "42", "MT")
