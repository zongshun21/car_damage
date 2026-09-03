from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from car_damage.balance import build_balanced_train_set  # noqa: E402
from car_damage.config import load_dataset_config, resolve_project_path  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a crack-balanced YOLO training dataset")
    parser.add_argument("--data", default="configs/data.yaml")
    parser.add_argument("--output", default=".runtime/balanced_dataset")
    parser.add_argument("--class-id", type=int, default=1)
    parser.add_argument("--factor", type=int, default=4)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_dataset_config(args.data)
    output = resolve_project_path(args.output)
    result = build_balanced_train_set(
        config.train_images,
        config.train_images.parent / "labels",
        output,
        minority_class=args.class_id,
        minority_factor=args.factor,
    )
    print(
        f"balanced dataset: source={result.source_images} output={result.output_images} "
        f"minority_images={result.minority_images} removed_boxes={result.removed_boxes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
