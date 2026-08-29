"""Small operating-system integration helpers."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def open_local_file(file_path: str | Path) -> Path:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    if os.name == "nt":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.run(("open", str(path)), check=True)
    elif os.name == "posix":
        subprocess.run(("xdg-open", str(path)), check=True)
    else:
        raise OSError(f"Unsupported operating system: {os.name}")
    return path
