from PIL import Image, ImageDraw
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtGui import QPixmap, Qt
import os

def compare_horizontal(main_ui):
    number = main_ui.input_number.text()
    current_button_name = main_ui.current_button_name
    option = main_ui.combo.currentText()
    folder_path = f"D:/Database-PC/{option}/map/{number}/{current_button_name}"
    
    if not os.path.exists(folder_path):
        QMessageBox.critical(main_ui, "Error", f"Folder not found: {folder_path}")
        return

    # Define the image size and prepare a list for images
    target_width, target_height = 2160, 2160
    images = []

    # Adjust the expected filenames to match actual files
    expected_files = [f"{number}{str(i).zfill(3)}.png" for i in range(1, 11)]
    found_images = {img: os.path.join(folder_path, img) for img in os.listdir(folder_path) if img.endswith(('.jpg', '.png', '.tiff'))}

    print("Expected files:", expected_files)
    print("Found images:", found_images.keys())

    # Fill in images, and add a blank image where an image is missing
    for file_name in expected_files:
        actual_file_name = file_name.replace("000", "00", 1)  # Adjust to match actual file format
        if actual_file_name in found_images:
            try:
                img = Image.open(found_images[actual_file_name]).resize((target_width, target_height), Image.LANCZOS)
                images.append(img)
            except Exception as e:
                print(f"Error loading image {actual_file_name}: {e}")
                blank_img = Image.new('RGB', (target_width, target_height), (255, 255, 255))
                images.append(blank_img)
        else:
            print(f"File {file_name} not found, adding a blank space.")
            blank_img = Image.new('RGB', (target_width, target_height), (255, 255, 255))
            images.append(blank_img)

    # Calculate the grid size
    cols = 5  # Fixed number of columns
    rows = (len(images) + cols - 1) // cols

    # Define the combined image size and margins
    combined_width = target_width * cols + (cols + 1) * 20
    combined_height = target_height * rows + (rows + 1) * 20
    margin = 20

    combined_image = Image.new('RGB', (combined_width, combined_height), (255, 255, 255))

    # Paste the images into the combined image
    for i, image in enumerate(images):
        x = (i % cols) * (target_width + margin) + margin
        y = (i // cols) * (target_height + margin) + margin
        combined_image.paste(image, (x, y))

    # Allow user to select the save folder
    save_folder = QFileDialog.getExistingDirectory(main_ui, "Select Save Folder")
    if not save_folder:
        return

    output_path = os.path.join(save_folder, 'combined_image_with_design_resized.png')
    combined_image.save(output_path, format='PNG')

    # Display the saved image
    pixmap = QPixmap(output_path)
    if pixmap.isNull():
        QMessageBox.critical(main_ui, "Error", "Failed to load the combined image.")
    else:
        main_ui.preview_label.setPixmap(pixmap.scaled(main_ui.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        main_ui.preview_label.adjustSize()

    QMessageBox.information(main_ui, "Success", f"Image saved to {output_path}")
