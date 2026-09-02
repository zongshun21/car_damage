from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from car_damage.config import resolve_project_path  # noqa: E402
from car_damage.dataset import IMAGE_SUFFIXES  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="对单张图片或图片目录执行车辆缺陷检测")
    parser.add_argument("--weights", required=True, help="best.pt 权重路径")
    parser.add_argument("--source", required=True, help="图片或图片目录")
    parser.add_argument("--device", default="0", help="推理设备，例如 0 或 cpu")
    parser.add_argument("--conf", type=float, default=0.25, help="置信度阈值")
    parser.add_argument("--iou", type=float, default=0.70, help="IoU 阈值")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--output", default="runs/car_damage/predict", help="输出目录")
    parser.add_argument("--save-txt", action="store_true", help="保存 YOLO 文本预测")
    parser.add_argument("--save-conf", action="store_true", help="文本预测中包含置信度")
    return parser


def _validate_source(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"输入不存在: {path}")
    if path.is_file() and path.suffix.lower() not in IMAGE_SUFFIXES:
        raise ValueError(f"不支持的图片格式: {path.suffix}")
    if path.is_dir() and not any(
        item.is_file() and item.suffix.lower() in IMAGE_SUFFIXES for item in path.iterdir()
    ):
        raise ValueError(f"目录内没有支持的图片: {path}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        weights = resolve_project_path(args.weights)
        source = resolve_project_path(args.source)
        output = resolve_project_path(args.output)
        if not weights.is_file():
            raise FileNotFoundError(f"权重不存在: {weights}")
        _validate_source(source)
        if not 0.0 <= args.conf <= 1.0 or not 0.0 <= args.iou <= 1.0:
            raise ValueError("conf 和 iou 必须位于 0 到 1")
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("未安装 Ultralytics，请先运行 setup_env.ps1") from exc

        output.parent.mkdir(parents=True, exist_ok=True)
        model = YOLO(str(weights))
        model.predict(
            source=str(source),
            device=args.device,
            conf=args.conf,
            iou=args.iou,
            imgsz=args.imgsz,
            save=True,
            save_txt=args.save_txt,
            save_conf=args.save_conf,
            project=str(output.parent),
            name=output.name,
            exist_ok=True,
        )
        print(f"推理结果: {output}")
        return 0
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

