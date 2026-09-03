from __future__ import annotations

from pathlib import Path

import pytest

from car_damage.config import ConfigError, load_dataset_config, load_train_config, prepare_runtime_data_yaml
from car_damage.paths import PROJECT_ROOT, resolve_project_path


def test_project_path_is_independent_of_working_directory(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    assert resolve_project_path("configs/data.yaml") == PROJECT_ROOT / "configs/data.yaml"


def test_dataset_config_resolves_existing_dataset() -> None:
    config = load_dataset_config()
    assert config.dataset_root.name == "车损车身数据集"
    assert config.train_images.is_dir()
    assert config.val_images.is_dir()
    assert config.names == {0: "dent", 1: "crack", 2: "scratch"}


def test_train_defaults() -> None:
    config = load_train_config()
    assert config["model"] == "yolo26s.pt"
    assert config["epochs"] == 150
    assert config["imgsz"] == 640
    assert config["batch"] == -1


def test_runtime_yaml_uses_absolute_dataset_path(tmp_path: Path) -> None:
    output = tmp_path / "data.yaml"
    prepare_runtime_data_yaml(output=output)
    text = output.read_text(encoding="utf-8")
    assert "车损车身数据集" in text
    assert "train/images" in text


def test_runtime_yaml_allows_validation_outside_dataset_root(tmp_path: Path) -> None:
    train_root = tmp_path / "balanced"
    validation = tmp_path / "original" / "val" / "images"
    (train_root / "train" / "images").mkdir(parents=True)
    validation.mkdir(parents=True)
    config = tmp_path / "data.yaml"
    config.write_text(
        "\n".join(
            [
                f"path: {train_root.as_posix()}",
                "train: train/images",
                f"val: {validation.as_posix()}",
                "names:",
                "  0: defect",
            ]
        ),
        encoding="utf-8",
    )
    output = tmp_path / "runtime.yaml"

    prepare_runtime_data_yaml(config, output)

    text = output.read_text(encoding="utf-8")
    assert f"val: {validation.as_posix()}" in text


def test_invalid_yaml_shape_raises(tmp_path: Path) -> None:
    config = tmp_path / "invalid.yaml"
    config.write_text("- item\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_dataset_config(config)
