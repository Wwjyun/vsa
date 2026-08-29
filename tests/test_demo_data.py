import pandas as pd

from scripts.create_demo_data import COMPONENT_ID, LOT_ID, PRODUCT, create_demo_data
from vsa_paths import STAGE_SEQUENCE


def test_demo_generator_creates_runnable_dataset(tmp_path):
    output = create_demo_data(tmp_path)

    assert output == tmp_path
    for stage in STAGE_SEQUENCE:
        csv_file = output / PRODUCT / "csv" / LOT_ID / stage / f"{COMPONENT_ID}.csv"
        map_file = output / PRODUCT / "map" / LOT_ID / stage / f"{COMPONENT_ID}.png"
        roi_file = output / PRODUCT / "roi" / LOT_ID / stage / COMPONENT_ID / "1.tiff"
        example_file = output / PRODUCT / "example" / stage / "ok.tiff"
        assert csv_file.is_file()
        assert map_file.is_file()
        assert roi_file.is_file()
        assert example_file.is_file()
        assert list(pd.read_csv(csv_file).columns) == ["No", "Row", "Col", "DefectType"]
