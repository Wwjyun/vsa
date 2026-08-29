"""Non-sensitive runtime diagnostics suitable for issue reports."""

from __future__ import annotations

import platform
import sys
from importlib.metadata import PackageNotFoundError, version

from vsa import __version__

DEPENDENCIES = ("PySide6", "pandas", "plotly", "dash", "Pillow")


def diagnostic_summary() -> str:
    lines = [
        f"VSA: {__version__}",
        f"Python: {platform.python_version()}",
        f"Platform: {platform.system()} {platform.release()}",
        f"Executable mode: {'frozen' if getattr(sys, 'frozen', False) else 'source'}",
    ]
    for dependency in DEPENDENCIES:
        try:
            dependency_version = version(dependency)
        except PackageNotFoundError:
            dependency_version = "not installed"
        lines.append(f"{dependency}: {dependency_version}")
    return "\n".join(lines)
