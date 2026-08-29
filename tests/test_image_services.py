import pytest
from PIL import Image

from vsa.services.images import compose_image_grid, estimate_canvas_bytes


def test_compose_image_grid_supports_missing_stages_and_closes_sources(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (8, 8), "red").save(source)

    canvas = compose_image_grid([source, None], columns=2, tile_size=(10, 10), margin=1)
    try:
        assert canvas.size == (23, 12)
        assert canvas.getpixel((1, 1)) == (255, 0, 0)
        assert canvas.getpixel((12, 1)) == (255, 255, 255)
    finally:
        canvas.close()

    source.unlink()


def test_compose_image_grid_rejects_excessive_canvas():
    estimated = estimate_canvas_bytes(14, columns=7, tile_size=(800, 800), margin=16)
    with pytest.raises(ValueError, match="choose a smaller tile size"):
        compose_image_grid([None] * 14, max_canvas_bytes=estimated - 1)
