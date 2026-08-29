"""Qt adapters for image-comparison and yield exports."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFileDialog, QMessageBox

from vsa.config import STAGE_SEQUENCE
from vsa.paths import bar_image_path, map_folder, map_image_path
from vsa.services.images import save_image_grid

logger = logging.getLogger(__name__)


def _show_export(main_window, image_path: Path) -> None:
    pixmap = QPixmap(str(image_path))
    if pixmap.isNull():
        raise OSError(f"Unable to preview exported image: {image_path}")
    main_window.preview_label.setPixmap(
        pixmap.scaled(
            main_window.preview_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
    )
    main_window.preview_label.adjustSize()
    QMessageBox.information(main_window, "Success", f"Image saved to {image_path}")


def _choose_output(main_window, filename: str) -> Path | None:
    folder = QFileDialog.getExistingDirectory(main_window, "Select Save Folder")
    return Path(folder) / filename if folder else None


def export_vertical_comparison(main_window) -> None:
    try:
        selection = main_window.selected_values()
        paths = [
            map_image_path(selection.product, selection.lot_id, stage, selection.component_id)
            for stage in STAGE_SEQUENCE
        ]
        output = _choose_output(main_window, "stage-comparison.tiff")
        if output is None:
            return
        main_window.run_background_task(
            lambda: save_image_grid(paths, output, columns=7),
            on_success=lambda path: _show_export(main_window, path),
            error_title="Comparison error",
        )
    except (OSError, ValueError) as error:
        logger.exception("Vertical comparison failed")
        QMessageBox.warning(main_window, "Comparison error", str(error))


def export_vertical_yield(main_window) -> None:
    try:
        selection = main_window.selected_values()
        paths = [
            bar_image_path(selection.product, selection.lot_id, stage) for stage in STAGE_SEQUENCE
        ]
        output = _choose_output(main_window, "yield-comparison.tiff")
        if output is None:
            return
        main_window.run_background_task(
            lambda: save_image_grid(paths, output, columns=7),
            on_success=lambda path: _show_export(main_window, path),
            error_title="Yield error",
        )
    except (OSError, ValueError) as error:
        logger.exception("Yield comparison failed")
        QMessageBox.warning(main_window, "Yield error", str(error))


def export_horizontal_comparison(main_window) -> None:
    try:
        selection = main_window.selected_values()
        folder = map_folder(selection.product, selection.lot_id, selection.stage)
        if not folder.is_dir():
            raise FileNotFoundError(f"Map folder not found: {folder}")
        paths = sorted(
            path
            for path in folder.iterdir()
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
        )[:10]
        if not paths:
            raise FileNotFoundError(f"No map images found in: {folder}")
        output = _choose_output(main_window, "lot-comparison.png")
        if output is None:
            return
        main_window.run_background_task(
            lambda: save_image_grid(paths, output, columns=5),
            on_success=lambda path: _show_export(main_window, path),
            error_title="Comparison error",
        )
    except (OSError, ValueError) as error:
        logger.exception("Horizontal comparison failed")
        QMessageBox.warning(main_window, "Comparison error", str(error))
