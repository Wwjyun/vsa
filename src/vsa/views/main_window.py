import logging
from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool, Slot
from PySide6.QtGui import QCursor, QIntValidator, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from vsa.config import (
    LOSS_STAGE_PAIRS,
    STAGE_SEQUENCE,
    ConfigurationError,
    get_data_root,
    load_product_stages,
)
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
from vsa.ui.widgets import (
    ActionButton,
    AppHeader,
    DataRow,
    FieldLabel,
    LabeledField,
    PreviewPane,
    Separator,
    SidePanel,
    StageRail,
    StatusPill,
    UnitField,
    is_loss_stage,
)
from vsa.views.actions import (
    export_horizontal_comparison,
    export_vertical_comparison,
    export_vertical_yield,
)
from vsa.views.custom_map_window import CustomizeMapWindow
from vsa.views.diagnostics_dialog import DiagnosticsDialog
from vsa.views.loss_map_window import LossMapWindow
from vsa.views.roi_plot import RoiPlotWindow
from vsa.workers import FunctionWorker

logger = logging.getLogger(__name__)

DEFAULT_PLOT_WIDTH = 1000
DEFAULT_PLOT_HEIGHT = 800
DEFAULT_POINT_SIZE = 2
STAGE_COUNT = 14


def _relative_to_data_root(path: Path) -> str:
    """Show paths relative to the data root so the UI never exposes machine paths."""

    try:
        return str(Path(path).relative_to(get_data_root()))
    except ValueError:
        return Path(path).name


