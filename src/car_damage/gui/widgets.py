from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from .theme import COLORS


class MetricCard(QFrame):
    def __init__(self, title: str, value: str = "--", accent: str = "#176BCE") -> None:
        super().__init__()
        self.setObjectName("Card")
        self.setMinimumHeight(108)
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        marker = QLabel("●")
        marker.setStyleSheet(f"color: {accent}; font-size: 13px;")
        label = QLabel(title)
        label.setObjectName("MetricLabel")
        top.addWidget(marker)
        top.addWidget(label)
        top.addStretch()
        self.value_label = QLabel(value)
        self.value_label.setObjectName("MetricValue")
        layout.addLayout(top)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class ImageView(QLabel):
    def __init__(self, placeholder: str = "请选择图片") -> None:
        super().__init__(placeholder)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(280, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            f"background:#101B2A; color:#91A4BA; border:1px solid {COLORS['border']}; border-radius:10px;"
        )
        self._pixmap: QPixmap | None = None

    def set_image(self, path: str | Path) -> None:
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self._pixmap = None
            self.setText("图片加载失败")
            return
        self._pixmap = pixmap
        self._render()

    def clear_image(self) -> None:
        self._pixmap = None
        self.setPixmap(QPixmap())
        self.setText("请选择图片")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._render()

    def _render(self) -> None:
        if self._pixmap:
            self.setPixmap(
                self._pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )


class StatBars(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.values: dict[str, int] = {"凹陷": 0, "裂纹": 0, "划痕": 0}
        self.setMinimumHeight(180)

    def set_values(self, values: dict[str, int]) -> None:
        self.values = values
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        maximum = max(self.values.values(), default=1) or 1
        colors = [QColor(COLORS["primary"]), QColor(COLORS["orange"]), QColor(COLORS["cyan"])]
        row_height = max(36, self.height() // max(1, len(self.values)))
        for index, (name, value) in enumerate(self.values.items()):
            y = index * row_height + 8
            painter.setPen(QColor(COLORS["muted"]))
            painter.drawText(8, y + 17, 52, 20, Qt.AlignmentFlag.AlignLeft, name)
            bar_x = 66
            bar_width = max(4, int((self.width() - 125) * value / maximum))
            painter.setBrush(colors[index % len(colors)])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(bar_x, y + 3, bar_width, 16, 5, 5)
            painter.setPen(QColor(COLORS["text"]))
            painter.drawText(self.width() - 52, y + 17, 45, 20, Qt.AlignmentFlag.AlignRight, str(value))


def page_heading(title: str, subtitle: str) -> QVBoxLayout:
    layout = QVBoxLayout()
    label = QLabel(title)
    label.setObjectName("PageTitle")
    note = QLabel(subtitle)
    note.setObjectName("Muted")
    layout.addWidget(label)
    layout.addWidget(note)
    return layout


def secondary_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setProperty("secondary", True)
    return button
