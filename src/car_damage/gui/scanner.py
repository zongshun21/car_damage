from __future__ import annotations

from pathlib import Path

from car_damage.dataset import IMAGE_SUFFIXES


def scan_images(source: str | Path) -> list[Path]:
    path = Path(source)
    if path.is_file():
        return [path] if path.suffix.lower() in IMAGE_SUFFIXES else []
    if not path.is_dir():
        return []
    return sorted(
        (item for item in path.iterdir() if item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES),
        key=lambda item: item.name.lower(),
    )