class MainWindow(QWidget):
    """Operator window.

    The public surface other modules rely on is unchanged: ``combo``,
    ``input_number``, ``input_code1``, ``input_search``, ``input_plot_*``,
    ``buttons``, ``preview_label``, ``status_label``, ``current_button_name``,
    ``plot_options()``, ``selected_values()`` and ``run_background_task()``.
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("window")
        self.current_button_name = ""
        self.custom_color_map = None
        self.thread_pool = QThreadPool.globalInstance()
        self.active_workers: set[FunctionWorker] = set()
        self.initUI()

    # ------------------------------------------------------------------ UI
    def initUI(self):
        self.load_button_names_from_json()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())
        root.addWidget(self._build_query_bar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.stage_rail = StageRail(STAGE_COUNT, parent=self)
        self.buttons = self.stage_rail.buttons  # kept for callers and tests
        for button in self.buttons:
            button.clicked.connect(self.button_clicked)
        body.addWidget(self.stage_rail)

        center = QWidget(self)
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        self.preview = PreviewPane(center)
        self.preview_label = self.preview.label  # actions.py writes to this
        center_layout.addWidget(self.preview, 1)
        center_layout.addWidget(self._build_footer_bar())
        body.addWidget(center, 1)

        body.addWidget(self._build_side_panel())
        root.addLayout(body, 1)

        self.update_button_names()
        self.setWindowTitle("VSA")
        self.setMinimumSize(1120, 720)
        self.resize(1440, 900)

    def _build_header(self) -> AppHeader:
        header = AppHeader("VSA", "Visual Stage Analysis", self)
        self.status_pill = StatusPill("Ready", header)
        self.status_label = self.status_pill.label  # callers keep setText()ing this
        header.add_trailing(self.status_pill)
        diagnostics_button = QPushButton("Diagnostics", header)
        diagnostics_button.setObjectName("ghost")
        diagnostics_button.clicked.connect(self.show_diagnostics)
        header.add_trailing(diagnostics_button)
        return header

    def _build_query_bar(self) -> QFrame:
        bar = QFrame(self)
        bar.setObjectName("queryBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(18)

        self.combo = QComboBox(bar)
        self.combo.addItems(self.button_name_map or ["Product A"])
        self.combo.currentTextChanged.connect(self.update_button_names)

        self.input_number = QLineEdit(bar)
        self.input_number.setPlaceholderText("DEMO-LOT")

        self.input_code1 = QLineEdit(bar)
        self.input_code1.setPlaceholderText("DEMO-CMP")

        product_field = LabeledField("Product", self.combo, 190, bar)
        lot_field = LabeledField("Lot ID", self.input_number, 210, bar)
        component_field = LabeledField("Component ID", self.input_code1, 210, bar)
        self.label_dropdown = product_field.label
        self.label_number = lot_field.label
        self.label_code1 = component_field.label
        layout.addWidget(product_field)
        layout.addWidget(lot_field)
        layout.addWidget(component_field)

        search_button = QPushButton("Search", bar)
        search_button.setObjectName("primary")
        search_button.setFixedHeight(36)
        search_button.clicked.connect(self.search)
        layout.addWidget(search_button, 0, Qt.AlignBottom)
        layout.addWidget(Separator(True, 38, bar), 0, Qt.AlignBottom)

        options = QWidget(bar)
        options_layout = QVBoxLayout(options)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(6)
        options_label = FieldLabel("Map options", options)
        options_label.setToolTip("Optional. Applies to Loss Map and Customize Map.")
        options_row = QHBoxLayout()
        options_row.setContentsMargins(0, 0, 0, 0)
        options_row.setSpacing(8)

        width_field = UnitField("W", 104, options)
        self.input_plot_width = width_field.edit
        self.input_plot_width.setPlaceholderText(str(DEFAULT_PLOT_WIDTH))
        self.input_plot_width.setValidator(QIntValidator(100, 10000, self))
        self.label_plot_width = options_label

        height_field = UnitField("H", 104, options)
        self.input_plot_height = height_field.edit
        self.input_plot_height.setPlaceholderText(str(DEFAULT_PLOT_HEIGHT))
        self.input_plot_height.setValidator(QIntValidator(100, 10000, self))
        self.label_plot_height = options_label

        point_field = UnitField("Point", 108, options)
        self.input_point_size = point_field.edit
        self.input_point_size.setPlaceholderText(str(DEFAULT_POINT_SIZE))
        self.input_point_size.setValidator(QIntValidator(1, 100, self))
        self.label_point_size = options_label

        times = QLabel("×", options)
        times.setObjectName("hint")
        options_row.addWidget(width_field)
        options_row.addWidget(times)
        options_row.addWidget(height_field)
        options_row.addSpacing(4)
        options_row.addWidget(point_field)
        options_layout.addWidget(options_label)
        options_layout.addLayout(options_row)
        layout.addWidget(options, 0, Qt.AlignBottom)
        layout.addStretch(1)
        return bar

    def _build_footer_bar(self) -> QFrame:
        bar = QFrame(self)
        bar.setObjectName("footerBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(12)
        self.label_search = FieldLabel("PKG NO", bar)
        self.input_search = QLineEdit(bar)
        self.input_search.setPlaceholderText("—")
        self.input_search.returnPressed.connect(self.search_image)
        hint = QLabel("Double-click a point in ROI or Loss Map to fill this", bar)
        hint.setObjectName("hint")
        self.button_search = QPushButton("Open ROI image", bar)
        self.button_search.setFixedHeight(36)
        self.button_search.clicked.connect(self.search_image)
        layout.addWidget(self.label_search)
        layout.addWidget(self.input_search, 1)
        layout.addWidget(hint)
        layout.addWidget(self.button_search)
        return bar

    def _build_side_panel(self) -> SidePanel:
        panel = SidePanel(272, self)

        panel.add_section("Inspect")
        self.roi_button = ActionButton("ROI", "Interactive defect points", "primary", panel)
        self.roi_button.clicked.connect(self.plot_roi)
        panel.add(self.roi_button)
        self.loss_button = ActionButton("Loss Map", "Select a LOSS stage first", parent=panel)
        self.loss_button.clicked.connect(self.open_loss_custom_ui)
        panel.add(self.loss_button)
        self.custom_button = ActionButton("Customize Map", "Legend-driven red ratio", parent=panel)
        self.custom_button.clicked.connect(self.open_customize_map_ui)
        panel.add(self.custom_button)

        panel.add_section("Export")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(7)
        grid.setVerticalSpacing(7)
        exports = (
            ("Export Map", self.export_map),
            ("Export Original", self.download_original),
            ("Stage Comparison", lambda: export_vertical_comparison(self)),
            ("Lot Comparison", lambda: export_horizontal_comparison(self)),
        )
        for index, (text, handler) in enumerate(exports):
            button = QPushButton(text, panel)
            button.setObjectName("gridButton")
            button.clicked.connect(handler)
            grid.addWidget(button, index // 2, index % 2)
        yield_button = QPushButton("Yield Comparison", panel)
        yield_button.setObjectName("gridButton")
        yield_button.clicked.connect(lambda: export_vertical_yield(self))
        grid.addWidget(yield_button, 2, 0, 1, 2)
        panel.add_layout(grid)

        panel.add_stretch()
        panel.add(Separator(False, parent=panel))
        panel.add_section("Session")
        self.session_stage_row = DataRow("stage", "—", boxed=False, parent=panel)
        self.session_worker_row = DataRow("workers", "0 active", boxed=False, parent=panel)
        panel.add(DataRow("data root", "VSA_DATA_ROOT", boxed=False, parent=panel))
        panel.add(self.session_stage_row)
        panel.add(self.session_worker_row)
        return panel

    # --------------------------------------------------------------- state
    def _stage_description(self, stage: str) -> str:
        pair = LOSS_STAGE_PAIRS.get(stage)
        if pair:
            return f"{pair[0]} → {pair[1]}"
        if not stage:
            return "no stage selected"
        return "process stage"

    def _sync_stage_chrome(self) -> None:
        stage = self.current_button_name
        self.preview.set_stage(stage, self._stage_description(stage))
        self.session_stage_row.set_value(stage or "—")
        self.stage_rail.set_current(stage)
        if is_loss_stage(stage):
            self.loss_button.set_subtitle(f"Compare {self._stage_description(stage)}")
        else:
            self.loss_button.set_subtitle("Select a LOSS stage first")
        selection_hint = (
            f"map / {self.input_number.text() or '<lot>'} / {stage or '<stage>'} / "
            f"{self.input_code1.text() or '<component>'}"
        )
        self.preview.set_path(selection_hint if stage else "")

    # ------------------------------------------------------- unchanged API
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
        display_path = _relative_to_data_root(image_path)
        if pixmap.isNull():
            self.preview.show_message(f"Image not found:\n{display_path}")
            return
        self.preview.show_pixmap(pixmap)
        self.preview.set_path(display_path)

    def search(self):
        try:
            self.current_button_name = STAGE_SEQUENCE[0]
            self._sync_stage_chrome()
            self.display_map_image(self.current_button_name)
        except ValueError as error:
            QMessageBox.warning(self, "Missing input", str(error))

    def button_clicked(self):
        try:
            button = self.sender()
            self.current_button_name = button.text()
            self._sync_stage_chrome()
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
        self.status_pill.set_busy(True)
        self.session_worker_row.set_value(f"{len(self.active_workers)} active")
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
            self.session_worker_row.set_value(f"{len(self.active_workers)} active")
            if not self.active_workers:
                self.status_label.setText("Ready")
                self.status_pill.set_busy(False)
                self.unsetCursor()

        worker.signals.succeeded.connect(handle_success)
        worker.signals.failed.connect(handle_failure)
        worker.signals.finished.connect(handle_finished)
        self.thread_pool.start(worker)

    def show_diagnostics(self):
        DiagnosticsDialog(self).exec()

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
        names = self.button_name_map.get(selected_option) or []
        self.stage_rail.set_names(names)
        self.stage_rail.count_label.setText(str(len(names)))
        self._sync_stage_chrome()
