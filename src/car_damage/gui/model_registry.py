from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path

from .models import ModelSpec


class ModelRegistry:
    def __init__(self, models_dir: Path, manifest_path: Path | None = None) -> None:
        self.models_dir = Path(models_dir)
        self.manifest_path = manifest_path or self.models_dir / "models.json"
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def all(self) -> list[ModelSpec]:
        specs: list[ModelSpec] = []
        if self.manifest_path.is_file():
            try:
                raw = json.loads(self.manifest_path.read_text(encoding="utf-8"))
                specs = [ModelSpec.from_dict(item) for item in raw.get("models", [])]
            except (json.JSONDecodeError, OSError, TypeError, ValueError):
                specs = []
        known = {spec.filename.lower() for spec in specs}
        for path in sorted(self.models_dir.rglob("*.pt")):
            relative = path.relative_to(self.models_dir).as_posix()
            if relative.lower() not in known:
                specs.append(
                    ModelSpec(
                        id=f"auto-{uuid.uuid5(uuid.NAMESPACE_URL, str(path.resolve()))}",
                        display_name=path.stem.replace("_", "-"),
                        filename=relative,
                        description="自动扫描到的本地模型",
                    )
                )
        return specs

    def available(self) -> list[ModelSpec]:
        return [spec for spec in self.all() if spec.path(self.models_dir).is_file()]

    def save(self, specs: list[ModelSpec]) -> None:
        payload = {"version": 1, "models": [spec.to_dict() for spec in specs]}
        self.manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def import_model(self, source: Path, display_name: str | None = None) -> ModelSpec:
        source = Path(source)
        if not source.is_file() or source.suffix.lower() != ".pt":
            raise ValueError("请选择有效的 .pt 权重文件")
        specs = self.all()
        safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", source.stem).strip("._") or "model"
        custom_dir = self.models_dir / "custom"
        custom_dir.mkdir(parents=True, exist_ok=True)
        destination = custom_dir / f"{safe_stem}.pt"
        counter = 2
        while destination.exists() and destination.resolve() != source.resolve():
            destination = custom_dir / f"{safe_stem}_{counter}.pt"
            counter += 1
        if destination.resolve() != source.resolve():
            shutil.copy2(source, destination)
        spec = ModelSpec(
            id=f"custom-{uuid.uuid4()}",
            display_name=(display_name or source.stem).strip(),
            filename=destination.relative_to(self.models_dir).as_posix(),
            description="用户导入模型",
        )
        specs.append(spec)
        self.save(specs)
        return spec

    def update(self, updated: ModelSpec) -> None:
        specs = self.all()
        for index, spec in enumerate(specs):
            if spec.id == updated.id:
                specs[index] = updated
                self.save(specs)
                return
        raise KeyError(updated.id)

    def remove(self, model_id: str) -> None:
        specs = self.all()
        target = next((spec for spec in specs if spec.id == model_id), None)
        if target is None:
            raise KeyError(model_id)
        if target.builtin:
            raise ValueError("内置模型不能移除")
        path = target.path(self.models_dir)
        if path.is_file():
            path.unlink()
        self.save([spec for spec in specs if spec.id != model_id])
