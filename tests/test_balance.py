from __future__ import annotations

from pathlib import Path

from car_damage.balance import build_balanced_train_set


def test_balanced_dataset_repeats_minority_and_removes_zero_area_boxes(tmp_path: Path) -> None:
    images = tmp_path / "source" / "images"
    labels = tmp_path / "source" / "labels"
    images.mkdir(parents=True)
    labels.mkdir(parents=True)
    (images / "major.jpg").write_bytes(b"major")
    (images / "minor.jpg").write_bytes(b"minor")
    (labels / "major.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    (labels / "minor.txt").write_text(
        "1 0.5 0.5 0.1 0.1\n1 0.5 0.5 0.0 0.1\n", encoding="utf-8"
    )

    result = build_balanced_train_set(images, labels, tmp_path / "balanced", minority_factor=3)

    assert result.source_images == 2
    assert result.output_images == 4
    assert result.minority_images == 1
    assert result.removed_boxes == 1
    output_labels = sorted((tmp_path / "balanced" / "train" / "labels").glob("*.txt"))
    assert len(output_labels) == 4
    assert all(" 0.0 " not in path.read_text(encoding="utf-8") for path in output_labels)


def test_balanced_dataset_rejects_nonempty_output(tmp_path: Path) -> None:
    images = tmp_path / "source" / "images"
    labels = tmp_path / "source" / "labels"
    images.mkdir(parents=True)
    labels.mkdir(parents=True)
    (images / "one.jpg").write_bytes(b"one")
    (labels / "one.txt").write_text("0 0.5 0.5 0.2 0.2\n", encoding="utf-8")
    output = tmp_path / "balanced"
    (output / "train" / "images").mkdir(parents=True)
    (output / "train" / "labels").mkdir(parents=True)
    (output / "train" / "images" / "existing.jpg").write_bytes(b"existing")

    try:
        build_balanced_train_set(images, labels, output)
    except FileExistsError:
        pass
    else:
        raise AssertionError("expected nonempty output to be rejected")
