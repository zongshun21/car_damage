from __future__ import annotations

import csv
import time
import uuid
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QListView, QListWidget, QMessageBox, QProgressBar, QPushButton, QSpinBox,
    QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..history import HistoryStore
from ..desktop import open_local_path
from ..inference import InferenceService
from ..model_registry import ModelRegistry
from ..models import ImageResult, ModelSpec, TaskSummary
from ..scanner import scan_images
from ..settings import AppSettings
from ..widgets import ImageView, secondary_button
from ..workers import InferenceWorker


class DetectionPage(QWidget):
    history_changed = pyqtSignal()
    model_selection_changed = pyqtSignal(str)

    def __init__(self, registry: ModelRegistry, history: HistoryStore, settings: AppSettings) -> None:
        super().__init__()
        self.registry = registry
        self.history = history
        self.settings = settings
        self.service = InferenceService()
        self.images: list[Path] = []
        self.results: dict[str, ImageResult] = {}
        self.current_source = ""
        self.current_output_dir: Path | None = None
        self.started_at = 0.0
        self.processing_ms_total = 0.0
        self.speed_samples = 0
        self.thread: QThread | None = None
        self.worker: InferenceWorker | None = None
        self._build_ui()
        self.refresh_models()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        self.model_combo = QComboBox()
        self.device_combo = QComboBox()
        self.device_combo.addItems(["auto", "0", "cpu"])
        self.confidence = QDoubleSpinBox()
        self.confidence.setRange(0.01, 0.99)
        self.confidence.setSingleStep(0.05)
        self.confidence.setValue(self.settings.get("confidence"))
        self.iou = QDoubleSpinBox()
        self.iou.setRange(0.1, 0.95)
        self.iou.setValue(self.settings.get("iou"))
        self.imgsz = QSpinBox()
        self.imgsz.setRange(320, 1280)
        self.imgsz.setSingleStep(32)
        self.imgsz.setValue(self.settings.get("imgsz"))

        action_card = QFrame()
        action_card.setObjectName("Card")
        action_card.setMaximumHeight(58)
        buttons = QHBoxLayout(action_card)
        buttons.setContentsMargins(10, 6, 10, 6)
        buttons.setSpacing(8)
        self.open_image_button = secondary_button("打开图片")
        self.open_folder_button = secondary_button("打开文件夹")
        self.import_model_button = secondary_button("导入模型")
        self.clear_button = secondary_button("清空")
        self.start_button = QPushButton("缺陷检测")
        self.stop_button = QPushButton("停止")
        self.stop_button.setProperty("danger", True)
        self.stop_button.setEnabled(False)
        self.output_button = secondary_button("打开输出目录")
        self.export_button = secondary_button("导出 CSV")
        self.output_button.setEnabled(False)
        self.export_button.setEnabled(False)
        for button in (
            self.open_image_button, self.open_folder_button, self.import_model_button,
            self.clear_button, self.start_button, self.stop_button,
            self.output_button, self.export_button,
        ):
            buttons.addWidget(button)
        buttons.addStretch()
        root.addWidget(action_card)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        preview_card = QFrame()
        preview_card.setObjectName("Card")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(10, 8, 10, 10)
        self.preview_title = QLabel("图片预览")
        self.preview_view = ImageView("请选择待检测图片")
        self.preview_view.setMinimumHeight(420)
        preview_layout.addWidget(self.preview_title)
        preview_layout.addWidget(self.preview_view, 1)

        self.right_panel = QWidget()
        self.right_panel.setMinimumWidth(290)
        self.right_panel.setMaximumWidth(370)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self.settings_card = QFrame()
        self.settings_card.setObjectName("Card")
        self.settings_card.setMinimumHeight(245)
        settings_layout = QGridLayout(self.settings_card)
        settings_layout.setContentsMargins(12, 9, 12, 10)
        settings_layout.setHorizontalSpacing(8)
        settings_layout.setVerticalSpacing(4)
        settings_title = QLabel("检测设置")
        settings_layout.addWidget(settings_title, 0, 0, 1, 2)
        settings_layout.addWidget(QLabel("模型"), 1, 0, 1, 2)
        settings_layout.addWidget(self.model_combo, 2, 0, 1, 2)
        settings_layout.addWidget(QLabel("设备"), 3, 0)
        settings_layout.addWidget(QLabel("置信度"), 3, 1)
        settings_layout.addWidget(self.device_combo, 4, 0)
        settings_layout.addWidget(self.confidence, 4, 1)
        settings_layout.addWidget(QLabel("IoU"), 5, 0)
        settings_layout.addWidget(QLabel("输入尺寸"), 5, 1)
        settings_layout.addWidget(self.iou, 6, 0)
        settings_layout.addWidget(self.imgsz, 6, 1)
        self.setting_inputs = [
            self.model_combo, self.device_combo, self.confidence, self.iou, self.imgsz
        ]
        for widget in self.setting_inputs:
            widget.setMinimumHeight(36)
        for row, height in ((0, 22), (1, 20), (2, 36), (3, 20), (4, 36), (5, 20), (6, 36)):
            settings_layout.setRowMinimumHeight(row, height)
        right_layout.addWidget(self.settings_card)

        queue_card = QFrame()
        queue_card.setObjectName("Card")
        queue_layout = QVBoxLayout(queue_card)
        queue_layout.setContentsMargins(12, 8, 12, 8)
        queue_layout.setSpacing(4)
        queue_layout.addWidget(QLabel("图片任务"))
        self.image_list = QListWidget()
        self.image_list.setFlow(QListView.Flow.TopToBottom)
        self.image_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.image_list.setSpacing(3)
        self.image_list.setMinimumHeight(120)
        queue_layout.addWidget(self.image_list)
        right_layout.addWidget(queue_card, 2)

        self.details_card = QFrame()
        self.details_card.setObjectName("Card")
        details_layout = QVBoxLayout(self.details_card)
        details_layout.setContentsMargins(12, 8, 12, 8)
        details_layout.setSpacing(5)
        details_layout.addWidget(QLabel("当前图片检测明细"))
        details_body = QHBoxLayout()
        self.result_table = QTableWidget(0, 3)
        self.result_table.setHorizontalHeaderLabels(["类别", "置信度", "边界框"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.result_table.setColumnWidth(0, 68)
        self.result_table.setColumnWidth(1, 72)
        details_body.addWidget(self.result_table)
        self.summary_label = QLabel("尚未开始检测")
        self.summary_label.setWordWrap(True)
        details_layout.addLayout(details_body)
        details_layout.addWidget(self.summary_label)
        right_layout.addWidget(self.details_card, 3)

        self.main_splitter.addWidget(preview_card)
        self.main_splitter.addWidget(self.right_panel)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 0)
        self.main_splitter.setCollapsible(0, False)
        self.main_splitter.setCollapsible(1, False)
        self.main_splitter.setSizes([900, 330])
        root.addWidget(self.main_splitter, 1)

        progress_row = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.status = QLabel("就绪")
        self.status.setMinimumWidth(250)
        self.speed_label = QLabel("速度：-- FPS")
        self.speed_label.setMinimumWidth(165)
        progress_row.addWidget(self.progress, 1)
        progress_row.addWidget(self.speed_label)
        progress_row.addWidget(self.status)
        root.addLayout(progress_row)

        self.open_image_button.clicked.connect(self.open_image)
        self.open_folder_button.clicked.connect(self.open_folder)
        self.import_model_button.clicked.connect(self.import_model)
        self.clear_button.clicked.connect(self.clear_task)
        self.start_button.clicked.connect(self.start_detection)
        self.stop_button.clicked.connect(self.stop_detection)
        self.output_button.clicked.connect(self.open_output)
        self.export_button.clicked.connect(self.export_csv)
        self.image_list.currentRowChanged.connect(self.show_image)
        self.model_combo.currentIndexChanged.connect(self._emit_model_selection)

    def _emit_model_selection(self) -> None:
        model = self.selected_model()
        if model:
            self.settings.set("default_model", model.id)
            self.model_selection_changed.emit(model.display_name)

    def refresh_models(self) -> None:
        selected = self.model_combo.currentData() if self.model_combo.count() else self.settings.get("default_model")
        self.model_combo.clear()
        for model in self.registry.available():
            self.model_combo.addItem(model.display_name, model.id)
        index = self.model_combo.findData(selected)
        self.model_combo.setCurrentIndex(max(0, index))
        self._emit_model_selection()

    def selected_model(self) -> ModelSpec | None:
        model_id = self.model_combo.currentData()
        return next((item for item in self.registry.available() if item.id == model_id), None)

    def import_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "导入 YOLO 模型", "", "PyTorch 权重 (*.pt)")
        if not path:
            return
        try:
            model = self.registry.import_model(Path(path))
            self.refresh_models()
            self.model_combo.setCurrentIndex(self.model_combo.findData(model.id))
            QMessageBox.information(self, "导入成功", f"已导入模型：{model.display_name}")
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "导入失败", str(exc))

    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择车辆图片", "", "图片 (*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff)")
        if path:
            self.set_source(Path(path))

    def open_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if path:
            self.set_source(Path(path))

    def set_source(self, source: Path) -> None:
        images = scan_images(source)
        if not images:
            QMessageBox.warning(self, "没有图片", "所选位置没有支持的图片文件。")
            return
        self.clear_task()
        self.current_source = str(source)
        self.images = images
        self.image_list.addItems([f"○  {item.name}" for item in images])
        self.image_list.setCurrentRow(0)
        self.status.setText(f"已载入 {len(images)} 张图片，请点击“缺陷检测”")

    def clear_task(self) -> None:
        if self.thread and self.thread.isRunning():
            return
        self.images = []
        self.results = {}
        self.current_source = ""
        self.current_output_dir = None
        self.image_list.clear()
        self.result_table.setRowCount(0)
        self.preview_title.setText("图片预览")
        self.preview_view.clear_image()
        self.progress.setValue(0)
        self.status.setText("就绪")
        self.speed_label.setText("速度：-- FPS")
        self.summary_label.setText("尚未开始检测")
        self.output_button.setEnabled(False)
        self.export_button.setEnabled(False)

    def show_image(self, row: int) -> None:
        if row < 0 or row >= len(self.images):
            return
        source = self.images[row]
        result = self.results.get(str(source))
        self.result_table.setRowCount(0)
        if not result or not result.output_path:
            self.preview_title.setText("原始图片")
            self.preview_view.set_image(source)
            return
        self.preview_title.setText("检测结果")
        self.preview_view.set_image(result.output_path)
        self.result_table.setRowCount(len(result.detections))
        for index, detection in enumerate(result.detections):
            box = ", ".join(str(round(value)) for value in detection.box)
            for column, value in enumerate((detection.display_name, f"{detection.confidence:.1%}", box)):
                self.result_table.setItem(index, column, QTableWidgetItem(value))

    def start_detection(self) -> None:
        model = self.selected_model()
        if not self.images:
            QMessageBox.information(self, "提示", "请先打开一张图片或图片文件夹。")
            return
        if not model:
            QMessageBox.warning(self, "模型不可用", "请选择一个可用的模型。")
            return
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_model = model.id.replace("yolo26s-", "")
        output_root = Path(self.settings.get("output_dir"))
        if not output_root.is_absolute():
            output_root = Path(__file__).resolve().parents[4] / output_root
        self.current_output_dir = output_root / f"{stamp}_{safe_model}"
        self.results = {}
        current_row = self.image_list.currentRow()
        if 0 <= current_row < len(self.images):
            self.preview_title.setText("原始图片")
            self.preview_view.set_image(self.images[current_row])
        self.result_table.setRowCount(0)
        self.started_at = time.perf_counter()
        self.processing_ms_total = 0.0
        self.speed_samples = 0
        self.progress.setValue(0)
        self._set_running(True)
        self.thread = QThread(self)
        self.worker = InferenceWorker(
            self.service, model, self.registry.models_dir, self.images, self.current_output_dir,
            self.device_combo.currentText(), self.confidence.value(), self.iou.value(), self.imgsz.value(),
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.started.connect(self.status.setText)
        self.worker.progress.connect(self.on_progress)
        self.worker.image_done.connect(self.on_image_done)
        self.worker.image_failed.connect(lambda path, error: self.status.setText(f"跳过 {Path(path).name}: {error}"))
        self.worker.fatal_error.connect(lambda error: QMessageBox.critical(self, "检测失败", error))
        self.worker.completed.connect(self.on_completed)
        self.worker.completed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _set_running(self, running: bool) -> None:
        for widget in (
            self.model_combo, self.device_combo, self.confidence, self.iou, self.imgsz,
            self.open_image_button, self.open_folder_button, self.import_model_button,
            self.clear_button, self.start_button,
        ):
            widget.setEnabled(not running)
        self.stop_button.setEnabled(running)

    def on_progress(self, current: int, total: int, result: ImageResult) -> None:
        self.progress.setValue(round(current * 100 / total))
        self.status.setText(f"正在处理 {current}/{total}：{Path(result.source_path).name}")
        if not result.error:
            self.processing_ms_total += result.elapsed_ms
            self.speed_samples += 1
        average_ms = self.processing_ms_total / max(self.speed_samples, 1)
        self.speed_label.setText(f"{1000 / average_ms:.1f} FPS · {average_ms:.1f} ms/张")
        row = next((i for i, item in enumerate(self.images) if str(item) == result.source_path), -1)
        if row >= 0:
            marker = "✓" if not result.error else "!"
            self.image_list.item(row).setText(f"{marker}  {self.images[row].name}")

    def on_image_done(self, result: ImageResult) -> None:
        self.results[result.source_path] = result
        row = next((i for i, item in enumerate(self.images) if str(item) == result.source_path), -1)
        if row >= 0 and row != self.image_list.currentRow():
            self.image_list.setCurrentRow(row)
        elif row >= 0:
            self.show_image(row)

    def on_completed(self, results: list[ImageResult], cancelled: bool) -> None:
        model = self.selected_model()
        elapsed = time.perf_counter() - self.started_at
        successful = [item for item in results if not item.error]
        detections = sum(len(item.detections) for item in successful)
        defect_images = sum(bool(item.detections) for item in successful)
        status = "cancelled" if cancelled else "completed"
        if model and self.current_output_dir:
            summary = TaskSummary(
                id=str(uuid.uuid4()), created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                model_name=model.display_name, source=self.current_source,
                output_dir=str(self.current_output_dir), total_images=len(self.images),
                completed_images=len(successful), defect_images=defect_images,
                total_detections=detections, elapsed_seconds=elapsed, status=status,
            )
            self.history.save_task(summary, results)
        average = sum(d.confidence for item in successful for d in item.detections) / detections if detections else 0
        average_ms = self.processing_ms_total / max(self.speed_samples, 1)
        self.summary_label.setText(
            f"完成图片：{len(successful)}/{len(self.images)}　缺陷图片：{defect_images}　目标总数：{detections}\n"
            f"平均置信度：{average:.1%}　平均速度：{average_ms:.1f} ms/张\n"
            f"推理帧率：{1000 / max(average_ms, 0.001):.1f} FPS　"
            f"总耗时：{elapsed:.2f} 秒"
        )
        self.status.setText("任务已停止" if cancelled else "检测完成")
        self._set_running(False)
        self.output_button.setEnabled(bool(self.current_output_dir and self.current_output_dir.exists()))
        self.export_button.setEnabled(bool(results))
        self.history_changed.emit()
        self.worker = None
        self.thread = None

    def stop_detection(self) -> None:
        if self.worker:
            self.worker.cancel()
            self.status.setText("正在安全停止，请等待当前图片完成……")
            self.stop_button.setEnabled(False)

    def open_output(self) -> None:
        if self.current_output_dir and self.current_output_dir.exists():
            open_local_path(self.current_output_dir)

    def export_csv(self) -> None:
        if not self.results:
            return
        default = str((self.current_output_dir or Path.cwd()) / "detection_report.csv")
        path, _ = QFileDialog.getSaveFileName(self, "导出检测报告", default, "CSV (*.csv)")
        if path:
            with open(path, "w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle)
                writer.writerow(["图片", "输出图片", "类别", "置信度", "边界框", "耗时(ms)"])
                for result in self.results.values():
                    if not result.detections:
                        writer.writerow([result.source_path, result.output_path, "无缺陷", "", "", f"{result.elapsed_ms:.1f}"])
                    for item in result.detections:
                        writer.writerow([result.source_path, result.output_path, item.display_name, f"{item.confidence:.6f}", item.box, f"{result.elapsed_ms:.1f}"])
