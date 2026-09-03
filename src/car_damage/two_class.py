from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


IMAGE_SUFFIXES = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


@dataclass(frozen=True)
class TwoClassResult:
    images: int
    kept_boxes: int
    dropped_class_boxes: int
    removed_invalid_boxes: int


def _link_or_copy(source: Path, destination: Path) -> None:
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def _rewrite_label(text: str) -> tuple[str, int, int, int]:
    lines: list[str] = []
    kept = dropped = invalid = 0
    for raw_line in text.splitlines():
        fields = raw_line.strip().split()
        if len(fields) != 5:
            invalid += 1
            continue
        try:
            class_id = int(fields[0])
            coordinates = [float(value) for value in fields[1:]]
        except ValueError:
            invalid += 1
            continue
        if coordinates[2] <= 0 or coordinates[3] <= 0:
            invalid += 1
            continue
        if class_id == 1:
            dropped += 1
            continue
        if class_id not in (0, 2):
            invalid += 1
            continue
        new_class = 0 if class_id == 0 else 1
        lines.append(" ".join([str(new_class), *fields[1:]]))
        kept += 1
    rewritten = "\n".join(lines) + ("\n" if lines else "")
    return rewritten, kept, dropped, invalid


def build_two_class_dataset(source_root: Path, output_root: Path) -> TwoClassResult:
    """Create a dent/scratch derivative while leaving the source untouched."""
    for split in ("train", "val"):
        source_images = source_root / split / "images"
        source_labels = source_root / split / "labels"
        if not source_images.is_dir() or not source_labels.is_dir():
            raise FileNotFoundError(f"missing source split: {split}")
        output_images = output_root / split / "images"
        output_labels = output_root / split / "labels"
        if output_images.exists() and any(output_images.iterdir()):
            raise FileExistsError(f"two-class output is not empty: {output_root}")
        if output_labels.exists() and any(output_labels.iterdir()):
            raise FileExistsError(f"two-class output is not empty: {output_root}")

    total_images = kept_boxes = dropped_boxes = invalid_boxes = 0
    for split in ("train", "val"):
        source_images = source_root / split / "images"
        source_labels = source_root / split / "labels"
        images = {
            path.stem: path
            for path in source_images.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        }
        labels = {path.stem: path for path in source_labels.glob("*.txt")}
        if set(images) != set(labels):
            raise ValueError(
                f"image/label mismatch in {split}: "
                f"missing_labels={sorted(set(images) - set(labels))[:5]}, "
                f"missing_images={sorted(set(labels) - set(images))[:5]}"
            )

        output_images = output_root / split / "images"
        output_labels = output_root / split / "labels"
        output_images.mkdir(parents=True, exist_ok=True)
        output_labels.mkdir(parents=True, exist_ok=True)
        for stem in sorted(images):
            image = images[stem]
            rewritten, kept, dropped, invalid = _rewrite_label(
                labels[stem].read_text(encoding="utf-8")
            )
            _link_or_copy(image, output_images / f"{stem}{image.suffix.lower()}")
            (output_labels / f"{stem}.txt").write_text(rewritten, encoding="utf-8")
            total_images += 1
            kept_boxes += kept
            dropped_boxes += dropped
            invalid_boxes += invalid

    return TwoClassResult(total_images, kept_boxes, dropped_boxes, invalid_boxes)
