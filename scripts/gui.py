from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from car_damage.gui.bootstrap import prepare_qt_environment, write_startup_log  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="启动兰州石化职业技术大学车辆缺陷检测平台")
    parser.add_argument("--smoke-test", action="store_true", help="启动后自动退出，用于环境检查")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    prepare_qt_environment(allow_offscreen=args.smoke_test)
    write_startup_log(
        f"bootstrap smoke_test={args.smoke_test} qpa={__import__('os').environ.get('QT_QPA_PLATFORM')}"
    )
    try:
        from car_damage.gui.app import run

        return run(smoke_test=args.smoke_test)
    except Exception as exc:
        write_startup_log(f"fatal {type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
