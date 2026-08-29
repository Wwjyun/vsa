import pandas as pd
import pytest

from vsa.services.data import (
    classify_defects,
    merge_loss_frames,
    read_defect_csv,
    validate_columns,
)


def sample_frame():
    return pd.DataFrame(
        {
            "No": [10, 11],
            "Row": [0, 0],
            "Col": [0, 1],
            "DefectType": ["ok", "scratch"],
        }
    )


def test_classify_good_and_bad_defects_without_mutating_input():
    original = sample_frame()

    good = classify_defects(original, ["ok"], "good")
    bad = classify_defects(original, ["scratch"], "bad")

    assert good["ConvertedDefectType"].tolist() == [1, 0]
    assert bad["ConvertedDefectType"].tolist() == [1, 0]
    assert "ConvertedDefectType" not in original.columns


def test_classify_can_flip_columns():
    flipped = classify_defects(sample_frame(), ["ok"], flip=True)
    assert flipped["Col"].tolist() == [1, 0]


def test_merge_loss_frames_exposes_package_number_and_color():
    good = classify_defects(sample_frame(), ["ok"], "good")
    bad_source = sample_frame().assign(No=[20, 21])
    bad = classify_defects(bad_source, ["scratch"], "bad")

    merged = merge_loss_frames(good, bad)

    assert merged["SelectedNo"].tolist() == [20, 21]
    assert merged["Color"].tolist() == ["gray", "gray"]


def test_validate_columns_reports_all_missing_fields():
    with pytest.raises(ValueError, match="Col, DefectType, No, Row"):
        validate_columns(pd.DataFrame({"Other": [1]}))


def test_read_defect_csv_rejects_empty_file(tmp_path):
    source = tmp_path / "empty.csv"
    source.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="CSV file is empty"):
        read_defect_csv(source)


def test_read_defect_csv_rejects_header_only_csv(tmp_path):
    source = tmp_path / "header-only.csv"
    source.write_text("No,Row,Col,DefectType\n", encoding="utf-8")

    with pytest.raises(ValueError, match="no data rows"):
        read_defect_csv(source)


def test_read_defect_csv_rejects_non_numeric_coordinates(tmp_path):
    source = tmp_path / "invalid-coordinate.csv"
    sample_frame().assign(Col=["left", "right"]).to_csv(source, index=False)

    with pytest.raises(ValueError, match="numeric coordinates"):
        read_defect_csv(source)


def test_merge_rejects_duplicate_coordinates():
    duplicate = pd.concat([sample_frame(), sample_frame().assign(No=[12, 13])], ignore_index=True)
    good = classify_defects(duplicate, ["ok"], "good")
    bad = classify_defects(sample_frame(), ["scratch"], "bad")

    with pytest.raises(ValueError, match="duplicate coordinates"):
        merge_loss_frames(good, bad)


def test_merge_join_strategy_controls_stage_only_coordinates():
    good = classify_defects(sample_frame(), ["ok"], "good")
    bad_source = sample_frame().assign(No=[20, 21], Col=[1, 2])
    bad = classify_defects(bad_source, ["scratch"], "bad")

    inner = merge_loss_frames(good, bad, join="inner")
    outer = merge_loss_frames(good, bad, join="outer")

    assert inner[["Row", "Col"]].values.tolist() == [[0, 1]]
    assert outer[["Row", "Col"]].values.tolist() == [[0, 0], [0, 1], [0, 2]]
    assert outer["StagePresence"].astype(str).tolist() == ["left_only", "both", "right_only"]


def test_merge_rejects_unknown_join_strategy():
    frame = classify_defects(sample_frame(), ["ok"], "good")
    with pytest.raises(ValueError, match="join must be"):
        merge_loss_frames(frame, frame, join="cross")
