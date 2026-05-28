"""Spike 3: Prototype the F1×F2 vowel space scatter widget.

Generates random F1/F2 pairs at 30 Hz to simulate live updates.
Check: no flicker, "you are here" dot visible, reference ellipses visible.

Run: python spikes/03_vowel_space_widget.py
"""
import sys
import random
from collections import deque
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

# Reference ellipse centres (F1, F2) and radii for cis-female speech
FEMALE_CENTRE = (450, 1800)
FEMALE_RADIUS = (200, 500)
MALE_CENTRE = (600, 1300)
MALE_RADIUS = (200, 400)

F1_RANGE = (200, 900)    # y-axis (inverted: low F1 at top)
F2_RANGE = (700, 3000)   # x-axis


class VowelSpaceWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(400, 350)
        self.setWindowTitle("Vowel Space Spike")
        self._history: deque[tuple[float, float]] = deque(maxlen=60)  # ~2s at 30Hz
        self._current: tuple[float, float] | None = None
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(33)  # ~30 Hz

    def _tick(self) -> None:
        f1 = random.gauss(FEMALE_CENTRE[0], 80)
        f2 = random.gauss(FEMALE_CENTRE[1], 200)
        self._history.append((f1, f2))
        self._current = (f1, f2)
        self.update()

    def _to_px(self, f1: float, f2: float) -> tuple[int, int]:
        w, h = self.width(), self.height()
        pad = 30
        x = int(pad + (f2 - F2_RANGE[0]) / (F2_RANGE[1] - F2_RANGE[0]) * (w - 2 * pad))
        # F1 axis is inverted (higher F1 = lower formant frequency = bottom)
        y = int(pad + (1 - (f1 - F1_RANGE[0]) / (F1_RANGE[1] - F1_RANGE[0])) * (h - 2 * pad))
        return x, y

    def paintEvent(self, _event: object) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(20, 20, 30))

        # Reference ellipses
        for centre, radius, color in [
            (FEMALE_CENTRE, FEMALE_RADIUS, QColor(80, 200, 120, 60)),
            (MALE_CENTRE, MALE_RADIUS, QColor(200, 80, 80, 60)),
        ]:
            cx, cy = self._to_px(*centre)
            rx = int(radius[1] / (F2_RANGE[1] - F2_RANGE[0]) * (self.width() - 60))
            ry = int(radius[0] / (F1_RANGE[1] - F1_RANGE[0]) * (self.height() - 60))
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - rx, cy - ry, 2 * rx, 2 * ry)

        # History dots
        painter.setPen(Qt.PenStyle.NoPen)
        for i, (f1, f2) in enumerate(self._history):
            alpha = int(60 + 180 * i / max(len(self._history), 1))
            painter.setBrush(QBrush(QColor(100, 180, 255, alpha)))
            x, y = self._to_px(f1, f2)
            painter.drawEllipse(x - 3, y - 3, 6, 6)

        # Current position
        if self._current:
            x, y = self._to_px(*self._current)
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(x - 6, y - 6, 12, 12)


app = QApplication(sys.argv)
w = VowelSpaceWidget()
w.show()
sys.exit(app.exec())
