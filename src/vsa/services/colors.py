"""Deterministic defect-type colors shared by the interactive plots."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable

from plotly.colors import qualitative

PALETTE: tuple[str, ...] = tuple(qualitative.Plotly)


def defect_color(defect_type: object) -> str:
    """Return the palette color for a defect type.

    The color depends only on the defect name, so the same defect keeps the same
    color across lots, stages, and sessions regardless of which other defect
    types happen to be present in the file.
    """

    digest = hashlib.blake2s(str(defect_type).encode("utf-8"), digest_size=8).digest()
    return PALETTE[int.from_bytes(digest, "big") % len(PALETTE)]


def defect_color_map(defect_types: Iterable[object]) -> dict[str, str]:
    """Build a name-to-color mapping for the given defect types."""

    return {str(defect_type): defect_color(defect_type) for defect_type in defect_types}
