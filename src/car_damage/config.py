from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .paths import PROJECT_ROOT, resolve_project_path


class ConfigError(ValueError):
    """Raised when a project configuration is invalid."""


@dataclass(frozen=True)
class DatasetConfig:
    config_path: Path
    dataset_root: Path
    train_images: Path
    val_images: Path
    names: dict[int, str]


def load_yaml(path: str | Path) -> dict[str, Any]:
    config_path = resolve_project_path(path)
    if not config_path.is_file():
        raise ConfigError(f"配置文件不存在: {config_path}")
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML 格式错误: {config_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"YAML 顶层必须是映射: {config_path}")
    return data


def load_dataset_config(path: str | Path = "configs/data.yaml") -> DatasetConfig:
    config_path = resolve_project_path(path)
    raw = load_yaml(config_path)
    for key in ("path", "train", "val", "names"):
        if key not in raw:
            raise ConfigError(f"数据配置缺少字段 '{key}': {config_path}")

    root_value = Path(str(raw["path"])).expanduser()
    dataset_root = (
        root_value.resolve()
        if root_value.is_absolute()
        else (config_path.parent / root_value).resolve()
    )
    train_images = (dataset_root / str(raw["train"])).resolve()
    val_images = (dataset_root / str(raw["val"])).resolve()

    raw_names = raw["names"]
    if not isinstance(raw_names, dict):
        raise ConfigError("'names' 必须是类别编号到名称的映射")
    try:
        names = {int(key): str(value) for key, value in raw_names.items()}
    except (TypeError, ValueError) as exc:
        raise ConfigError("类别编号必须是整数") from exc
    if sorted(names) != list(range(len(names))):
        raise ConfigError(f"类别编号必须从 0 连续开始，当前为 {sorted(names)}")

    return DatasetConfig(
        config_path=config_path,
        dataset_root=dataset_root,
        train_images=train_images,
        val_images=val_images,
        names=names,
    )


def prepare_runtime_data_yaml(
    path: str | Path = "configs/data.yaml",
    output: str | Path = ".runtime/data.resolved.yaml",
) -> Path:
    """Create an absolute-path dataset YAML accepted consistently by Ultralytics."""
    config = load_dataset_config(path)
    output_path = resolve_project_path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    def runtime_split(path: Path) -> str:
        try:
            return path.relative_to(config.dataset_root).as_posix()
        except ValueError:
            return path.as_posix()

    payload = {
        "path": config.dataset_root.as_posix(),
        "train": runtime_split(config.train_images),
        "val": runtime_split(config.val_images),
        "names": config.names,
    }
    output_path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return output_path


def load_train_config(path: str | Path = "configs/train.yaml") -> dict[str, Any]:
    config = load_yaml(path)
    required = {
        "model": str,
        "data": str,
        "epochs": int,
        "imgsz": int,
        "batch": (int, float),
        "device": (int, str),
        "project": str,
        "name": str,
    }
    for key, expected in required.items():
        if key not in config:
            raise ConfigError(f"训练配置缺少字段 '{key}'")
        if not isinstance(config[key], expected):
            raise ConfigError(f"训练配置字段 '{key}' 类型错误: {type(config[key]).__name__}")

    if config["epochs"] <= 0 or config["imgsz"] <= 0:
        raise ConfigError("epochs 和 imgsz 必须大于 0")
    config["project"] = str(resolve_project_path(config["project"]))
    config["data"] = str(resolve_project_path(config["data"]))
    return config


def project_root() -> Path:
    return PROJECT_ROOT
