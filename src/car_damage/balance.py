from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


@dataclass(frozen=True)
class BalanceResult:
    source_images: int
    output_images: int
    minority_images: int
    removed_boxes: int


def _clean_label(text: str) -> tuple[str, set[int], int]:
    kept: list[str] = []
    classes: set[int] = set()
    removed = 0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) != 5:
            kept.append(line)
            continue
        class_id, _, _, width, height = map(float, fields)
        if width <= 0 or height <= 0:
            removed += 1
            continue
        kept.append(line)
        classes.add(int(class_id))
    return ("\n".join(kept) + ("\n" if kept else ""), classes, removed)


def _link_or_copy(source: Path, destination: Path) -> None:
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def build_balanced_train_set(
    source_images: Path,
    source_labels: Path,
    output_root: Path,
    minority_class: int = 1,
    minority_factor: int = 4,
) -> BalanceResult:
    """Build a training-only dataset with repeated minority-class images.

    Images are hard-linked when possible, while labels are rewritten so invalid
    zero-area boxes do not get amplified by oversampling.
    """
    if minority_factor < 1:
        raise ValueError("minority_factor must be at least 1")

    image_map = {
        path.stem: path
        for path in source_images.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    }
    label_map = {path.stem: path for path in source_labels.glob("*.txt")}
    if set(image_map) != set(label_map):
        missing_labels = sorted(set(image_map) - set(label_map))
        missing_images = sorted(set(label_map) - set(image_map))
        raise ValueError(
            f"image/label mismatch: missing_labels={missing_labels[:5]}, "
            f"missing_images={missing_images[:5]}"
        )

    output_images = output_root / "train" / "images"
    output_labels = output_root / "train" / "labels"
    output_images.mkdir(parents=True, exist_ok=True)
    output_labels.mkdir(parents=True, exist_ok=True)
    if any(output_images.iterdir()) or any(output_labels.iterdir()):
        raise FileExistsError(f"balanced output is not empty: {output_root}")

    minority_images = 0
    removed_boxes = 0
    written = 0
    for stem in sorted(image_map):
        image = image_map[stem]
        cleaned, classes, removed = _clean_label(label_map[stem].read_text(encoding="utf-8"))
        repeats = minority_factor if minority_class in classes else 1
        minority_images += int(minority_class in classes)
        removed_boxes += removed
        for repeat in range(repeats):
            output_stem = stem if repeat == 0 else f"{stem}__minority_{repeat}"
            _link_or_copy(image, output_images / f"{output_stem}{image.suffix.lower()}")
            (output_labels / f"{output_stem}.txt").write_text(cleaned, encoding="utf-8")
            written += 1

    return BalanceResult(
        source_images=len(image_map),
        output_images=written,
        minority_images=minority_images,
        removed_boxes=removed_boxes,
    )
