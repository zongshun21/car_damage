from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import Detection, ImageResult, TaskSummary


class HistoryStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, created_at TEXT NOT NULL, model_name TEXT NOT NULL,
                    source TEXT NOT NULL, output_dir TEXT NOT NULL, total_images INTEGER NOT NULL,
                    completed_images INTEGER NOT NULL, defect_images INTEGER NOT NULL,
                    total_detections INTEGER NOT NULL, elapsed_seconds REAL NOT NULL,
                    status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS image_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
                    source_path TEXT NOT NULL, output_path TEXT NOT NULL,
                    elapsed_ms REAL NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL,
                    detections_json TEXT NOT NULL, error TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
                );
                """
            )

    def save_task(self, summary: TaskSummary, results: list[ImageResult]) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                tuple(vars(summary).values()),
            )
            db.execute("DELETE FROM image_results WHERE task_id = ?", (summary.id,))
            for result in results:
                detections = [
                    {
                        "class_name": item.class_name,
                        "display_name": item.display_name,
                        "confidence": item.confidence,
                        "box": list(item.box),
                    }
                    for item in result.detections
                ]
                db.execute(
                    """INSERT INTO image_results
                    (task_id, source_path, output_path, elapsed_ms, width, height,
                     detections_json, error) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        summary.id,
                        result.source_path,
                        result.output_path,
                        result.elapsed_ms,
                        result.width,
                        result.height,
                        json.dumps(detections, ensure_ascii=False),
                        result.error,
                    ),
                )

    def list_tasks(self, query: str = "", model_name: str = "") -> list[TaskSummary]:
        sql = "SELECT * FROM tasks WHERE 1=1"
        params: list[str] = []
        if query:
            sql += " AND (source LIKE ? OR model_name LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        if model_name:
            sql += " AND model_name = ?"
            params.append(model_name)
        sql += " ORDER BY created_at DESC"
        with self._connect() as db:
            rows = db.execute(sql, params).fetchall()
        return [TaskSummary(**dict(row)) for row in rows]

    def task_results(self, task_id: str) -> list[ImageResult]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM image_results WHERE task_id = ? ORDER BY id", (task_id,)
            ).fetchall()
        results: list[ImageResult] = []
        for row in rows:
            detections = [
                Detection(
                    item["class_name"],
                    item["display_name"],
                    float(item["confidence"]),
                    tuple(item["box"]),
                )
                for item in json.loads(row["detections_json"])
            ]
            results.append(
                ImageResult(
                    row["source_path"], row["output_path"], row["elapsed_ms"],
                    row["width"], row["height"], detections, row["error"]
                )
            )
        return results

    def delete_task(self, task_id: str) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def clear_all(self) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM tasks")

    def totals(self) -> dict[str, int]:
        with self._connect() as db:
            row = db.execute(
                """SELECT COUNT(*) tasks, COALESCE(SUM(completed_images), 0) images,
                COALESCE(SUM(total_detections), 0) detections FROM tasks"""
            ).fetchone()
        return dict(row)
