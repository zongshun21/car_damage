from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSettings

from .desktop import default_output_dir


class AppSettings:
    DEFAULTS = {
        "default_model": "yolo26s-two-class",
        "device": "auto",
        "confidence": 0.25,
        "iou": 0.70,
        "imgsz": 768,
        "output_dir": "",
    }

    def __init__(self, path: Path | None = None) -> None:
        self._settings = (
            QSettings(str(path), QSettings.Format.IniFormat)
            if path
            else QSettings("LZPU", "CarDamagePlatform")
        )

    def get(self, key: str):
        default = self.DEFAULTS[key]
        if key == "output_dir" and not default:
            default = str(default_output_dir())
        value = self._settings.value(key, default)
        if isinstance(default, float):
            return float(value)
        if isinstance(default, int):
            return int(value)
        return str(value)

    def set(self, key: str, value) -> None:
        self._settings.setValue(key, value)
        self._settings.sync()

    def reset(self) -> None:
        self._settings.clear()
        self._settings.sync()
