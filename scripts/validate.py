from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from car_damage.config import ConfigError, prepare_runtime_data_yaml, resolve_project_path  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="验证车辆缺陷检测权重")
    parser.add_argument("--weights", required=True, help="best.pt 或其他权重路径")
    parser.add_argument("--data", default="configs/data.yaml", help="数据配置 YAML")
    parser.add_argument("--device", default="0", help="推理设备，例如 0 或 cpu")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--name", default="validation")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        weights = resolve_project_path(args.weights)
        if not weights.is_file():
            raise FileNotFoundError(f"权重不存在: {weights}")
        runtime_data = prepare_runtime_data_yaml(args.data)
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("未安装 Ultralytics，请先运行 setup_env.ps1") from exc

        model = YOLO(str(weights))
        metrics = model.val(
            data=str(runtime_data),
            split="val",
            device=args.device,
            imgsz=args.imgsz,
            batch=args.batch,
            project=str(resolve_project_path("runs/car_damage")),
            name=args.name,
            plots=True,
        )
        summary = {key: float(value) for key, value in metrics.results_dict.items()}
        summary["per_class_map50_95"] = [float(value) for value in metrics.box.maps]
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except (ConfigError, FileNotFoundError, OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

