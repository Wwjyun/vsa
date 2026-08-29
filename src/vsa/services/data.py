"""Validated CSV loading, classification, conversion, and loss-map operations."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

import pandas as pd

from vsa.config import load_classification_rules as load_packaged_rules

logger = logging.getLogger(__name__)

DEFECT_COLUMNS = {"No", "Row", "Col", "DefectType"}
CONVERTED_COLUMNS = DEFECT_COLUMNS | {"ConvertedDefectType"}
CONVERSION_COLUMNS = {"Row", "Col", "ConvertedDefectType"}
JoinStrategy = Literal["inner", "outer", "left", "right"]


def validate_columns(frame: pd.DataFrame, required: set[str] = DEFECT_COLUMNS) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")


def validate_defect_frame(
    frame: pd.DataFrame,
    *,
    required: set[str] = DEFECT_COLUMNS,
    allow_empty: bool = False,
) -> pd.DataFrame:
    """Return a copy with numeric coordinates after validating the input schema."""

    validate_columns(frame, required)
    if frame.empty and not allow_empty:
        raise ValueError("CSV contains no data rows.")

    result = frame.copy()
    for column in ("Row", "Col"):
        try:
            result[column] = pd.to_numeric(result[column], errors="raise")
        except (TypeError, ValueError) as error:
            raise ValueError(f"CSV column {column!r} must contain numeric coordinates.") from error
        if result[column].isna().any():
            raise ValueError(f"CSV column {column!r} contains missing coordinates.")
    if "No" in required and result["No"].isna().any():
        raise ValueError("CSV column 'No' contains missing package identifiers.")
    return result


def read_defect_csv(
    file_path: str | Path,
    *,
    require_converted: bool = False,
) -> pd.DataFrame:
    """Read a UTF-8 CSV and return a validated defect dataframe."""

    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")
    try:
        frame = pd.read_csv(path, encoding="utf-8")
    except pd.errors.EmptyDataError as error:
        raise ValueError(f"CSV file is empty: {path.name}") from error
    except (pd.errors.ParserError, UnicodeError) as error:
        raise ValueError(f"CSV file cannot be parsed as UTF-8: {path.name}") from error
    required = CONVERTED_COLUMNS if require_converted else DEFECT_COLUMNS
    return validate_defect_frame(frame, required=required)


def read_converted_csv(file_path: str | Path) -> pd.DataFrame:
    """Read a converted CSV used by the legacy change-ratio workflow."""

    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Converted CSV file not found: {path}")
    try:
        frame = pd.read_csv(path, encoding="utf-8")
    except pd.errors.EmptyDataError as error:
        raise ValueError(f"Converted CSV file is empty: {path.name}") from error
    except (pd.errors.ParserError, UnicodeError) as error:
        raise ValueError(f"Converted CSV cannot be parsed as UTF-8: {path.name}") from error
    return validate_defect_frame(frame, required=CONVERSION_COLUMNS)


def classify_defects(
    frame: pd.DataFrame,
    selected_defects: Iterable[object],
    selection_type: str = "good",
    *,
    flip: bool = False,
) -> pd.DataFrame:
    """Return a classified copy of a defect dataframe."""

    result = validate_defect_frame(frame)
    if selection_type not in {"good", "bad"}:
        raise ValueError("selection_type must be 'good' or 'bad'.")

    selected_mask = result["DefectType"].isin(set(selected_defects))
    result["ConvertedDefectType"] = (
        selected_mask.astype("int8")
        if selection_type == "good"
        else (~selected_mask).astype("int8")
    )
    if flip:
        result["Col"] = result["Col"].max() - result["Col"]
    return result


def _reject_duplicate_coordinates(frame: pd.DataFrame, label: str) -> None:
    duplicate_mask = frame.duplicated(["Row", "Col"], keep=False)
    if duplicate_mask.any():
        duplicate_count = int(duplicate_mask.sum())
        raise ValueError(
            f"{label} stage contains {duplicate_count} rows with duplicate coordinates."
        )


def merge_loss_frames(
    good_frame: pd.DataFrame,
    bad_frame: pd.DataFrame,
    *,
    join: JoinStrategy = "inner",
) -> pd.DataFrame:
    """Merge classified stages using an explicit coordinate join strategy.

    Duplicate coordinates are rejected because a many-to-many merge would create
    artificial defect points. Outer/left/right joins retain stage-only coordinates
    and expose their origin in the ``StagePresence`` column.
    """

    if join not in {"inner", "outer", "left", "right"}:
        raise ValueError("join must be one of: inner, outer, left, right.")
    good = validate_defect_frame(good_frame, required=CONVERTED_COLUMNS)
    bad = validate_defect_frame(bad_frame, required=CONVERTED_COLUMNS)
    _reject_duplicate_coordinates(good, "First")
    _reject_duplicate_coordinates(bad, "Second")

    merged = pd.merge(
        good,
        bad,
        on=["Row", "Col"],
        how=join,
        suffixes=("_good", "_bad"),
        indicator="StagePresence",
        validate="one_to_one",
    )
    merged["Difference"] = merged["ConvertedDefectType_good"] - merged["ConvertedDefectType_bad"]
    merged["Color"] = merged["Difference"].eq(1).map({True: "red", False: "gray"})
    merged["SelectedNo"] = merged["No_bad"].where(merged["No_bad"].notna(), merged["No_good"])
    return merged


def load_classification_rules(rules_file: str | Path | None = None) -> dict[str, tuple[str, ...]]:
    """Load validated rules from a custom file or the packaged default."""

    if rules_file is None:
        return load_packaged_rules()
    path = Path(rules_file)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Unable to load classification rules: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("Classification rules must contain an object.")
    result: dict[str, tuple[str, ...]] = {}
    for key in ("good", "bad"):
        values = data.get(key, [])
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise ValueError(f"Classification rule {key!r} must be a list of strings.")
        result[key] = tuple(values)
    return result


def convert_defect_type(frame: pd.DataFrame, good_defects: Iterable[object]) -> pd.Series:
    validated = validate_defect_frame(frame)
    return validated["DefectType"].isin(set(good_defects)).astype("int8")


def convert_csv_files(
    input_folder: str | Path,
    rules_file: str | Path | None = None,
    user_selected_good: Iterable[object] | None = None,
) -> list[Path]:
    """Convert source CSVs in a folder and return the written output paths."""

    folder = Path(input_folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"CSV folder not found: {folder}")
    rules = load_classification_rules(rules_file)
    good_defects = tuple(user_selected_good) if user_selected_good is not None else rules["good"]
    outputs: list[Path] = []
    for input_file in sorted(folder.glob("*.csv")):
        if input_file.name.startswith("convert_"):
            continue
        defect_data = read_defect_csv(input_file)
        defect_data["ConvertedDefectType"] = convert_defect_type(defect_data, good_defects)
        output_file = folder / f"convert_{input_file.name}"
        defect_data[["No", "Col", "Row", "ConvertedDefectType"]].to_csv(
            output_file, index=False, encoding="utf-8"
        )
        outputs.append(output_file)
        logger.info("Converted CSV %s", input_file.name)
    return outputs


def calculate_change(first_folder: str | Path, second_folder: str | Path) -> dict[str, float]:
    """Calculate good-to-bad ratios for matching converted CSV files."""

    first = Path(first_folder)
    second = Path(second_folder)
    if not first.is_dir() or not second.is_dir():
        raise FileNotFoundError("Both converted CSV folders must exist.")
    changes: dict[str, float] = {}
    for first_file in sorted(first.glob("convert_*.csv")):
        second_file = second / first_file.name
        if not second_file.is_file():
            continue
        first_frame = read_converted_csv(first_file)
        second_frame = read_converted_csv(second_file)
        _reject_duplicate_coordinates(first_frame, "First")
        _reject_duplicate_coordinates(second_frame, "Second")
        merged = pd.merge(
            first_frame,
            second_frame,
            on=["Row", "Col"],
            suffixes=("_good", "_bad"),
            validate="one_to_one",
        )
        changed = merged["ConvertedDefectType_good"].eq(1) & merged["ConvertedDefectType_bad"].eq(0)
        name = first_file.name.removeprefix("convert_")
        changes[name] = float(changed.mean()) if not merged.empty else 0.0
    return changes


def save_changes(changes: dict[str, float], save_path: str | Path) -> Path:
    path = Path(save_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(f"{name}: {ratio:.2%}\n" for name, ratio in sorted(changes.items())),
        encoding="utf-8",
    )
    return path
