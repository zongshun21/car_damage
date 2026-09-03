from __future__ import annotations

import math
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

from PIL import Image

from .config import DatasetConfig, load_dataset_config


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


@dataclass
class SplitReport:
    split: str
    images: int = 0
    labels: int = 0
    objects: int = 0
    empty_labels: int = 0
    class_counts: dict[int, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class DatasetReport:
    dataset_root: str
    class_names: dict[int, str]
    splits: list[SplitReport]

    @property
    def ok(self) -> bool:
        return all(split.ok for split in self.splits)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "dataset_root": self.dataset_root,
            "class_names": self.class_names,
            "splits": [asdict(split) | {"ok": split.ok} for split in self.splits],
        }


def _files_by_stem(directory: Path, suffixes: Iterable[str]) -> dict[str, Path]:
    allowed = {suffix.lower() for suffix in suffixes}
    if not directory.is_dir():
        return {}
    return {
        item.stem: item
        for item in directory.iterdir()
        if item.is_file() and item.suffix.lower() in allowed
    }


def _check_image(path: Path) -> str | None:
    try:
        with Image.open(path) as image:
            image.verify()
        return None
    except Exception as exc:  # Pillow exposes several decoder-specific errors.
        return f"图片无法读取: {path}: {exc}"


def _parse_label(
    path: Path, num_classes: int
) -> tuple[Counter[int], list[str], list[str], bool]:
    counts: Counter[int] = Counter()
    errors: list[str] = []
    warnings: list[str] = []
    nonempty = False
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        return counts, [f"标签无法读取: {path}: {exc}"], warnings, nonempty

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        nonempty = True
        parts = stripped.split()
        prefix = f"{path}:{line_number}"
        if len(parts) != 5:
            errors.append(f"{prefix}: 应有5个字段，实际{len(parts)}个")
            continue
        try:
            class_value = float(parts[0])
            coords = [float(value) for value in parts[1:]]
        except ValueError:
            errors.append(f"{prefix}: 包含非数值字段")
            continue
        if not class_value.is_integer():
            errors.append(f"{prefix}: 类别编号不是整数: {parts[0]}")
            continue
        class_id = int(class_value)
        if not 0 <= class_id < num_classes:
            errors.append(f"{prefix}: 类别编号越界: {class_id}")
        if not all(math.isfinite(value) for value in coords):
            errors.append(f"{prefix}: 坐标包含 NaN 或无穷值")
            continue
        x, y, width, height = coords
        if width <= 0 or height <= 0:
            # Ultralytics 8.4.x accepts this row; report it without blocking an otherwise trainable dataset.
            warnings.append(f"{prefix}: 零面积框会被训练器接受，但不会提供有效定位监督")
        # Match Ultralytics 8.4.x verification tolerance.
        if max(coords) > 1.01 or min(coords) < -0.01:
            errors.append(f"{prefix}: 坐标超出 Ultralytics 容差: {coords}")
        if 0 <= class_id < num_classes:
            counts[class_id] += 1
    return counts, errors, warnings, nonempty


def check_split(
    split: str,
    images_dir: Path,
    num_classes: int,
    verify_images: bool = True,
) -> SplitReport:
    report = SplitReport(split=split)
    labels_dir = images_dir.parent / "labels"
    if not images_dir.is_dir():
        report.errors.append(f"图片目录不存在: {images_dir}")
        return report
    if not labels_dir.is_dir():
        report.errors.append(f"标签目录不存在: {labels_dir}")
        return report

    images = _files_by_stem(images_dir, IMAGE_SUFFIXES)
    labels = _files_by_stem(labels_dir, {".txt"})
    report.images = len(images)
    report.labels = len(labels)

    for stem in sorted(set(images) - set(labels)):
        report.errors.append(f"缺少标签: {images[stem]}")
    for stem in sorted(set(labels) - set(images)):
        report.errors.append(f"缺少图片: {labels[stem]}")

    class_counts: Counter[int] = Counter()
    for stem in sorted(set(images) & set(labels)):
        if verify_images:
            image_error = _check_image(images[stem])
            if image_error:
                report.errors.append(image_error)
        counts, errors, warnings, nonempty = _parse_label(labels[stem], num_classes)
        class_counts.update(counts)
        report.objects += sum(counts.values())
        report.errors.extend(errors)
        report.warnings.extend(warnings)
        if not nonempty:
            report.empty_labels += 1

    report.class_counts = dict(sorted(class_counts.items()))
    return report


def check_dataset(
    config_path: str | Path = "configs/data.yaml",
    verify_images: bool = True,
) -> DatasetReport:
    config: DatasetConfig = load_dataset_config(config_path)
    splits = [
        check_split("train", config.train_images, len(config.names), verify_images),
        check_split("val", config.val_images, len(config.names), verify_images),
    ]
    return DatasetReport(
        dataset_root=str(config.dataset_root),
        class_names=config.names,
        splits=splits,
    )
