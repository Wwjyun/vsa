"""Centralized, validated paths for VSA production data."""

from __future__ import annotations

import os
from pathlib import Path

DATA_ROOT_ENV = "VSA_DATA_ROOT"
DEFAULT_DATA_ROOT = Path("D:/Database-PC")
PROJECT_ROOT = Path(__file__).resolve().parent
BUTTON_NAMES_PATH = PROJECT_ROOT / "button_names.json"

STAGE_SEQUENCE = (
    "MT",
    "LOSS1",
    "DC2",
    "LOSS2",
    "INNER1",
    "LOSS3",
    "RDL",
    "LOSS4",
    "INNER2",
    "LOSS5",
    "CU",
    "LOSS6",
    "EMC",
    "FPY",
)

DYNAMIC_STAGES = ("MT", "DC2", "INNER1", "RDL", "INNER2", "EMC")

LOSS_STAGE_PAIRS = {
    "LOSS1": ("MT", "DC2"),
    "LOSS2": ("DC2", "INNER1"),
    "LOSS3": ("INNER1", "RDL"),
    "LOSS4": ("RDL", "INNER2"),
    "LOSS5": ("INNER2", "CU"),
    "LOSS6": ("CU", "EMC"),
}

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tiff", ".tif")
WINDOWS_RESERVED_CHARACTERS = frozenset('<>:"|?*')
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


def get_data_root() -> Path:
    """Return the configured data root without requiring it to exist."""

    configured = os.environ.get(DATA_ROOT_ENV)
    return Path(configured).expanduser() if configured else DEFAULT_DATA_ROOT


def validate_component(value: str, label: str) -> str:
    """Validate a single user-controlled path component."""

    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{label} is required.")
    if normalized in {".", ".."} or "/" in normalized or "\\" in normalized:
        raise ValueError(f"{label} contains an invalid path separator.")
    if any(ord(character) < 32 for character in normalized):
        raise ValueError(f"{label} contains an invalid control character.")
    if any(character in WINDOWS_RESERVED_CHARACTERS for character in normalized):
        raise ValueError(f"{label} contains a Windows-reserved character.")
    if normalized.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
        raise ValueError(f"{label} uses a Windows-reserved name.")
    return normalized


def data_path(
    product: str,
    category: str,
    lot_id: str,
    stage: str,
    *parts: str,
    root: Path | None = None,
) -> Path:
    """Build a path guaranteed to remain below the selected data root."""

    base = (root or get_data_root()).expanduser().resolve(strict=False)
    components = (
        validate_component(product, "Product"),
        validate_component(category, "Category"),
        validate_component(lot_id, "Lot ID"),
        validate_component(stage, "Stage"),
        *(validate_component(part, "Path component") for part in parts),
    )
    candidate = base.joinpath(*components).resolve(strict=False)
    if candidate != base and base not in candidate.parents:
        raise ValueError("Resolved path escapes the configured data root.")
    return candidate


def csv_path(product: str, lot_id: str, stage: str, component_id: str) -> Path:
    return data_path(
        product, "csv", lot_id, stage, f"{validate_component(component_id, 'Component ID')}.csv"
    )


def map_folder(product: str, lot_id: str, stage: str) -> Path:
    return data_path(product, "map", lot_id, stage)


def map_image_path(product: str, lot_id: str, stage: str, component_id: str) -> Path:
    folder = map_folder(product, lot_id, stage)
    component = validate_component(component_id, "Component ID")
    direct = folder / component
    if direct.is_file():
        return direct
    if direct.suffix.lower() in IMAGE_EXTENSIONS:
        return direct
    for extension in IMAGE_EXTENSIONS:
        candidate = folder / f"{component}{extension}"
        if candidate.is_file():
            return candidate
    return folder / f"{component}.png"


def roi_folder(product: str, lot_id: str, stage: str, component_id: str) -> Path:
    return data_path(
        product, "roi", lot_id, stage, validate_component(component_id, "Component ID")
    )


def roi_image_path(
    product: str,
    lot_id: str,
    stage: str,
    component_id: str,
    package_no: str,
) -> Path:
    package = validate_component(package_no, "PKG NO")
    return roi_folder(product, lot_id, stage, component_id) / f"{package}.tiff"


def original_folder(product: str, lot_id: str, stage: str, component_id: str) -> Path:
    return data_path(
        product, "org", lot_id, stage, validate_component(component_id, "Component ID")
    )


def example_image_path(product: str, stage: str) -> Path:
    product_name = validate_component(product, "Product")
    stage_name = validate_component(stage, "Stage")
    base = get_data_root().expanduser().resolve(strict=False)
    return base / product_name / "example" / stage_name / "ok.tiff"


def bar_image_path(product: str, lot_id: str, stage: str) -> Path:
    return data_path(product, "bar", lot_id, stage, f"{validate_component(stage, 'Stage')}.png")
