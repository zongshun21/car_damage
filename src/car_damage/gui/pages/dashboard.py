from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..history import HistoryStore
from ..model_registry import ModelRegistry
from ..settings import AppSettings
from ..theme import COLORS
from ..widgets import MetricCard, StatBars, page_heading


class DashboardPage(QWidget):
    def __init__(self, registry: ModelRegistry, history: HistoryStore, settings: AppSettings) -> None:
        super().__init__()
        self.registry = registry
        self.history = history
        self.settings = settings
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(16)
        root.addLayout(page_heading("首页概览", "车辆缺陷智能识别系统运行概况"))

        self.model_card = MetricCard("当前模型", "--", COLORS["primary"])
        self.tasks_card = MetricCard("累计检测任务", "0", COLORS["orange"])
        self.images_card = MetricCard("累计处理图片", "0", COLORS["success"])
        cards = QGridLayout()
        for index, card in enumerate((self.model_card, self.tasks_card, self.images_card)):
            cards.addWidget(card, 0, index)
        root.addLayout(cards)

        lower = QHBoxLayout()
        chart_card = QFrame()
        chart_card.setObjectName("Card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.addWidget(QLabel("累计缺陷分布"))
        self.chart = StatBars()
        chart_layout.addWidget(self.chart)
        lower.addWidget(chart_card, 2)
        recent_card = QFrame()
        recent_card.setObjectName("Card")
        recent_layout = QVBoxLayout(recent_card)
        recent_header = QHBoxLayout()
        recent_header.addWidget(QLabel("最近检测任务"))
        recent_header.addStretch()
        self.delete_button = QPushButton("删除选中记录")
        self.delete_button.setProperty("secondary", True)
        self.clear_history_button = QPushButton("清空全部统计")
        self.clear_history_button.setProperty("danger", True)
        recent_header.addWidget(self.delete_button)
        recent_header.addWidget(self.clear_history_button)
        recent_layout.addLayout(recent_header)
        self.recent = QTableWidget(0, 3)
        self.recent.setHorizontalHeaderLabels(["时间", "模型", "图片数"])
        self.recent.horizontalHeader().setStretchLastSection(True)
        self.recent.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.recent.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        recent_layout.addWidget(self.recent)
        lower.addWidget(recent_card, 3)
        root.addLayout(lower, 1)
        self.delete_button.clicked.connect(self.delete_selected_task)
        self.clear_history_button.clicked.connect(self.clear_history)
        self.refresh()

    def refresh(self) -> None:
        model_id = self.settings.get("default_model")
        model = next((item for item in self.registry.all() if item.id == model_id), None)
        if model:
            self.model_card.set_value(model.display_name.replace("YOLO26s-", ""))
        totals = self.history.totals()
        self.tasks_card.set_value(str(totals["tasks"]))
        self.images_card.set_value(str(totals["images"]))
        tasks = self.history.list_tasks()[:6]
        self.recent.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            for column, value in enumerate((task.created_at, task.model_name, task.completed_images)):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, task.id)
                self.recent.setItem(row, column, item)

        counts = {"凹陷": 0, "裂纹": 0, "划痕": 0}
        for task in self.history.list_tasks():
            for result in self.history.task_results(task.id):
                for detection in result.detections:
                    counts[detection.display_name] = counts.get(detection.display_name, 0) + 1
        self.chart.set_values(counts)

    def delete_selected_task(self) -> None:
        row = self.recent.currentRow()
        item = self.recent.item(row, 0) if row >= 0 else None
        task_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not task_id:
            QMessageBox.information(self, "请选择记录", "请先在最近检测任务中选择一条记录。")
            return
        self.history.delete_task(str(task_id))
        self.refresh()

    def clear_history(self) -> None:
        if not self.history.list_tasks():
            return
        answer = QMessageBox.question(
            self,
            "确认清空",
            "确定要清空全部检测历史和首页统计吗？此操作不会删除检测结果图片。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.history.clear_all()
            self.refresh()
