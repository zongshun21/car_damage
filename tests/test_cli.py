from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


@pytest.mark.parametrize(
    "script",
    [
        "build_balanced_dataset.py",
        "build_two_class_dataset.py",
        "check_dataset.py",
        "gui.py",
        "train.py",
        "validate.py",
        "predict.py",
    ],
)
def test_help_works(script: str) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / script), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _load_script(name: str):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_train_dry_run_builds_yolo26s_arguments(capsys) -> None:
    train = _load_script("train.py")
    assert train.main(["--dry-run", "--skip-image-verify", "--epochs", "2"]) == 0
    output = capsys.readouterr().out
    assert "yolo26s.pt" in output
    assert '"epochs": 2' in output


def test_validate_rejects_missing_weights(capsys) -> None:
    validate = _load_script("validate.py")
    assert validate.main(["--weights", "missing.pt"]) == 2
    assert "权重不存在" in capsys.readouterr().err


def test_predict_rejects_missing_weights(capsys) -> None:
    predict = _load_script("predict.py")
    assert predict.main(["--weights", "missing.pt", "--source", "missing.jpg"]) == 2
    assert "权重不存在" in capsys.readouterr().err
