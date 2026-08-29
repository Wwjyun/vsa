"""Create deterministic synthetic VSA data for demos and tests."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw

from vsa.config import STAGE_SEQUENCE

PRODUCT = "Product A"
LOT_ID = "DEMO-LOT"
COMPONENT_ID = "DEMO-CMP"
GRID_SIZE = 8
DEFECT_TYPES = ("ok", "scratch", "particle", "miss")
COLORS = {
    "ok": "#68c174",
    "scratch": "#e05d5d",
    "particle": "#f4b942",
    "miss": "#7289da",
}


def build_stage_frame(stage_index: int) -> pd.DataFrame:
    records = []
    package_no = 1
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            defect_type = DEFECT_TYPES[(row * 3 + col + stage_index) % len(DEFECT_TYPES)]
            records.append(
                {
                    "No": package_no,
                    "Row": row,
                    "Col": col,
                    "DefectType": defect_type,
                }
            )
            package_no += 1
    return pd.DataFrame.from_records(records)


def render_map(frame: pd.DataFrame, title: str, size: int = 800) -> Image.Image:
    image = Image.new("RGB", (size, size), "#101318")
    draw = ImageDraw.Draw(image)
    margin = 80
    cell = (size - 2 * margin) / GRID_SIZE
    draw.text((margin, 25), title, fill="white")
    for record in frame.itertuples(index=False):
        x = margin + (record.Col + 0.5) * cell
        y = margin + (record.Row + 0.5) * cell
        radius = max(4, int(cell * 0.16))
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=COLORS[record.DefectType],
        )
    return image


def render_roi(package_no: int, defect_type: str, stage: str) -> Image.Image:
    image = Image.new("RGB", (128, 128), COLORS[defect_type])
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, 119, 119), outline="white", width=2)
    draw.text((14, 48), f"{stage}\nNo {package_no}", fill="white")
    return image


def create_demo_data(output_root: str | Path) -> Path:
    root = Path(output_root).expanduser().resolve()
    product_root = root / PRODUCT

    for stage_index, stage in enumerate(STAGE_SEQUENCE):
        frame = build_stage_frame(stage_index)
        csv_file = product_root / "csv" / LOT_ID / stage / f"{COMPONENT_ID}.csv"
        csv_file.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(csv_file, index=False)

        stage_map = render_map(frame, f"{stage} defect map")
        map_folder = product_root / "map" / LOT_ID / stage
        map_folder.mkdir(parents=True, exist_ok=True)
        stage_map.save(map_folder / f"{COMPONENT_ID}.png")
        for index in range(1, 11):
            stage_map.save(map_folder / f"{LOT_ID}{index:03}.png")

        roi_folder = product_root / "roi" / LOT_ID / stage / COMPONENT_ID
        roi_folder.mkdir(parents=True, exist_ok=True)
        for record in frame.itertuples(index=False):
            render_roi(record.No, record.DefectType, stage).save(roi_folder / f"{record.No}.tiff")

        example_folder = product_root / "example" / stage
        example_folder.mkdir(parents=True, exist_ok=True)
        render_roi(0, "ok", stage).save(example_folder / "ok.tiff")

        bar_folder = product_root / "bar" / LOT_ID / stage
        bar_folder.mkdir(parents=True, exist_ok=True)
        stage_map.resize((400, 400)).save(bar_folder / f"{stage}.png")

        original_folder = product_root / "org" / LOT_ID / stage / COMPONENT_ID
        original_folder.mkdir(parents=True, exist_ok=True)
        stage_map.save(original_folder / f"{COMPONENT_ID}_original.tiff")

    return root


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("demo_data"),
        help="Destination data root (default: ./demo_data)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    output = create_demo_data(args.output)
    print(f"Demo data created at: {output}")
    print(f"Product: {PRODUCT}")
    print(f"Lot ID: {LOT_ID}")
    print(f"Component ID: {COMPONENT_ID}")


if __name__ == "__main__":
    main()
