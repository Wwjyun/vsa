import logging
from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool, Slot
from PySide6.QtGui import QCursor, QIntValidator, QPixmap
from PySide6.QtWidgets import (
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

from vsa.config import ConfigurationError, load_product_stages
from vsa.diagnostics import diagnostic_summary
from vsa.models import InspectionSelection
from vsa.paths import (
    csv_path,
    example_image_path,
    map_image_path,
    original_folder,
    roi_folder,
    roi_image_path,
)
from vsa.services.files import copy_file, copy_folder_contents
from vsa.services.system import open_local_file
from vsa.views.actions import (
    export_horizontal_comparison,
    export_vertical_comparison,
    export_vertical_yield,
)
from vsa.views.custom_map_window import CustomizeMapWindow
from vsa.views.loss_map_window import LossMapWindow
from vsa.views.roi_plot import RoiPlotWindow
from vsa.workers import FunctionWorker

logger = logging.getLogger(__name__)

DEFAULT_PLOT_WIDTH = 1000
DEFAULT_PLOT_HEIGHT = 800
DEFAULT_POINT_SIZE = 2


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.current_button_name = ""
        self.custom_color_map = None
        self.thread_pool = QThreadPool.globalInstance()
        self.active_workers: set[FunctionWorker] = set()
        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        self.load_button_names_from_json()

        self.label_number = QLabel("Lot ID", self)
        self.input_number = QLineEdit(self)
        self.label_code1 = QLabel("Component ID", self)
        self.input_code1 = QLineEdit(self)

        self.label_dropdown = QLabel("Product", self)
        self.combo = QComboBox(self)
        self.combo.addItems(self.button_name_map or ["Product A"])
        self.combo.currentTextChanged.connect(self.update_button_names)
        layout.addWidget(self.label_dropdown, 0, 0)
        layout.addWidget(self.combo, 0, 1)
        layout.addWidget(self.label_number, 1, 0)
        layout.addWidget(self.input_number, 1, 1)
        layout.addWidget(self.label_code1, 1, 2)
        layout.addWidget(self.input_code1, 1, 3)

        self.label_plot_width = QLabel("Map width", self)
        self.input_plot_width = QLineEdit(self)
        self.input_plot_width.setPlaceholderText(str(DEFAULT_PLOT_WIDTH))
        self.input_plot_width.setValidator(QIntValidator(100, 10000, self))
        self.label_plot_height = QLabel("Map height", self)
        self.input_plot_height = QLineEdit(self)
        self.input_plot_height.setPlaceholderText(str(DEFAULT_PLOT_HEIGHT))
        self.input_plot_height.setValidator(QIntValidator(100, 10000, self))
        layout.addWidget(self.label_plot_width, 2, 0)
        layout.addWidget(self.input_plot_width, 2, 1)
        layout.addWidget(self.label_plot_height, 2, 2)
        layout.addWidget(self.input_plot_height, 2, 3)

        self.label_point_size = QLabel("Point size", self)
        self.input_point_size = QLineEdit(self)
        self.input_point_size.setPlaceholderText(str(DEFAULT_POINT_SIZE))
        self.input_point_size.setValidator(QIntValidator(1, 100, self))
        layout.addWidget(self.label_point_size, 2, 4)
        layout.addWidget(self.input_point_size, 2, 5)

        search_button = QPushButton("Search", self)
        search_button.clicked.connect(self.search)
        layout.addWidget(search_button, 3, 0, 1, 6, alignment=Qt.AlignCenter)

        self.status_label = QLabel("Ready", self)
        layout.addWidget(self.status_label, 3, 6)

        self.preview_label = QLabel(self)
        self.preview_label.setAlignment(Qt.AlignCenter)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.preview_label)
        layout.addWidget(scroll_area, 4, 0, 4, 6)

        button_container = QHBoxLayout()
        original_button = QPushButton("Export Original", self)
        roi_button = QPushButton("ROI", self)
        loss_custom_button = QPushButton("Loss Map", self)

        original_button.clicked.connect(self.download_original)
        roi_button.clicked.connect(self.plot_roi)
        loss_custom_button.clicked.connect(self.open_loss_custom_ui)
        button_container.addWidget(original_button)
        button_container.addWidget(roi_button)
        button_container.addWidget(loss_custom_button)

        vertical_comparison_button = QPushButton("Stage Comparison", self)
        horizontal_comparison_button = QPushButton("Lot Comparison", self)
        customize_map_button = QPushButton("Customize Map", self)
        vertical_yield_button = QPushButton("Yield Comparison", self)
        export_map_button = QPushButton("Export Map", self)
        diagnostics_button = QPushButton("Diagnostics", self)
        export_map_button.clicked.connect(self.export_map)
        diagnostics_button.clicked.connect(self.show_diagnostics)

        vertical_comparison_button.clicked.connect(lambda: export_vertical_comparison(self))
        horizontal_comparison_button.clicked.connect(lambda: export_horizontal_comparison(self))
        customize_map_button.clicked.connect(self.open_customize_map_ui)
        vertical_yield_button.clicked.connect(lambda: export_vertical_yield(self))

        button_container.addWidget(vertical_comparison_button)
        button_container.addWidget(horizontal_comparison_button)
        button_container.addWidget(customize_map_button)
        button_container.addWidget(vertical_yield_button)
        button_container.addWidget(export_map_button)
        button_container.addWidget(diagnostics_button)

        layout.addLayout(button_container, 8, 0, 1, 6)

        self.button_layout = QWidget(self)
        self.button_vbox = QVBoxLayout(self.button_layout)

        self.buttons = []
        for i in range(14):
            button = QPushButton(f"Button {i + 1}", self.button_layout)
            button.setMinimumSize(100, 32)
            button.clicked.connect(self.button_clicked)
            self.buttons.append(button)
            self.button_vbox.addWidget(button)

        self.button_vbox.addStretch(1)
        layout.addWidget(self.button_layout, 4, 6, 4, 1)
        self.update_button_names()

        self.label_search = QLabel("PKG NO", self)
        self.input_search = QLineEdit(self)
        self.button_search = QPushButton("Search", self)
        self.button_search.clicked.connect(self.search_image)
        layout.addWidget(self.label_search, 9, 0)
        layout.addWidget(self.input_search, 9, 1, 1, 4)
        layout.addWidget(self.button_search, 9, 5)

        self.setLayout(layout)
        self.setWindowTitle("VSA")
        self.setMinimumSize(800, 600)
        self.resize(1000, 800)

    def plot_options(self) -> dict[str, int]:
        """Return the validated map size and point size, falling back to defaults."""

        def value(field, default: int) -> int:
            text = field.text().strip()
            return int(text) if text else default

        return {
            "plot_width": value(self.input_plot_width, DEFAULT_PLOT_WIDTH),
            "plot_height": value(self.input_plot_height, DEFAULT_PLOT_HEIGHT),
            "point_size": value(self.input_point_size, DEFAULT_POINT_SIZE),
        }

    def selected_values(self, require_stage=True) -> InspectionSelection:
        return InspectionSelection(
            product=self.combo.currentText(),
            lot_id=self.input_number.text(),
            component_id=self.input_code1.text(),
            stage=self.current_button_name,
        ).validated(require_stage=require_stage)

    def display_map_image(self, stage):
        selection = self.selected_values(require_stage=False)
        image_path = map_image_path(
            selection.product, selection.lot_id, stage, selection.component_id
        )
        pixmap = QPixmap(str(image_path))
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

    def search(self):
        try:
            self.current_button_name = "MT"
            self.display_map_image("MT")
        except ValueError as error:
            QMessageBox.warning(self, "Missing input", str(error))

    def button_clicked(self):
        try:
            button = self.sender()
            self.current_button_name = button.text()
            self.display_map_image(self.current_button_name)
        except ValueError as error:
            QMessageBox.warning(self, "Missing input", str(error))
        except (OSError, RuntimeError) as error:
            logger.exception("Map preview failed")
            QMessageBox.critical(self, "Preview error", str(error))

    def download_original(self):
        try:
            selection = self.selected_values()
            source_folder = original_folder(
                selection.product,
                selection.lot_id,
                selection.stage,
                selection.component_id,
            )
            target_folder = QFileDialog.getExistingDirectory(self, "Select save folder")
            if target_folder:
                self.run_background_task(
                    lambda: self.download_folder(source_folder, target_folder),
                    success_message="Original files exported.",
                    error_title="Export error",
                )
        except (ValueError, FileNotFoundError) as error:
            QMessageBox.warning(self, "Export error", str(error))
        except OSError as error:
            QMessageBox.critical(self, "Export error", str(error))

    def export_map(self):
        try:
            selection = self.selected_values()
            source_file = map_image_path(
                selection.product,
                selection.lot_id,
                selection.stage,
                selection.component_id,
            )
            if not source_file.is_file():
                raise FileNotFoundError(f"Map image not found: {source_file}")
            target_folder = QFileDialog.getExistingDirectory(self, "Select save folder")
            if target_folder:
                target_file = (
                    Path(target_folder)
                    / f"{selection.stage}_{selection.component_id}{source_file.suffix}"
                )
                if target_file.exists():
                    answer = QMessageBox.question(
                        self,
                        "Replace file?",
                        f"{target_file.name} already exists. Replace it?",
                    )
                    if answer != QMessageBox.Yes:
                        return
                self.run_background_task(
                    lambda: self.download_file(source_file, target_file),
                    success_message=f"Map exported to {target_file}",
                    error_title="Export error",
                )
        except (ValueError, FileNotFoundError) as error:
            QMessageBox.warning(self, "Export error", str(error))
        except OSError as error:
            QMessageBox.critical(self, "Export error", str(error))

    def download_folder(self, source_folder, target_folder):
        return copy_folder_contents(source_folder, target_folder)

    def download_file(self, source_file, target_file):
        return copy_file(source_file, target_file)

    def run_background_task(
        self,
        function,
        *,
        on_success=None,
        success_message: str | None = None,
        error_title: str = "Operation error",
    ) -> None:
        worker = FunctionWorker(function)
        self.active_workers.add(worker)
        self.status_label.setText("Working…")
        self.setCursor(QCursor(Qt.WaitCursor))

        def handle_success(result):
            if on_success is not None:
                on_success(result)
            if success_message:
                QMessageBox.information(self, "Success", success_message)

        def handle_failure(error):
            QMessageBox.critical(self, error_title, str(error))

        def handle_finished():
            self.active_workers.discard(worker)
            if not self.active_workers:
                self.status_label.setText("Ready")
                self.unsetCursor()

        worker.signals.succeeded.connect(handle_success)
        worker.signals.failed.connect(handle_failure)
        worker.signals.finished.connect(handle_finished)
        self.thread_pool.start(worker)

    def show_diagnostics(self):
        QMessageBox.information(self, "VSA diagnostics", diagnostic_summary())

    def plot_roi(self):
        try:
            selection = self.selected_values()
            csv_file = csv_path(
                selection.product,
                selection.lot_id,
                selection.stage,
                selection.component_id,
            )
            image_folder = roi_folder(
                selection.product,
                selection.lot_id,
                selection.stage,
                selection.component_id,
            )
            image_url = example_image_path(selection.product, selection.stage)

            if not csv_file.is_file():
                raise FileNotFoundError(f"CSV file not found: {csv_file}")
            if not image_folder.is_dir():
                raise FileNotFoundError(f"Image folder not found: {image_folder}")
            if not image_url.is_file():
                raise FileNotFoundError(f"Image URL not found: {image_url}")

            self.plot_window = RoiPlotWindow(
                csv_file,
                image_folder,
                selection.stage,
                image_url,
                selection.lot_id,
                selection.component_id,
                selection.product,
            )
            self.plot_window.show()

        except (ValueError, FileNotFoundError) as error:
            QMessageBox.warning(self, "ROI plot error", str(error))
        except (RuntimeError, TypeError) as error:
            logger.exception("ROI plot failed")
            QMessageBox.critical(self, "ROI plot error", str(error))

    @Slot(str)
    def update_search_field(self, no):
        self.input_search.setText(no)

    def search_image(self):
        try:
            selection = self.selected_values()
            no = self.input_search.text().strip()
            image_path = roi_image_path(
                selection.product,
                selection.lot_id,
                selection.stage,
                selection.component_id,
                no,
            )
            open_local_file(image_path)
        except (ValueError, FileNotFoundError) as error:
            QMessageBox.warning(self, "Image search", str(error))
        except OSError as error:
            QMessageBox.critical(self, "Image search", str(error))

    def open_loss_custom_ui(self):
        try:
            self.selected_values()
            if self.current_button_name not in {f"LOSS{i}" for i in range(1, 7)}:
                raise ValueError("Select a LOSS stage first.")
            self.loss_custom_ui = LossMapWindow(self)
            self.loss_custom_ui.show()
        except (ValueError, FileNotFoundError) as error:
            QMessageBox.warning(self, "Loss map", str(error))
        except (RuntimeError, TypeError) as error:
            logger.exception("Loss map failed")
            QMessageBox.critical(self, "Loss map", str(error))

    def open_customize_map_ui(self):
        try:
            selection = self.selected_values()
            options = self.plot_options()
            self.customize_map_ui = CustomizeMapWindow(
                selection,
                map_size=(options["plot_width"], options["plot_height"]),
            )
            self.customize_map_ui.show()
        except ValueError as error:
            QMessageBox.warning(self, "Customize map", str(error))

    def load_button_names_from_json(self):
        try:
            self.button_name_map = load_product_stages()
        except ConfigurationError as error:
            logger.exception("Product configuration could not be loaded")
            QMessageBox.critical(self, "Configuration error", str(error))
            self.button_name_map = {}

    def update_button_names(self):
        selected_option = self.combo.currentText()
        if selected_option in self.button_name_map:
            button_names = self.button_name_map[selected_option]
            for i, button in enumerate(self.buttons):
                if i < len(button_names):
                    button.setText(button_names[i])
                else:
                    button.setText(f"Button {i + 1}")
        else:
            for i, button in enumerate(self.buttons):
                button.setText(f"Button {i + 1}")
