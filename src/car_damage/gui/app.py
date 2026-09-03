from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow
from .bootstrap import write_startup_log
from .theme import APP_STYLESHEET


def create_application(argv: list[str] | None = None) -> QApplication:
    existing = QApplication.instance()
    app = existing if isinstance(existing, QApplication) else QApplication(argv or sys.argv)
    app.setApplicationName("车辆车身缺陷智能检测平台")
    app.setOrganizationName("兰州石化职业技术大学")
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setStyleSheet(APP_STYLESHEET)
    return app


def run(smoke_test: bool = False) -> int:
    app = create_application()
    write_startup_log(f"QApplication created platform={QGuiApplication.platformName()}")
    window = MainWindow()
    screen = app.primaryScreen()
    if screen is not None:
        available = screen.availableGeometry()
        width = min(1440, max(960, int(available.width() * 0.94)))
        height = min(900, max(620, int(available.height() * 0.92)))
        window.resize(width, height)
        frame = window.frameGeometry()
        frame.moveCenter(available.center())
        window.move(frame.topLeft())
        write_startup_log(
            f"screen={available.width()}x{available.height()} window={width}x{height} "
            f"position={frame.x()},{frame.y()}"
        )
    window.showNormal()
    window.raise_()
    window.activateWindow()
    app._car_damage_window = window  # type: ignore[attr-defined]

    def bring_to_front() -> None:
        if window.isMinimized():
            window.showNormal()
        window.raise_()
        window.activateWindow()
        write_startup_log(
            f"window visible={window.isVisible()} active={window.isActiveWindow()} "
            f"winId={int(window.winId())}"
        )

    QTimer.singleShot(250, bring_to_front)
    if smoke_test:
        QTimer.singleShot(800, app.quit)
    return app.exec()
