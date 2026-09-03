from __future__ import annotations

from pathlib import Path

from PIL import Image

from car_damage.gui.history import HistoryStore
from car_damage.gui.inference import annotate_image
from car_damage.gui.desktop import default_output_dir
from car_damage.gui.model_registry import ModelRegistry
from car_damage.gui.models import Detection, ImageResult, ModelSpec, TaskSummary
from car_damage.gui.scanner import scan_images
from car_damage.gui.settings import AppSettings
from car_damage.gui.workers import InferenceWorker


def test_annotate_image_draws_box_without_mutating_source() -> None:
    source = Image.new("RGB", (240, 160), "white")
    detection = Detection("dent", "凹陷", 0.96, (20, 30, 180, 120))

    annotated = annotate_image(source, [detection])

    assert source.getpixel((20, 30)) == (255, 255, 255)
    assert annotated.getpixel((20, 30)) != (255, 255, 255)
    assert annotated.size == source.size


def test_registry_keeps_named_models_and_imports_custom_weight(tmp_path: Path) -> None:
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    builtin = models_dir / "YOLO26s_DentScratch_mAP50_73.18.pt"
    builtin.write_bytes(b"weight")
    registry = ModelRegistry(models_dir, models_dir / "models.json")
    registry.save(
        [
            ModelSpec(
                id="yolo26s-two-class",
                display_name="YOLO26s-两分类车损检测",
                filename=builtin.name,
                classes=["dent", "scratch"],
                map50=0.7318,
                builtin=True,
            )
        ]
    )

    assert registry.available()[0].display_name.startswith("YOLO26s")
    source = tmp_path / "custom.pt"
    source.write_bytes(b"custom")
    imported = registry.import_model(source, "YOLO26s-自定义车损检测")
    assert imported.path(models_dir).is_file()
    assert imported.filename.startswith("custom/")
    assert len(registry.all()) == 2
    registry.remove(imported.id)
    assert len(registry.all()) == 1


def test_registry_does_not_remove_builtin_model(tmp_path: Path) -> None:
    registry = ModelRegistry(tmp_path, tmp_path / "models.json")
    registry.save([ModelSpec("builtin", "YOLO26s-Builtin", "a.pt", builtin=True)])
    try:
        registry.remove("builtin")
    except ValueError:
        pass
    else:
        raise AssertionError("expected built-in protection")


def test_history_round_trip_and_delete(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "history.db")
    result = ImageResult(
        source_path="a.jpg",
        output_path="out/a.jpg",
        elapsed_ms=12.5,
        width=640,
        height=480,
        detections=[Detection("dent", "凹陷", 0.88, (1, 2, 30, 40))],
    )
    summary = TaskSummary(
        id="task-1",
        created_at="2026-09-03 10:00:00",
        model_name="YOLO26s-两分类车损检测",
        source="images",
        output_dir="out",
        total_images=1,
        completed_images=1,
        defect_images=1,
        total_detections=1,
        elapsed_seconds=0.1,
        status="completed",
    )
    store.save_task(summary, [result])

    assert store.list_tasks()[0].model_name == summary.model_name
    assert store.task_results("task-1")[0].detections[0].confidence == 0.88
    store.delete_task("task-1")
    assert store.list_tasks() == []


def test_history_clear_all_removes_tasks_and_results(tmp_path: Path) -> None:
    store = HistoryStore(tmp_path / "history.db")
    result = ImageResult("a.jpg", "out/a.jpg", 1.0, 10, 10, [])
    for task_id in ("task-1", "task-2"):
        summary = TaskSummary(
            id=task_id,
            created_at="2026-09-03 10:00:00",
            model_name="YOLO26s-Test",
            source="images",
            output_dir="out",
            total_images=1,
            completed_images=1,
            defect_images=0,
            total_detections=0,
            elapsed_seconds=0.1,
            status="completed",
        )
        store.save_task(summary, [result])

    store.clear_all()

    assert store.list_tasks() == []
    assert store.totals() == {"tasks": 0, "images": 0, "detections": 0}


def test_scan_images_filters_formats_and_is_not_recursive(tmp_path: Path) -> None:
    (tmp_path / "a.jpg").write_bytes(b"a")
    (tmp_path / "b.PNG").write_bytes(b"b")
    (tmp_path / "note.txt").write_text("x")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "hidden.jpg").write_bytes(b"hidden")

    assert [path.name for path in scan_images(tmp_path)] == ["a.jpg", "b.PNG"]


def test_settings_round_trip_and_reset(tmp_path: Path) -> None:
    settings = AppSettings(tmp_path / "settings.ini")
    settings.set("confidence", 0.4)
    settings.set("imgsz", 640)
    assert settings.get("confidence") == 0.4
    assert settings.get("imgsz") == 640
    settings.reset()
    assert settings.get("confidence") == 0.25
    assert Path(settings.get("output_dir")).name == "CarDamageResults"
    assert default_output_dir().is_absolute()


def test_inference_worker_emits_results_with_fake_service(tmp_path: Path) -> None:
    class FakeService:
        def load(self, _path):
            return None

        def predict(self, image, output, *_args):
            return ImageResult(str(image), str(output / "out.jpg"), 1.0, 10, 10, [])

    image = tmp_path / "image.jpg"
    image.write_bytes(b"image")
    worker = InferenceWorker(
        FakeService(), ModelSpec("m", "YOLO26s-Test", "test.pt"), tmp_path,
        [image], tmp_path / "out", "cpu", 0.25, 0.7, 640,
    )
    completed = []
    progress = []
    worker.progress.connect(lambda current, total, result: progress.append((current, total)))
    worker.completed.connect(lambda results, cancelled: completed.append((results, cancelled)))
    worker.run()
    assert progress == [(1, 1)]
    assert len(completed[0][0]) == 1
    assert completed[0][1] is False


def test_cancelled_worker_does_not_process_images(tmp_path: Path) -> None:
    class FakeService:
        def load(self, _path):
            return None

        def predict(self, *_args):
            raise AssertionError("cancelled worker must not predict")

    worker = InferenceWorker(
        FakeService(), ModelSpec("m", "YOLO26s-Test", "test.pt"), tmp_path,
        [tmp_path / "a.jpg"], tmp_path / "out", "cpu", 0.25, 0.7, 640,
    )
    completed = []
    worker.completed.connect(lambda results, cancelled: completed.append((results, cancelled)))
    worker.cancel()
    worker.run()
    assert completed == [([], True)]
