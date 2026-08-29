"""Repository-root launcher.

The application lives in ``src/vsa`` and is normally started with ``python -m vsa``.
This file keeps ``python main.py`` working from a shortcut or a checkout where the
package has not been installed.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from vsa.app import main  # noqa: E402  (the path above must be set before importing)

if __name__ == "__main__":
    raise SystemExit(main())
