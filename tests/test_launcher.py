import subprocess
import sys
from pathlib import Path

LAUNCHER = Path(__file__).resolve().parents[1] / "main.py"


def test_root_launcher_starts_the_application(tmp_path):
    """`python main.py` must keep working as a launch entry point."""

    environment = {
        "PATH": __import__("os").environ.get("PATH", ""),
        "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", ""),
        "QT_QPA_PLATFORM": "offscreen",
        "QTWEBENGINE_DISABLE_SANDBOX": "1",
        "QTWEBENGINE_CHROMIUM_FLAGS": "--disable-gpu --disable-software-rasterizer",
        "VSA_DATA_ROOT": str(tmp_path),
    }
    result = subprocess.run(
        [sys.executable, str(LAUNCHER), "--smoke-test"],
        capture_output=True,
        text=True,
        timeout=120,
        env=environment,
    )

    assert result.returncode == 0, result.stderr
