"""Testable file export operations used by the Qt UI."""

from __future__ import annotations

import shutil
from pathlib import Path


def copy_file(source_file: str | Path, target_file: str | Path) -> Path:
    source = Path(source_file)
    target = Path(target_file)
    if not source.is_file():
        raise FileNotFoundError(f"Source file not found: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def copy_folder_contents(source_folder: str | Path, target_folder: str | Path) -> Path:
    source = Path(source_folder)
    target = Path(target_folder)
    if not source.is_dir():
        raise FileNotFoundError(f"Source folder not found: {source}")
    target.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        destination = target / item.name
        if item.is_dir():
            shutil.copytree(item, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(item, destination)
    return target
