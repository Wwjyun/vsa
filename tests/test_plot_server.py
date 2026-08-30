import socket

import pandas as pd
from PIL import Image

from vsa.views.roi_plot import RoiPlotWindow


def test_plot_window_stops_server_and_cleans_temp_files(qtbot, tmp_path):
    csv_path = tmp_path / "sample.csv"
    pd.DataFrame({"No": [1], "Row": [2], "Col": [3], "DefectType": ["scratch"]}).to_csv(
        csv_path, index=False
    )
    roi_folder = tmp_path / "roi"
    roi_folder.mkdir()
    Image.new("RGB", (10, 10), "white").save(roi_folder / "1.tiff")
    example_image = tmp_path / "ok.tiff"
    Image.new("RGB", (10, 10), "white").save(example_image)

    window = RoiPlotWindow(
        csv_path,
        roi_folder,
        "STAGE1",
        example_image,
        "LOT-1",
        "CMP-1",
        "Demo",
    )
    qtbot.addWidget(window)
    port = window.http_server.server_port
    temp_directory = window.temp_dir.name
    assert window.dash_thread.is_alive()

    window.close()
    qtbot.waitUntil(lambda: not window.dash_thread.is_alive(), timeout=5000)

    with socket.socket() as probe:
        assert probe.connect_ex(("127.0.0.1", port)) != 0
    assert not __import__("pathlib").Path(temp_directory).exists()
