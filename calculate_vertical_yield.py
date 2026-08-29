from pathlib import Path

from PIL import Image
from PySide6.QtGui import QPixmap, Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox

from vsa_paths import STAGE_SEQUENCE, bar_image_path


def vertical_yield(main_ui):
    number = main_ui.input_number.text()
    option = main_ui.combo.currentText()
    button_names = STAGE_SEQUENCE
    image_paths = {}
    target_width, target_height = 2160, 2160  # Adjust these values as needed
    margin = 20

    # Collect image paths and handle missing images
    for button_name in button_names:
        image_path = bar_image_path(option, number, button_name)
        if image_path.is_file():
            image_paths[button_name] = image_path
        else:
            image_paths[button_name] = None
            print(f"Image not found for {button_name}, leaving space blank.")

    # Define the combined image size and margins
    combined_width = target_width * 7 + 8 * margin  # 5 images wide
    combined_height = target_height * 2 + 3 * margin  # 2 images high

    combined_image = Image.new("RGB", (combined_width, combined_height), (255, 255, 255))
    # Paste the images into the combined image
    for i, button_name in enumerate(button_names):
        x = (i % 7) * (target_width + margin) + margin
        y = (i // 7) * (target_height + margin) + margin
        if image_paths[button_name]:
            with Image.open(image_paths[button_name]) as source_image:
                resized = source_image.convert("RGB").resize(
                    (target_width, target_height), Image.Resampling.LANCZOS
                )
                combined_image.paste(resized, (x, y))

    # Allow user to select the save folder
    save_folder = QFileDialog.getExistingDirectory(main_ui, "Select Save Folder")
    if not save_folder:
        return

    output_path = Path(save_folder) / "combined_image_vertical.tiff"
    combined_image.save(output_path, format="TIFF")  # Save as TIFF

    # Display the saved image
    pixmap = QPixmap(str(output_path))
    if pixmap.isNull():
        QMessageBox.critical(main_ui, "Error", "Failed to load the combined image.")
    else:
        main_ui.preview_label.setPixmap(
            pixmap.scaled(main_ui.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        main_ui.preview_label.adjustSize()

    QMessageBox.information(main_ui, "Success", f"Image saved to {output_path}")
