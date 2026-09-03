from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import MutableMapping


def prepare_qt_environment(
    environment: MutableMapping[str, str] | None = None,
    *,
    platform_name: str | None = None,
    allow_offscreen: bool = False,
) -> None:
    """Configure Qt before PyQt6 is imported.

    Some Windows hosts establish DPI awareness before Qt starts. Asking Qt to
    replace that context then fails with access denied. Let Windows keep the
    existing context and handle logical scaling through Qt.
    """
    env = environment if environment is not None else os.environ
    platform = platform_name or sys.platform
    if platform != "win32":
        return
    current = env.get("QT_QPA_PLATFORM", "").strip().lower()
    if not current or (current == "offscreen" and not allow_offscreen):
        env["QT_QPA_PLATFORM"] = "windows:dpiawareness=0"
    env.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")


def startup_log_path(environment: MutableMapping[str, str] | None = None) -> Path:
    env = environment if environment is not None else os.environ
    base = Path(env.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    directory = base / "LZPU" / "CarDamagePlatform"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "startup.log"


def write_startup_log(message: str) -> None:
    try:
        with startup_log_path().open("a", encoding="utf-8") as handle:
            handle.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | {message}\n")
    except OSError:
        pass
