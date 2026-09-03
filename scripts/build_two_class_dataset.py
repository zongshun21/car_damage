from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from car_damage.config import load_dataset_config, resolve_project_path  # noqa: E402
from car_damage.two_class import build_two_class_dataset  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a dent/scratch two-class dataset")
    parser.add_argument("--data", default="configs/data.yaml")
    parser.add_argument("--output", default=".runtime/two_class_dataset")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_dataset_config(args.data)
    result = build_two_class_dataset(config.dataset_root, resolve_project_path(args.output))
    print(
        f"two-class dataset: images={result.images} kept_boxes={result.kept_boxes} "
        f"dropped_crack_boxes={result.dropped_class_boxes} "
        f"removed_invalid_boxes={result.removed_invalid_boxes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
