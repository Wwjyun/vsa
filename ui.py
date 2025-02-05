from PySide6.QtWidgets import (
    QApplication, QWidget, QComboBox, QMessageBox, QVBoxLayout, QPushButton,
    QLineEdit, QLabel, QGridLayout, QScrollArea, QHBoxLayout, QFileDialog
)
from PySide6.QtCore import Qt, QRect, Slot
from PySide6.QtGui import QColor, QPixmap
from search import perform_search
from search2 import open_image_from_search
from plot import PlotWindow
from lossmap_ui import LossMapUI
from compare_vertical import vertical_comparison
from compare_horizontal import compare_horizontal
from calculate_vertical_yield import vertical_yield
from customize_map_ui import CustomizeMapUI
import shutil
import os
import sys
import random
import json


class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.current_button_name = ""
        self.custom_color_map = None

    def initUI(self):
        layout = QGridLayout()

        # 编号和刻号输入框
        self.label_number = QLabel('Lot ID', self)
        self.input_number = QLineEdit(self)
        self.label_code1 = QLabel('Component ID', self)
        self.input_code1 = QLineEdit(self)

        # 下拉菜单
        self.label_dropdown = QLabel('product', self)
        self.combo = QComboBox(self)
        self.combo.addItems(["Cartier", "i pixel plus", "ADB"])
        self.combo.currentTextChanged.connect(self.update_button_names)
        layout.addWidget(self.label_dropdown, 0, 0)
        layout.addWidget(self.combo, 0, 1)
        layout.addWidget(self.label_number, 1, 0)
        layout.addWidget(self.input_number, 1, 1)
        layout.addWidget(self.label_code1, 1, 2)
        layout.addWidget(self.input_code1, 1, 3)

        # 地图大小输入
        self.label_plot_width = QLabel('map weight', self)
        self.input_plot_width = QLineEdit(self)
        self.input_plot_width.setPlaceholderText('2000')
        self.label_plot_height = QLabel('map hight', self)
        self.input_plot_height = QLineEdit(self)
        self.input_plot_height.setPlaceholderText('2000')
        layout.addWidget(self.label_plot_width, 2, 0)
        layout.addWidget(self.input_plot_width, 2, 1)
        layout.addWidget(self.label_plot_height, 2, 2)
        layout.addWidget(self.input_plot_height, 2, 3)

        # 点大小输入
        self.label_point_size = QLabel('point size', self)
        self.input_point_size = QLineEdit(self)
        self.input_point_size.setPlaceholderText('10')
        layout.addWidget(self.label_point_size, 2, 4)
        layout.addWidget(self.input_point_size, 2, 5)

        # 搜索按钮
        search_button = QPushButton('Search', self)
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
        original_button = QPushButton('OriginalPicture', self)
        roi_button = QPushButton('Roi', self)
        loss_custom_button = QPushButton('LossCustomized', self)

        original_button.clicked.connect(self.download_original)
        roi_button.clicked.connect(self.plot_roi)
        loss_custom_button.clicked.connect(self.open_loss_custom_ui)
        button_container.addWidget(original_button)
        button_container.addWidget(roi_button)
        button_container.addWidget(loss_custom_button)

        vertical_comparison_button = QPushButton('VerticalComparison', self)
        horizontal_comparison_button = QPushButton('HorizontalComparison', self)
        customize_map_button = QPushButton('CustomizeMap', self)
        vertical_yield_button = QPushButton('VerticalYield', self)
        export_map_button = QPushButton('ExportMap', self)
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
            button = QPushButton(f'Button {i+1}', self.button_layout)
            button.setFixedSize(100, 50)
            button.clicked.connect(self.button_clicked)
            self.buttons.append(button)
            self.button_vbox.addWidget(button)

        self.button_vbox.addStretch(1)
        layout.addWidget(self.button_layout, 4, 6, 4, 1)

        # 搜索栏
        self.label_search = QLabel('PKG NO', self)
        self.input_search = QLineEdit(self)
        self.button_search = QPushButton('Search', self)
        self.button_search.clicked.connect(self.search_image)
        layout.addWidget(self.label_search, 9, 0)
        layout.addWidget(self.input_search, 9, 1, 1, 4)
        layout.addWidget(self.button_search, 9, 5)

        self.setLayout(layout)
        self.setWindowTitle('VSA')
        self.setGeometry(300, 300, 1000, 800)
        self.show()

    # 搜索功能
    def search(self):
        number = self.input_number.text()
        code1 = self.input_code1.text()
        option = self.combo.currentText()  # 获取选项
        self.mt_image_path = perform_search(option, number, code1, 'mt')  # 传递 option

    # 按钮点击事件
    def button_clicked(self):
        try:
            button = self.sender()
            self.current_button_name = button.text()
            button_name = self.current_button_name.lower().replace(' ', '_')
            code = self.input_code1.text()
            option = self.combo.currentText()  # 获取选项
            image_path = perform_search(option, self.input_number.text(), code, button_name)
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                self.preview_label.setText("Image not found or failed to load.")
            else:
                self.preview_label.setPixmap(pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.preview_label.adjustSize()
        except Exception as e:
            print(f"Error in button_clicked: {e}")

    # 下载原始文件
    def download_original(self):
        try:
            number = self.input_number.text()
            code = self.input_code1.text() if self.current_button_name == 'MT' else self.input_code1.text()
            option = self.combo.currentText()  # 获取选项
            source_folder = f"D:/Database-PC/{option}/org/{number}/{self.current_button_name}/{code}"
            target_folder = QFileDialog.getExistingDirectory(self, "选择保存路径")
            if target_folder:
                self.download_folder(source_folder, target_folder)
        except Exception as e:
            print(f"Error in download_original: {e}")

    # 导出地图
    def export_map(self):
        try:
            number = self.input_number.text()
            code = self.input_code1.text() if self.current_button_name == 'MT' else self.input_code1.text()
            option = self.combo.currentText()  # 获取选项
            source_file = f"D:/Database-PC/{option}/map/{number}/{self.current_button_name}/{code}.png"
            if not os.path.exists(source_file):
                print(f"File does not exist: {source_file}")
                return
            target_folder = QFileDialog.getExistingDirectory(self, "选择保存路径")
            if target_folder:
                new_file_name = f"{self.current_button_name}_{code}.png"
                target_file = os.path.join(target_folder, new_file_name)
                self.download_file(source_file, target_file)
        except Exception as e:
            print(f"Error in export_map: {e}")

    # 下载文件夹
    def download_folder(self, source_folder, target_folder):
        try:
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            for item in os.listdir(source_folder):
                s = os.path.join(source_folder, item)
                d = os.path.join(target_folder, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, False, None)
                else:
                    shutil.copy2(s, d)
        except Exception as e:
            print(f"Error in download_folder: {e}")

    # 下载文件
    def download_file(self, source_file, target_folder):
        try:
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            shutil.copy2(source_file, target_folder)
        except Exception as e:
            print(f"Error in download_file: {e}")

    # 绘制 ROI
    def plot_roi(self):
        try:
            # 从输入框和下拉框获取用户输入
            number = self.input_number.text()  # 获取编号
            code = self.input_code1.text()    # 获取代码
            option = self.combo.currentText()  # 获取下拉选项

            # 构造路径
            csv_path = f"D:/Database-PC/{option}/csv/{number}/{self.current_button_name}/{code}.csv"
            image_folder_path = f"D:/Database-PC/{option}/roi/{number}/{self.current_button_name}/{code}"
            image_url = f"D:/Database-PC/{option}/example/{self.current_button_name}/ok.tiff"
            port = random.randint(5000, 9000)

            # 检查路径是否存在
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"CSV file not found: {csv_path}")
            if not os.path.exists(image_folder_path):
                raise FileNotFoundError(f"Image folder not found: {image_folder_path}")
            if not os.path.exists(image_url):
                raise FileNotFoundError(f"Image URL not found: {image_url}")

            # 创建 PlotWindow 窗口并传递所有必要参数
            self.plot_window = PlotWindow(csv_path, image_folder_path, self.current_button_name, port, image_url, number, code, option)
            self.plot_window.show()

        except Exception as e:
            QMessageBox.warning(self, "錯誤", f"繪圖失敗: {e}")



    @Slot(str)
    def update_search_field(self, no):
        self.input_search.setText(no)

    def lighten_color(self, color, factor=0.2):
        color = QColor(color)
        hsv = list(color.getHsvF())
        hsv[2] = min(1, hsv[2] + factor)
        return QColor.fromHsvF(*hsv).name()

    # 搜索图片
    def search_image(self):
        try:
            number = self.input_number.text()
            code = self.input_code1.text() if self.current_button_name == 'MT' else self.input_code1.text()
            no = self.input_search.text()
            option = self.combo.currentText()  # 获取选项
            open_image_from_search(number, code, no, self.current_button_name)
        except Exception as e:
            print(f"Error in search_image: {e}")

    # 打开定制 UI
    def open_loss_custom_ui(self):
        try:
            self.loss_custom_ui = LossMapUI(self)
            self.loss_custom_ui.show()
        except Exception as e:
            print(f"Error in open_loss_custom_ui: {e}")

    def open_customize_map_ui(self):
        number = self.input_number.text()
        code = self.input_code1.text()
        option = self.combo.currentText()  # 获取选项
        current_button_name = self.current_button_name
        
        self.customize_map_ui = CustomizeMapUI(option,number, current_button_name, code)
        self.customize_map_ui.show()
        

    # 加载按钮名称
    def load_button_names_from_json(self):
        try:
            with open('button_names.json', 'r') as f:
                self.button_name_map = json.load(f)
        except Exception as e:
            print(f"Error loading JSON: {e}")
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
                    button.setText(f'Button {i+1}')  # 如果没有对应的名字则保留默认名称
        else:
            for i, button in enumerate(self.buttons):
                button.setText(f'Button {i+1}')  # 恢复默认名称


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec())
