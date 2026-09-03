from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from car_damage.paths import PROJECT_ROOT

from .history import HistoryStore
from .model_registry import ModelRegistry
from .pages.dashboard import DashboardPage
from .pages.detection import DetectionPage
from .desktop import user_data_dir
from .settings import AppSettings
from .theme import COLORS


class MainWindow(QMainWindow):
    def __init__(self, settings_path: Path | None = None, history_path: Path | None = None) -> None:
        super().__init__()
        self.setWindowTitle("兰州石化职业技术大学 - 车辆车身缺陷智能检测平台")
        self.resize(1440, 900)
        self.setMinimumSize(960, 620)
        self.registry = ModelRegistry(PROJECT_ROOT / "models")
        self.settings_store = AppSettings(settings_path)
        self.history_store = HistoryStore(history_path or user_data_dir() / "gui_history.db")

        root = QWidget()
        root.setObjectName("AppRoot")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        right.addWidget(self._build_topbar())
        self.stack = QStackedWidget()
        self.dashboard = DashboardPage(self.registry, self.history_store, self.settings_store)
        self.detection = DetectionPage(self.registry, self.history_store, self.settings_store)
        for page in (self.dashboard, self.detection):
            self.stack.addWidget(page)
        right.addWidget(self.stack, 1)
        layout.addLayout(right, 1)
        self.setCentralWidget(root)
        self.statusBar().showMessage("系统就绪 · 本地推理 · 数据不会上传")

        self.detection.history_changed.connect(self._refresh_history)
        self.detection.model_selection_changed.connect(
            lambda name: self.model_badge.setText(f"模型：{name}")
        )
        self.nav_buttons[0].setChecked(True)
        self._refresh_model_badge()

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(235)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 24, 18, 18)
        brand_icon = QLabel("◈  LZPU · AI")
        brand_icon.setStyleSheet(f"color:{COLORS['cyan']}; font-size:14px; font-weight:700;")
        school = QLabel("兰州石化职业技术大学")
        school.setObjectName("BrandTitle")
        school.setWordWrap(True)
        platform = QLabel("车辆车身缺陷\n智能检测平台")
        platform.setObjectName("BrandSchool")
        layout.addWidget(brand_icon)
        layout.addSpacing(8)
        layout.addWidget(school)
        layout.addWidget(platform)
        layout.addSpacing(30)
        self.nav_buttons: list[QPushButton] = []
        labels = ["▣  首页概览", "◎  智能检测"]
        for index, text in enumerate(labels):
            button = QPushButton(text)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked, page=index: self.navigate(page))
            layout.addWidget(button)
            self.nav_buttons.append(button)
        layout.addStretch()
        version = QLabel("YOLO26s · PyQt6\nVersion 1.5.0")
        version.setObjectName("BrandSchool")
        layout.addWidget(version)
        return sidebar

    def _build_topbar(self) -> QFrame:
        topbar = QFrame()
        topbar.setObjectName("Topbar")
        topbar.setFixedHeight(70)
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(24, 0, 24, 0)
        title = QLabel("车辆车身缺陷智能检测平台")
        title.setStyleSheet("font-size:18px; font-weight:700; color:#17233C;")
        layout.addWidget(title)
        layout.addStretch()
        self.model_badge = QLabel()
        self.model_badge.setStyleSheet(
            f"background:#E8F3FF; color:{COLORS['primary']}; padding:7px 12px; border-radius:8px; font-weight:600;"
        )
        self.device_badge = QLabel("● 设备：自动选择")
        self.device_badge.setStyleSheet(
            f"background:#E8FAF4; color:{COLORS['success']}; padding:7px 12px; border-radius:8px;"
        )
        layout.addWidget(self.model_badge)
        layout.addSpacing(8)
        layout.addWidget(self.device_badge)
        return topbar

    def navigate(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for position, button in enumerate(self.nav_buttons):
            button.setChecked(position == index)
        if index == 0:
            self.dashboard.refresh()

    def _refresh_model_badge(self) -> None:
        default = self.settings_store.get("default_model")
        model = next((item for item in self.registry.all() if item.id == default), None)
        self.model_badge.setText(f"模型：{model.display_name if model else '未选择'}")
        self.device_badge.setText(f"● 设备：{self.settings_store.get('device')}")

    def _refresh_models(self) -> None:
        self.detection.refresh_models()
        self.dashboard.refresh()
        self._refresh_model_badge()

    def _refresh_history(self) -> None:
        self.dashboard.refresh()

    def closeEvent(self, event) -> None:
        if self.detection.thread and self.detection.thread.isRunning():
            self.detection.stop_detection()
            self.statusBar().showMessage("正在安全停止检测，完成当前图片后将退出……")
            self.detection.thread.finished.connect(self.close)
            event.ignore()
            return
        event.accept()
