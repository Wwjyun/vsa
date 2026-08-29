"""Pure image composition helpers used by comparison exports."""

from __future__ import annotations

import math
import warnings
from collections.abc import Sequence
from pathlib import Path

from PIL import Image

DEFAULT_TILE_SIZE = (800, 800)
DEFAULT_MARGIN = 16
MAX_CANVAS_BYTES = 512 * 1024 * 1024


def estimate_canvas_bytes(
    item_count: int,
    *,
    columns: int,
    tile_size: tuple[int, int],
    margin: int,
) -> int:
    rows = max(1, math.ceil(item_count / columns))
    width = tile_size[0] * columns + (columns + 1) * margin
    height = tile_size[1] * rows + (rows + 1) * margin
    return width * height * 3


def compose_image_grid(
    image_paths: Sequence[str | Path | None],
    *,
    columns: int = 7,
    tile_size: tuple[int, int] = DEFAULT_TILE_SIZE,
    margin: int = DEFAULT_MARGIN,
    max_canvas_bytes: int = MAX_CANVAS_BYTES,
) -> Image.Image:
    """Compose an RGB grid while opening only one source image at a time."""

    if columns < 1 or tile_size[0] < 1 or tile_size[1] < 1 or margin < 0:
        raise ValueError("Grid dimensions must be positive and margin cannot be negative.")
    rows = max(1, math.ceil(len(image_paths) / columns))
    width = tile_size[0] * columns + (columns + 1) * margin
    height = tile_size[1] * rows + (rows + 1) * margin
    estimated_bytes = estimate_canvas_bytes(
        len(image_paths), columns=columns, tile_size=tile_size, margin=margin
    )
    if estimated_bytes > max_canvas_bytes:
        raise ValueError(
            f"Requested image grid needs about {estimated_bytes / 1024**2:.0f} MiB; "
            "choose a smaller tile size."
        )

    canvas = Image.new("RGB", (width, height), "white")
    for index, source_path in enumerate(image_paths):
        if source_path is None:
            continue
        source = Path(source_path)
        if not source.is_file():
            continue
        x = (index % columns) * (tile_size[0] + margin) + margin
        y = (index // columns) * (tile_size[1] + margin) + margin
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(source) as image:
                resized = image.convert("RGB").resize(tile_size, Image.Resampling.LANCZOS)
                canvas.paste(resized, (x, y))
                resized.close()
    return canvas


def save_image_grid(
    image_paths: Sequence[str | Path | None],
    output_path: str | Path,
    **grid_options: object,
) -> Path:
    """Compose and save an image grid, returning the output path."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = compose_image_grid(image_paths, **grid_options)
    try:
        canvas.save(output)
    finally:
        canvas.close()
    return output
