from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from .inference import InferenceService
from .models import ImageResult, ModelSpec


class InferenceWorker(QObject):
    started = pyqtSignal(str)
    progress = pyqtSignal(int, int, object)
    image_done = pyqtSignal(object)
    image_failed = pyqtSignal(str, str)
    completed = pyqtSignal(object, bool)
    fatal_error = pyqtSignal(str)

    def __init__(
        self,
        service: InferenceService,
        model: ModelSpec,
        models_dir: Path,
        images: list[Path],
        output_dir: Path,
        device: str,
        confidence: float,
        iou: float,
        imgsz: int,
    ) -> None:
        super().__init__()
        self.service = service
        self.model_spec = model
        self.models_dir = Path(models_dir)
        self.images = list(images)
        self.output_dir = Path(output_dir)
        self.device = device
        self.confidence = confidence
        self.iou = iou
        self.imgsz = imgsz
        self._cancelled = False

    @pyqtSlot()
    def cancel(self) -> None:
        self._cancelled = True

    @pyqtSlot()
    def run(self) -> None:
        results: list[ImageResult] = []
        try:
            self.started.emit(f"正在加载 {self.model_spec.display_name}")
            self.service.load(self.model_spec.path(self.models_dir))
            total = len(self.images)
            for index, image in enumerate(self.images, start=1):
                if self._cancelled:
                    break
                try:
                    try:
                        result = self.service.predict(
                            image, self.output_dir, self.device,
                            self.confidence, self.iou, self.imgsz
                        )
                    except RuntimeError as exc:
                        message = str(exc).lower()
                        if self.device == "auto" and ("cuda" in message or "out of memory" in message):
                            result = self.service.predict(
                                image, self.output_dir, "cpu",
                                self.confidence, self.iou, self.imgsz
                            )
                        else:
                            raise
                    results.append(result)
                    self.image_done.emit(result)
                    self.progress.emit(index, total, result)
                except Exception as exc:  # continue past one damaged image
                    failed = ImageResult(str(image), "", 0, 0, 0, error=str(exc))
                    results.append(failed)
                    self.image_failed.emit(str(image), str(exc))
                    self.progress.emit(index, total, failed)
            self.completed.emit(results, self._cancelled)
        except Exception as exc:
            self.fatal_error.emit(str(exc))
            self.completed.emit(results, self._cancelled)
