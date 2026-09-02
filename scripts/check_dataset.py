from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from car_damage.config import ConfigError  # noqa: E402
from car_damage.dataset import DatasetReport, check_dataset  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="检查车辆缺陷 YOLO 数据集")
    parser.add_argument("--data", default="configs/data.yaml", help="数据配置 YAML")
    parser.add_argument("--skip-image-verify", action="store_true", help="跳过图片解码检查")
    parser.add_argument("--json", dest="json_path", help="将完整报告保存为 JSON")
    return parser


def print_report(report: DatasetReport) -> None:
    print(f"数据集: {report.dataset_root}")
    print("类别: " + ", ".join(f"{key}={value}" for key, value in report.class_names.items()))
    for split in report.splits:
        counts = ", ".join(f"class_{key}={value}" for key, value in split.class_counts.items())
        print(
            f"[{split.split}] images={split.images} labels={split.labels} "
            f"objects={split.objects} empty={split.empty_labels} "
            f"warnings={len(split.warnings)} {counts}"
        )
        for warning in split.warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        for error in split.errors:
            print(f"ERROR: {error}", file=sys.stderr)
    print("检查结果: PASS" if report.ok else "检查结果: FAIL")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = check_dataset(args.data, verify_images=not args.skip_image_verify)
    except (ConfigError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print_report(report)
    if args.json_path:
        output = Path(args.json_path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON 报告: {output}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

