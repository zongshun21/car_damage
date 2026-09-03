from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtWidgets import QListView

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from car_damage.gui.app import create_application
from car_damage.gui.main_window import MainWindow


def test_main_window_builds_all_pages(tmp_path: Path) -> None:
    app = create_application(["test"])
    window = MainWindow(tmp_path / "settings.ini", tmp_path / "history.db")
    assert window.stack.count() == 2
    assert "兰州石化职业技术大学" in window.windowTitle()
    assert window.detection.model_combo.count() >= 2
    assert "mAP" not in window.detection.model_combo.itemText(0)
    assert hasattr(window.detection, "preview_view")
    assert window.detection.start_button.text() == "缺陷检测"
    assert window.detection.main_splitter.count() == 2
    assert window.detection.image_list.flow() == QListView.Flow.TopToBottom
    assert window.detection.right_panel.minimumWidth() >= 280
    assert window.detection.right_panel.maximumWidth() <= 380
    assert window.detection.preview_view.minimumHeight() >= 420
    assert window.detection.settings_card.minimumHeight() >= 230
    assert all(widget.minimumHeight() >= 34 for widget in window.detection.setting_inputs)
    assert not hasattr(window.dashboard, "map_card")
    window.close()
    app.processEvents()


def test_selecting_source_waits_for_manual_detection(tmp_path: Path) -> None:
    app = create_application(["test-manual-detect"])
    window = MainWindow(tmp_path / "settings.ini", tmp_path / "history.db")
    image = tmp_path / "car.jpg"
    image.write_bytes(b"test")
    calls = []
    window.detection.start_detection = lambda: calls.append("started")

    window.detection.set_source(image)
    app.processEvents()

    assert calls == []
    assert window.detection.preview_title.text() == "原始图片"
    window.close()
    app.processEvents()
