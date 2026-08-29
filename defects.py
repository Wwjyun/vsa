import os

import pandas as pd
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QPushButton, QVBoxLayout


def select_good_defects(input_folder):
    defect_types = set()

    for file_name in os.listdir(input_folder):
        if file_name.endswith(".csv"):
            input_file = os.path.join(input_folder, file_name)
            defect_data = pd.read_csv(input_file)

            # 打印列名以检查是否有 'DefectType' 列
            print(f"Columns in {file_name}: {defect_data.columns.tolist()}")

            # 检查是否存在 'DefectType' 列
            if "DefectType" in defect_data.columns:
                defect_types.update(defect_data["DefectType"].unique())
            else:
                print(f"Skipping {file_name}: Missing 'DefectType' column.")

    _app = QApplication.instance() or QApplication([])  # Keep the application alive for the dialog.
    dialog = QDialog()
    layout = QVBoxLayout()

    checkboxes = {defect: QCheckBox(defect) for defect in defect_types}
    for checkbox in checkboxes.values():
        layout.addWidget(checkbox)

    button = QPushButton("Confirm")
    layout.addWidget(button)
    dialog.setLayout(layout)

    selected_defects = []

    def on_confirm():
        nonlocal selected_defects
        selected_defects = [
            defect for defect, checkbox in checkboxes.items() if checkbox.isChecked()
        ]
        dialog.accept()

    button.clicked.connect(on_confirm)
    dialog.exec()

    return selected_defects
