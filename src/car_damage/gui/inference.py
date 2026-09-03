from __future__ import annotations

import os
import time
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .models import Detection, ImageResult


CLASS_NAMES_ZH = {"dent": "凹陷", "crack": "裂纹", "scratch": "划痕"}
BOX_COLORS = {
    "dent": (30, 112, 220),
    "crack": (232, 80, 91),
    "scratch": (18, 176, 150),
}


@lru_cache(maxsize=16)
def _annotation_font(size: int):
    windows_dir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    candidates = (
        windows_dir / "Fonts" / "msyh.ttc",
        windows_dir / "Fonts" / "msyhbd.ttc",
        windows_dir / "Fonts" / "simhei.ttf",
        windows_dir / "Fonts" / "simsun.ttc",
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    )
    for path in candidates:
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def annotate_image(source: Image.Image, detections: list[Detection]) -> Image.Image:
    """Return a copy with localized bounding boxes and confidence labels."""
    image = source.convert("RGB").copy()
    draw = ImageDraw.Draw(image)
    font_size = max(16, min(34, round(min(image.size) * 0.035)))
    font = _annotation_font(font_size)
    line_width = max(2, round(min(image.size) * 0.006))
    for detection in detections:
        x1, y1, x2, y2 = (round(value) for value in detection.box)
        x1 = max(0, min(x1, image.width - 1))
        y1 = max(0, min(y1, image.height - 1))
        x2 = max(x1, min(x2, image.width - 1))
        y2 = max(y1, min(y2, image.height - 1))
        color = BOX_COLORS.get(detection.class_name.lower(), (30, 112, 220))
        draw.rectangle((x1, y1, x2, y2), outline=color, width=line_width)

        label = f"{detection.display_name} {detection.confidence:.1%}"
        left, top, right, bottom = draw.textbbox((0, 0), label, font=font)
        text_width, text_height = right - left, bottom - top
        padding_x, padding_y = 7, 4
        label_y = y1 - text_height - padding_y * 2
        if label_y < 0:
            label_y = min(image.height - text_height - padding_y * 2, y1 + line_width)
        label_right = min(image.width - 1, x1 + text_width + padding_x * 2)
        draw.rounded_rectangle(
            (x1, label_y, label_right, label_y + text_height + padding_y * 2),
            radius=4,
            fill=color,
        )
        draw.text(
            (x1 + padding_x, label_y + padding_y - top),
            label,
            font=font,
            fill="white",
        )
    return image


def resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested
    try:
        import torch

        return "0" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


class InferenceService:
    def __init__(self) -> None:
        self.model = None
        self.loaded_path: Path | None = None

    def load(self, weight_path: Path) -> None:
        weight_path = Path(weight_path).resolve()
        if self.model is not None and self.loaded_path == weight_path:
            return
        if not weight_path.is_file():
            raise FileNotFoundError(f"模型权重不存在：{weight_path}")
        from ultralytics import YOLO

        self.model = YOLO(str(weight_path))
        self.loaded_path = weight_path

    def predict(
        self,
        image_path: Path,
        output_dir: Path,
        device: str,
        confidence: float,
        iou: float,
        imgsz: int,
    ) -> ImageResult:
        if self.model is None:
            raise RuntimeError("模型尚未加载")
        image_path = Path(image_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        predictions = self.model.predict(
            source=str(image_path),
            device=resolve_device(device),
            conf=confidence,
            iou=iou,
            imgsz=imgsz,
            verbose=False,
        )
        result = predictions[0]
        names = result.names
        detections: list[Detection] = []
        if result.boxes is not None:
            for box in result.boxes:
                class_id = int(box.cls[0].item())
                class_name = str(names.get(class_id, class_id))
                coordinates = tuple(float(value) for value in box.xyxy[0].tolist())
                detections.append(
                    Detection(
                        class_name=class_name,
                        display_name=CLASS_NAMES_ZH.get(class_name.lower(), class_name),
                        confidence=float(box.conf[0].item()),
                        box=coordinates,
                    )
                )
        output_path = output_dir / f"{image_path.stem}_detected.jpg"
        with Image.open(image_path) as source_image:
            annotated = annotate_image(ImageOps.exif_transpose(source_image), detections)
        annotated.save(output_path, quality=94)
        height, width = result.orig_shape
        return ImageResult(
            source_path=str(image_path),
            output_path=str(output_path),
            elapsed_ms=(time.perf_counter() - started) * 1000,
            width=int(width),
            height=int(height),
            detections=detections,
        )
