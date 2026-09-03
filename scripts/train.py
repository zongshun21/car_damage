from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from car_damage.config import (  # noqa: E402
    ConfigError,
    load_train_config,
    prepare_runtime_data_yaml,
    resolve_project_path,
)
from car_damage.dataset import check_dataset  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="训练 YOLO26s 车辆缺陷检测模型")
    parser.add_argument("--config", default="configs/train.yaml", help="训练配置 YAML")
    parser.add_argument("--epochs", type=int, help="覆盖训练轮数")
    parser.add_argument("--batch", type=float, help="覆盖 batch；-1 表示自动选择")
    parser.add_argument("--imgsz", type=int, help="覆盖输入尺寸")
    parser.add_argument("--device", help="覆盖设备，例如 0 或 cpu")
    parser.add_argument("--name", help="覆盖运行名称")
    parser.add_argument("--resume", help="从指定 last.pt 恢复训练")
    parser.add_argument("--dry-run", action="store_true", help="只检查并打印配置，不加载模型或训练")
    parser.add_argument("--skip-image-verify", action="store_true", help="预检时跳过图片解码")
    return parser


def _normalize_number(value: float | None) -> int | float | None:
    if value is None:
        return None
    return int(value) if value.is_integer() else value


def build_train_arguments(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    config = load_train_config(args.config)
    model_name = str(config.pop("model"))
    data_config = str(config.pop("data"))
    runtime_data = prepare_runtime_data_yaml(data_config)
    config["data"] = str(runtime_data)

    overrides = {
        "epochs": args.epochs,
        "batch": _normalize_number(args.batch),
        "imgsz": args.imgsz,
        "device": args.device,
        "name": args.name,
    }
    config.update({key: value for key, value in overrides.items() if value is not None})
    if config["epochs"] <= 0 or config["imgsz"] <= 0:
        raise ConfigError("epochs 和 imgsz 必须大于 0")
    return model_name, config


def _require_cuda_if_requested(device: Any) -> None:
    if str(device).lower() == "cpu":
        return
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("未安装 PyTorch，请先运行 setup_env.ps1") from exc
    if not torch.cuda.is_available():
        raise RuntimeError("训练配置要求 CUDA，但 PyTorch 未检测到可用 NVIDIA GPU")
    print(f"CUDA: {torch.cuda.get_device_name(0)} | torch={torch.__version__}")


def _run_preflight(data_config: str, verify_images: bool) -> None:
    report = check_dataset(data_config, verify_images=verify_images)
    for split in report.splits:
        print(
            f"[{split.split}] images={split.images} labels={split.labels} "
            f"objects={split.objects} empty={split.empty_labels} warnings={len(split.warnings)}"
        )
    if not report.ok:
        errors = [error for split in report.splits for error in split.errors]
        preview = "\n".join(errors[:20])
        raise RuntimeError(f"数据预检失败，共 {len(errors)} 个错误:\n{preview}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        raw = load_train_config(args.config)
        _run_preflight(raw["data"], verify_images=not args.skip_image_verify)
        model_name, train_args = build_train_arguments(args)

        if args.resume:
            resume_path = resolve_project_path(args.resume)
            if not resume_path.is_file():
                raise FileNotFoundError(f"断点不存在: {resume_path}")
            model_name = str(resume_path)
            train_args = {"resume": True}

        if args.dry_run:
            print("DRY RUN：不会加载模型或启动训练")
            print(json.dumps({"model": model_name, **train_args}, ensure_ascii=False, indent=2, default=str))
            return 0

        _require_cuda_if_requested(train_args.get("device", 0))
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("未安装 Ultralytics，请先运行 setup_env.ps1") from exc

        print(f"加载模型: {model_name}")
        model = YOLO(model_name)
        model.train(**train_args)
        return 0
    except (ConfigError, FileNotFoundError, OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
