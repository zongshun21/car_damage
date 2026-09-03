from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ModelSpec:
    id: str
    display_name: str
    filename: str
    classes: list[str] = field(default_factory=list)
    map50: float | None = None
    precision: float | None = None
    imgsz: int = 768
    description: str = ""
    builtin: bool = False

    def path(self, models_dir: Path) -> Path:
        return models_dir / self.filename

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ModelSpec":
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{key: value[key] for key in allowed if key in value})


@dataclass
class Detection:
    class_name: str
    display_name: str
    confidence: float
    box: tuple[float, float, float, float]


@dataclass
class ImageResult:
    source_path: str
    output_path: str
    elapsed_ms: float
    width: int
    height: int
    detections: list[Detection] = field(default_factory=list)
    error: str = ""


@dataclass
class TaskSummary:
    id: str
    created_at: str
    model_name: str
    source: str
    output_dir: str
    total_images: int
    completed_images: int
    defect_images: int
    total_detections: int
    elapsed_seconds: float
    status: str

