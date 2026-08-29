import os
import subprocess
import sys

from vsa_paths import roi_image_path


def open_image_from_search(option, number, code, no, button_name):
    file_path = roi_image_path(option, number, button_name, code, no)
    if not file_path.is_file():
        raise FileNotFoundError(f"ROI image not found: {file_path}")

    if os.name == "nt":
        os.startfile(file_path)
    elif sys.platform == "darwin":
        subprocess.run(("open", str(file_path)), check=True)
    elif os.name == "posix":
        subprocess.run(("xdg-open", str(file_path)), check=True)
    else:
        raise OSError(f"Unsupported operating system: {os.name}")
    return file_path
