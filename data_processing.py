"""Pure dataframe operations shared by VSA visualizations and tests."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

DEFECT_COLUMNS = {"No", "Row", "Col", "DefectType"}
CONVERTED_COLUMNS = DEFECT_COLUMNS | {"ConvertedDefectType"}


def validate_columns(frame: pd.DataFrame, required: set[str] = DEFECT_COLUMNS) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")


def classify_defects(
    frame: pd.DataFrame,
    selected_defects: Iterable[object],
    selection_type: str = "good",
    *,
    flip: bool = False,
) -> pd.DataFrame:
    """Return a classified copy of a defect dataframe."""

    validate_columns(frame)
    if selection_type not in {"good", "bad"}:
        raise ValueError("selection_type must be 'good' or 'bad'.")

    result = frame.copy()
    selected = set(selected_defects)
    selected_mask = result["DefectType"].isin(selected)
    result["ConvertedDefectType"] = (
        selected_mask.astype("int8")
        if selection_type == "good"
        else (~selected_mask).astype("int8")
    )

    if flip:
        numeric_col = pd.to_numeric(result["Col"], errors="raise")
        result["Col"] = numeric_col.max() - numeric_col
    return result


def merge_loss_frames(good_frame: pd.DataFrame, bad_frame: pd.DataFrame) -> pd.DataFrame:
    """Merge two classified stages and derive loss-map colors and point IDs."""

    validate_columns(good_frame, CONVERTED_COLUMNS)
    validate_columns(bad_frame, CONVERTED_COLUMNS)
    merged = pd.merge(
        good_frame,
        bad_frame,
        on=["Row", "Col"],
        suffixes=("_good", "_bad"),
    )
    merged["Difference"] = merged["ConvertedDefectType_good"] - merged["ConvertedDefectType_bad"]
    merged["Color"] = merged["Difference"].eq(1).map({True: "red", False: "gray"})
    merged["SelectedNo"] = merged["No_bad"].where(merged["No_bad"].notna(), merged["No_good"])
    return merged
