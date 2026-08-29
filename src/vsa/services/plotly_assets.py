"""Offline Plotly bundle shared by generated HTML pages.

Plotly embeds its full JavaScript bundle (several MiB) into every exported page
by default. VSA runs offline, so a CDN reference is not an option; instead each
window writes the bundle once into its own temporary directory and the generated
pages reference it relatively.
"""

from __future__ import annotations

from pathlib import Path

from plotly.offline import get_plotlyjs

PLOTLY_BUNDLE_NAME = "plotly.min.js"


def write_plotly_bundle(directory: str | Path) -> Path:
    """Write the offline Plotly bundle into ``directory`` if it is not there yet."""

    target = Path(directory) / PLOTLY_BUNDLE_NAME
    if not target.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(get_plotlyjs(), encoding="utf-8")
    return target
