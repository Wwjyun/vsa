import pandas as pd

from vsa.services.colors import PALETTE, defect_color, defect_color_map
from vsa.services.plotly_assets import PLOTLY_BUNDLE_NAME, write_plotly_bundle
from vsa.views.custom_map_plot import generate_map
from vsa.views.loss_map_plot import build_loss_figure, write_loss_page


def test_defect_color_is_stable_regardless_of_neighbouring_defect_types():
    first = defect_color_map(["scratch", "crack", "void"])
    second = defect_color_map(["void", "scratch"])

    assert first["scratch"] == second["scratch"]
    assert first["void"] == second["void"]
    assert defect_color("scratch") in PALETTE


def test_plotly_bundle_is_written_once_per_directory(tmp_path):
    first = write_plotly_bundle(tmp_path)
    first.write_text("cached", encoding="utf-8")
    second = write_plotly_bundle(tmp_path)

    assert first == second == tmp_path / PLOTLY_BUNDLE_NAME
    assert second.read_text(encoding="utf-8") == "cached"


def test_loss_page_references_the_shared_bundle_instead_of_inlining_plotly(tmp_path):
    merged = pd.DataFrame({"Col": [1], "Row": [2], "SelectedNo": ["42"], "Color": ["red"]})

    page_path = write_loss_page(build_loss_figure(merged, "LOSS1"), tmp_path)
    page_html = page_path.read_text(encoding="utf-8")
    bundle = tmp_path / PLOTLY_BUNDLE_NAME

    assert bundle.is_file()
    assert PLOTLY_BUNDLE_NAME in page_html
    assert page_path.stat().st_size < bundle.stat().st_size


def test_custom_map_page_references_the_shared_bundle(tmp_path):
    frame = pd.DataFrame({"No": [1], "Row": [2], "Col": [3], "DefectType": ["scratch"]})

    output = generate_map(frame, tmp_path / "custom-map.html")

    assert (tmp_path / PLOTLY_BUNDLE_NAME).is_file()
    assert PLOTLY_BUNDLE_NAME in output.read_text(encoding="utf-8")


def test_figure_builders_reject_out_of_range_sizes(tmp_path):
    merged = pd.DataFrame({"Col": [1], "Row": [2], "SelectedNo": ["42"], "Color": ["red"]})
    frame = pd.DataFrame({"No": [1], "Row": [2], "Col": [3], "DefectType": ["scratch"]})

    for kwargs in ({"point_size": 0}, {"width": 10}, {"height": 10}):
        try:
            build_loss_figure(merged, "LOSS1", **kwargs)
        except ValueError:
            continue
        raise AssertionError(f"build_loss_figure accepted {kwargs}")

    try:
        generate_map(frame, tmp_path / "too-small.html", map_size=(10, 10))
    except ValueError:
        return
    raise AssertionError("generate_map accepted an undersized map")
