from pathlib import Path

from PIL import Image
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox

from vsa_paths import map_folder


def compare_horizontal(main_ui):
    number = main_ui.input_number.text().strip()
    current_button_name = main_ui.current_button_name
    option = main_ui.combo.currentText()
    folder_path = map_folder(option, number, current_button_name)

    if not folder_path.is_dir():
        QMessageBox.critical(main_ui, "Error", f"Folder not found: {folder_path}")
        return

    target_width, target_height = 2160, 2160
    expected_files = [f"{number}{index:03}.png" for index in range(1, 11)]
    found_images = {
        image.name: image
        for image in folder_path.iterdir()
        if image.suffix.lower() in {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
    }

    cols = 5
    rows = (len(expected_files) + cols - 1) // cols
    margin = 20
    combined_width = target_width * cols + (cols + 1) * margin
    combined_height = target_height * rows + (rows + 1) * margin
    combined_image = Image.new("RGB", (combined_width, combined_height), "white")

    for index, expected_name in enumerate(expected_files):
        actual_name = expected_name.replace("000", "00", 1)
        source_path = found_images.get(actual_name)
        if source_path is None:
            continue
        try:
            with Image.open(source_path) as source_image:
                resized = source_image.convert("RGB").resize(
                    (target_width, target_height),
                    Image.Resampling.LANCZOS,
                )
                x = (index % cols) * (target_width + margin) + margin
                y = (index // cols) * (target_height + margin) + margin
                combined_image.paste(resized, (x, y))
        except OSError as error:
            QMessageBox.warning(main_ui, "Image error", f"{source_path.name}: {error}")

    save_folder = QFileDialog.getExistingDirectory(main_ui, "Select Save Folder")
    if not save_folder:
        return

    output_path = Path(save_folder) / "combined_image_with_design_resized.png"
    combined_image.save(output_path, format="PNG")

    pixmap = QPixmap(str(output_path))
    if pixmap.isNull():
        QMessageBox.critical(main_ui, "Error", "Failed to load the combined image.")
    else:
        main_ui.preview_label.setPixmap(
            pixmap.scaled(
                main_ui.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )
        main_ui.preview_label.adjustSize()

    QMessageBox.information(main_ui, "Success", f"Image saved to {output_path}")
