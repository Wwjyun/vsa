import pandas as pd
import pytest

from data_processing import classify_defects, merge_loss_frames, validate_columns


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
