import json
import sys
from pathlib import Path

from PySide6.QtCore import QRect, Qt, Slot
from PySide6.QtGui import QIntValidator, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from calculate_vertical_yield import vertical_yield
from compare_horizontal import compare_horizontal
from compare_vertical import vertical_comparison
from customize_map_ui import CustomizeMapUI
from file_operations import copy_file, copy_folder_contents
from lossmap_ui import LossMapUI
from plot import PlotWindow
from search import perform_search
from search2 import open_image_from_search
from vsa_paths import (
    BUTTON_NAMES_PATH,
    csv_path,
    example_image_path,
    map_image_path,
    original_folder,
    roi_folder,
)


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.current_button_name = ""
        self.custom_color_map = None
        self.initUI()

    def initUI(self):
        layout = QGridLayout()

        # 编号和刻号输入框
        self.label_number = QLabel("Lot ID", self)
        self.input_number = QLineEdit(self)
        self.label_code1 = QLabel("Component ID", self)
        self.input_code1 = QLineEdit(self)

        # 下拉菜单
        self.label_dropdown = QLabel("product", self)
        self.combo = QComboBox(self)
        self.combo.addItems(["Product A", "Product B", "Product C"])
        self.combo.currentTextChanged.connect(self.update_button_names)
        layout.addWidget(self.label_dropdown, 0, 0)
        layout.addWidget(self.combo, 0, 1)
        layout.addWidget(self.label_number, 1, 0)
        layout.addWidget(self.input_number, 1, 1)
        layout.addWidget(self.label_code1, 1, 2)
        layout.addWidget(self.input_code1, 1, 3)

        # 地图大小输入
        self.label_plot_width = QLabel("Map width", self)
        self.input_plot_width = QLineEdit(self)
        self.input_plot_width.setPlaceholderText("2000")
        self.input_plot_width.setValidator(QIntValidator(100, 10000, self))
        self.label_plot_height = QLabel("Map height", self)
        self.input_plot_height = QLineEdit(self)
        self.input_plot_height.setPlaceholderText("2000")
        self.input_plot_height.setValidator(QIntValidator(100, 10000, self))
        layout.addWidget(self.label_plot_width, 2, 0)
        layout.addWidget(self.input_plot_width, 2, 1)
        layout.addWidget(self.label_plot_height, 2, 2)
        layout.addWidget(self.input_plot_height, 2, 3)

        # 点大小输入
        self.label_point_size = QLabel("point size", self)
        self.input_point_size = QLineEdit(self)
        self.input_point_size.setPlaceholderText("10")
        self.input_point_size.setValidator(QIntValidator(1, 100, self))
        layout.addWidget(self.label_point_size, 2, 4)
        layout.addWidget(self.input_point_size, 2, 5)

        # 搜索按钮
        search_button = QPushButton("Search", self)
        search_button.clicked.connect(self.search)
        layout.addWidget(search_button, 3, 0, 1, 6, alignment=Qt.AlignCenter)

        # 预览窗口
        self.preview_label = QLabel(self)
        self.preview_label.setAlignment(Qt.AlignCenter)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.preview_label)
        layout.addWidget(scroll_area, 4, 0, 4, 6)

        # 下方按钮
        button_container = QHBoxLayout()
        original_button = QPushButton("OriginalPicture", self)
        roi_button = QPushButton("Roi", self)
        loss_custom_button = QPushButton("LossCustomized", self)

        original_button.clicked.connect(self.download_original)
        roi_button.clicked.connect(self.plot_roi)
        loss_custom_button.clicked.connect(self.open_loss_custom_ui)
        button_container.addWidget(original_button)
        button_container.addWidget(roi_button)
        button_container.addWidget(loss_custom_button)

        vertical_comparison_button = QPushButton("VerticalComparison", self)
        horizontal_comparison_button = QPushButton("HorizontalComparison", self)
        customize_map_button = QPushButton("CustomizeMap", self)
        vertical_yield_button = QPushButton("VerticalYield", self)
        export_map_button = QPushButton("ExportMap", self)
        export_map_button.clicked.connect(self.export_map)

        vertical_comparison_button.clicked.connect(lambda: vertical_comparison(self))
        horizontal_comparison_button.clicked.connect(lambda: compare_horizontal(self))
        customize_map_button.clicked.connect(self.open_customize_map_ui)
        vertical_yield_button.clicked.connect(lambda: vertical_yield(self))

        button_container.addWidget(vertical_comparison_button)
        button_container.addWidget(horizontal_comparison_button)
        button_container.addWidget(customize_map_button)
        button_container.addWidget(vertical_yield_button)
        button_container.addWidget(export_map_button)

        layout.addLayout(button_container, 8, 0, 1, 6)

        # 右侧按钮布局
        self.button_layout = QWidget(self)
        self.button_layout.setGeometry(QRect(600, 50, 600, 600))
        self.button_vbox = QVBoxLayout(self.button_layout)

        # 从 JSON 文件加载按钮名称
        self.load_button_names_from_json()

        # 初始化按钮
        self.buttons = []
        for i in range(14):
            button = QPushButton(f"Button {i + 1}", self.button_layout)
            button.setFixedSize(100, 50)
            button.clicked.connect(self.button_clicked)
            self.buttons.append(button)
            self.button_vbox.addWidget(button)

        self.button_vbox.addStretch(1)
        layout.addWidget(self.button_layout, 4, 6, 4, 1)
        self.update_button_names()

        # 搜索栏
        self.label_search = QLabel("PKG NO", self)
        self.input_search = QLineEdit(self)
        self.button_search = QPushButton("Search", self)
        self.button_search.clicked.connect(self.search_image)
        layout.addWidget(self.label_search, 9, 0)
        layout.addWidget(self.input_search, 9, 1, 1, 4)
        layout.addWidget(self.button_search, 9, 5)

        self.setLayout(layout)
        self.setWindowTitle("VSA")
        self.setGeometry(300, 300, 1000, 800)

    def selected_values(self, require_stage=True):
        number = self.input_number.text().strip()
        code = self.input_code1.text().strip()
        option = self.combo.currentText().strip()
        if not number:
            raise ValueError("Lot ID is required.")
        if not code:
            raise ValueError("Component ID is required.")
        if require_stage and not self.current_button_name:
            raise ValueError("Select a stage first.")
        return option, number, code, self.current_button_name

    def display_map_image(self, stage):
        option, number, code, _ = self.selected_values(require_stage=False)
        image_path = perform_search(option, number, code, stage)
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.preview_label.setText(f"Image not found: {image_path}")
            return
        self.preview_label.setPixmap(
            pixmap.scaled(
                self.preview_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )
        self.preview_label.adjustSize()

    # 搜索功能
    def search(self):
        try:
            self.current_button_name = "MT"
            self.display_map_image("MT")
        except ValueError as error:
            QMessageBox.warning(self, "Missing input", str(error))

    # 按钮点击事件
    def button_clicked(self):
        try:
            button = self.sender()
            self.current_button_name = button.text()
            self.display_map_image(self.current_button_name)
        except ValueError as error:
            QMessageBox.warning(self, "Missing input", str(error))
        except Exception as error:
            QMessageBox.critical(self, "Preview error", str(error))

    # 下载原始文件
    def download_original(self):
        try:
            option, number, code, stage = self.selected_values()
            source_folder = original_folder(option, number, stage, code)
            target_folder = QFileDialog.getExistingDirectory(self, "选择保存路径")
            if target_folder:
                self.download_folder(source_folder, target_folder)
                QMessageBox.information(self, "Success", "Original files exported.")
        except (ValueError, FileNotFoundError) as error:
            QMessageBox.warning(self, "Export error", str(error))
        except OSError as error:
            QMessageBox.critical(self, "Export error", str(error))

    # 导出地图
    def export_map(self):
        try:
            option, number, code, stage = self.selected_values()
            source_file = map_image_path(option, number, stage, code)
            if not source_file.is_file():
                raise FileNotFoundError(f"Map image not found: {source_file}")
            target_folder = QFileDialog.getExistingDirectory(self, "选择保存路径")
            if target_folder:
                target_file = Path(target_folder) / f"{stage}_{code}{source_file.suffix}"
                if target_file.exists():
                    answer = QMessageBox.question(
                        self,
                        "Replace file?",
                        f"{target_file.name} already exists. Replace it?",
                    )
                    if answer != QMessageBox.Yes:
                        return
                self.download_file(source_file, target_file)
                QMessageBox.information(self, "Success", f"Map exported to {target_file}")
        except (ValueError, FileNotFoundError) as error:
            QMessageBox.warning(self, "Export error", str(error))
        except OSError as error:
            QMessageBox.critical(self, "Export error", str(error))

    # 下载文件夹
    def download_folder(self, source_folder, target_folder):
        return copy_folder_contents(source_folder, target_folder)

    # 下载文件
    def download_file(self, source_file, target_file):
        return copy_file(source_file, target_file)

    # 绘制 ROI
    def plot_roi(self):
        try:
            option, number, code, stage = self.selected_values()
            csv_file = csv_path(option, number, stage, code)
            image_folder = roi_folder(option, number, stage, code)
            image_url = example_image_path(option, stage)

            if not csv_file.is_file():
                raise FileNotFoundError(f"CSV file not found: {csv_file}")
            if not image_folder.is_dir():
                raise FileNotFoundError(f"Image folder not found: {image_folder}")
            if not image_url.is_file():
                raise FileNotFoundError(f"Image URL not found: {image_url}")

            self.plot_window = PlotWindow(
                csv_file,
                image_folder,
                stage,
                image_url,
                number,
                code,
                option,
            )
            self.plot_window.show()

        except (ValueError, FileNotFoundError) as error:
            QMessageBox.warning(self, "錯誤", f"繪圖失敗: {error}")
        except Exception as error:
            QMessageBox.critical(self, "錯誤", f"繪圖失敗: {error}")

    @Slot(str)
    def update_search_field(self, no):
        self.input_search.setText(no)

    # 搜索图片
    def search_image(self):
        try:
            option, number, code, stage = self.selected_values()
            no = self.input_search.text().strip()
            open_image_from_search(option, number, code, no, stage)
        except (ValueError, FileNotFoundError) as error:
            QMessageBox.warning(self, "Image search", str(error))
        except OSError as error:
            QMessageBox.critical(self, "Image search", str(error))

    # 打开定制 UI
    def open_loss_custom_ui(self):
        try:
            self.selected_values()
            if self.current_button_name not in {f"LOSS{i}" for i in range(1, 7)}:
                raise ValueError("Select a LOSS stage first.")
            self.loss_custom_ui = LossMapUI(self)
            self.loss_custom_ui.show()
        except (ValueError, FileNotFoundError) as error:
            QMessageBox.warning(self, "Loss map", str(error))
        except Exception as error:
            QMessageBox.critical(self, "Loss map", str(error))

    def open_customize_map_ui(self):
        try:
            option, number, code, stage = self.selected_values()
            self.customize_map_ui = CustomizeMapUI(option, number, stage, code)
            self.customize_map_ui.show()
        except ValueError as error:
            QMessageBox.warning(self, "Customize map", str(error))

    # 加载按钮名称
    def load_button_names_from_json(self):
        try:
            with BUTTON_NAMES_PATH.open("r", encoding="utf-8") as f:
                self.button_name_map = json.load(f)
        except (OSError, json.JSONDecodeError) as error:
            QMessageBox.critical(self, "Configuration error", str(error))
            self.button_name_map = {}

    # 更新按钮名称
    def update_button_names(self):
        selected_option = self.combo.currentText()
        if selected_option in self.button_name_map:
            button_names = self.button_name_map[selected_option]
            for i, button in enumerate(self.buttons):
                if i < len(button_names):
                    button.setText(button_names[i])
                else:
                    button.setText(f"Button {i + 1}")  # 如果没有对应的名字则保留默认名称
        else:
            for i, button in enumerate(self.buttons):
                button.setText(f"Button {i + 1}")  # 恢复默认名称


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec())
