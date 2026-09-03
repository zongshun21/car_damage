from __future__ import annotations

from pathlib import Path

from car_damage.two_class import build_two_class_dataset


def _make_split(root: Path, split: str) -> None:
    images = root / split / "images"
    labels = root / split / "labels"
    images.mkdir(parents=True)
    labels.mkdir(parents=True)
    for stem in ("mixed", "crack_only", "background"):
        (images / f"{stem}.jpg").write_bytes(stem.encode())
    (labels / "mixed.txt").write_text(
        "0 0.5 0.5 0.2 0.2\n"
        "1 0.4 0.4 0.1 0.1\n"
        "2 0.6 0.6 0.3 0.3\n"
        "2 0.5 0.5 0.0 0.2\n",
        encoding="utf-8",
    )
    (labels / "crack_only.txt").write_text("1 0.5 0.5 0.1 0.1\n", encoding="utf-8")
    (labels / "background.txt").write_text("", encoding="utf-8")


def test_two_class_dataset_drops_crack_and_remaps_scratch(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _make_split(source, "train")
    _make_split(source, "val")

    result = build_two_class_dataset(source, tmp_path / "derived")

    assert result.images == 6
    assert result.kept_boxes == 4
    assert result.dropped_class_boxes == 4
    assert result.removed_invalid_boxes == 2
    for split in ("train", "val"):
        mixed = (tmp_path / "derived" / split / "labels" / "mixed.txt").read_text()
        assert mixed == "0 0.5 0.5 0.2 0.2\n1 0.6 0.6 0.3 0.3\n"
        assert (tmp_path / "derived" / split / "labels" / "crack_only.txt").read_text() == ""
        assert len(list((tmp_path / "derived" / split / "images").glob("*.jpg"))) == 3


def test_two_class_dataset_rejects_nonempty_output(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _make_split(source, "train")
    _make_split(source, "val")
    output = tmp_path / "derived"
    (output / "train" / "images").mkdir(parents=True)
    (output / "train" / "images" / "existing.jpg").write_bytes(b"existing")

    try:
        build_two_class_dataset(source, output)
    except FileExistsError:
        pass
    else:
        raise AssertionError("expected nonempty output to be rejected")
