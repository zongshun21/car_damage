from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QStandardPaths, QUrl
from PyQt6.QtGui import QDesktopServices


def user_data_dir() -> Path:
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    path = Path(location) if location else Path.home() / "AppData" / "Local" / "CarDamagePlatform"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_output_dir() -> Path:
    location = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    root = Path(location) if location else Path.home() / "Documents"
    return root / "CarDamageResults"


def open_local_path(path: str | Path) -> bool:
    target = Path(path).resolve()
    return target.exists() and QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))
