import pytest

from vsa_paths import (
    DATA_ROOT_ENV,
    DYNAMIC_STAGES,
    csv_path,
    map_image_path,
    roi_image_path,
    validate_component,
)


def test_paths_use_configured_root_and_canonical_stages(tmp_path, monkeypatch):
    monkeypatch.setenv(DATA_ROOT_ENV, str(tmp_path))

    expected_csv = tmp_path / "Demo" / "csv" / "LOT-1" / "INNER1" / "CMP-1.csv"
    assert csv_path("Demo", "LOT-1", "INNER1", "CMP-1") == expected_csv
    assert DYNAMIC_STAGES == ("MT", "DC2", "INNER1", "RDL", "INNER2", "EMC")


def test_map_image_discovers_supported_extension(tmp_path, monkeypatch):
    monkeypatch.setenv(DATA_ROOT_ENV, str(tmp_path))
    expected = tmp_path / "Demo" / "map" / "LOT-1" / "MT" / "CMP-1.jpg"
    expected.parent.mkdir(parents=True)
    expected.write_bytes(b"sample")

    assert map_image_path("Demo", "LOT-1", "MT", "CMP-1") == expected


@pytest.mark.parametrize(
    "value",
    ["", "..", "../secret", r"folder\secret", "bad:name", "NUL.txt"],
)
def test_path_components_reject_empty_or_traversal_values(value):
    with pytest.raises(ValueError):
        validate_component(value, "Test field")


def test_roi_path_rejects_package_traversal(tmp_path, monkeypatch):
    monkeypatch.setenv(DATA_ROOT_ENV, str(tmp_path))
    with pytest.raises(ValueError):
        roi_image_path("Demo", "LOT-1", "MT", "CMP-1", "../42")


def test_map_image_supports_dotted_component_ids(tmp_path, monkeypatch):
    monkeypatch.setenv(DATA_ROOT_ENV, str(tmp_path))
    expected = tmp_path / "Demo" / "map" / "LOT-1" / "MT" / "CMP.1.png"
    expected.parent.mkdir(parents=True)
    expected.write_bytes(b"sample")

    assert map_image_path("Demo", "LOT-1", "MT", "CMP.1") == expected
