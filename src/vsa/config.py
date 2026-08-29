"""Application configuration and validated package resources."""

from __future__ import annotations

import json
import os
from importlib.resources import files
from pathlib import Path

DATA_ROOT_ENV = "VSA_DATA_ROOT"
DEFAULT_DATA_ROOT = Path("D:/Database-PC")

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


class ConfigurationError(ValueError):
    """Raised when a packaged configuration resource is invalid."""


def get_data_root() -> Path:
    """Return the configured data root without requiring it to exist."""

    configured = os.environ.get(DATA_ROOT_ENV)
    return Path(configured).expanduser() if configured else DEFAULT_DATA_ROOT


def _load_resource_json(name: str) -> object:
    resource = files("vsa.resources").joinpath(name)
    try:
        return json.loads(resource.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConfigurationError(f"Unable to load {name}: {error}") from error


def load_product_stages() -> dict[str, tuple[str, ...]]:
    """Load and validate the product-to-stage button mapping."""

    data = _load_resource_json("button_names.json")
    if not isinstance(data, dict) or not data:
        raise ConfigurationError("button_names.json must contain a non-empty object.")

    result: dict[str, tuple[str, ...]] = {}
    for product, stages in data.items():
        if not isinstance(product, str) or not product.strip():
            raise ConfigurationError("Every product name must be a non-empty string.")
        if not isinstance(stages, list) or not stages:
            raise ConfigurationError(f"Product {product!r} must define at least one stage.")
        if any(not isinstance(stage, str) or not stage.strip() for stage in stages):
            raise ConfigurationError(f"Product {product!r} contains an invalid stage name.")
        result[product] = tuple(stages)
    return result


def load_classification_rules() -> dict[str, tuple[str, ...]]:
    """Load and validate good/bad defect classification rules."""

    data = _load_resource_json("rule.json")
    if not isinstance(data, dict):
        raise ConfigurationError("rule.json must contain an object.")

    result: dict[str, tuple[str, ...]] = {}
    for key in ("good", "bad"):
        values = data.get(key)
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise ConfigurationError(f"rule.json field {key!r} must be a list of strings.")
        result[key] = tuple(values)
    return result
