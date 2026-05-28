"""Vowel space (F1×F2) scatter widget.

Reference ellipse centres (from published acoustic data):
  Female: F1=450 Hz, F2=1800 Hz, radii ±200 Hz (F1), ±500 Hz (F2)
  Male:   F1=600 Hz, F2=1300 Hz, radii ±200 Hz (F1), ±400 Hz (F2)

Axes (standard vowel-chart orientation):
  X axis: F2, 500 Hz (left) → 3000 Hz (right) — high F2 = fronted vowel
  Y axis: F1, 900 Hz (top) → 200 Hz (bottom) — low F1 = closed vowel

"You are here" dot colour:
  Green  : within female ellipse (F1 and F2 both within female radii)
  Yellow : between male and female ellipses
  Red    : within male ellipse (F1 and F2 both within male radii)
"""
from __future__ import annotations
from collections import deque
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtCore import Qt

_TRAIL_LEN = 60   # ~2 seconds of history at 30 Hz

# Reference ellipse centres and radii [Hz]
_FEMALE = {"f1": 450.0, "f2": 1800.0, "r_f1": 200.0, "r_f2": 500.0}
_MALE   = {"f1": 600.0, "f2": 1300.0, "r_f1": 200.0, "r_f2": 400.0}

_F2_MIN, _F2_MAX = 500.0, 3000.0
_F1_MIN, _F1_MAX = 200.0, 900.0


def _in_ellipse(f1: float, f2: float, centre: dict) -> bool:
    """Return True if (f1, f2) lies inside the ellipse defined by centre.

    Uses the proper ellipse equation: (dx/r_f1)² + (dy/r_f2)² ≤ 1
    This is NOT a bounding-box test — corners of the bounding box are outside.
    """
    return (
        (f1 - centre["f1"]) ** 2 / centre["r_f1"] ** 2
        + (f2 - centre["f2"]) ** 2 / centre["r_f2"] ** 2
    ) <= 1.0


def _dot_color(f1: float, f2: float) -> QColor:
    if _in_ellipse(f1, f2, _FEMALE):
        return QColor(60, 200, 100)    # green
    if _in_ellipse(f1, f2, _MALE):
        return QColor(200, 60, 60)     # red
    return QColor(220, 200, 60)        # yellow — between ellipses


class VowelSpaceWidget(QWidget):
    """F1×F2 scatter plot with reference ellipses and rolling history trail."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(250, 220)
        self._trail: deque[tuple[float, float]] = deque(maxlen=_TRAIL_LEN)
        self._current: tuple[float, float] | None = None

    def add_frame(self, f1: float, f2: float) -> None:
        """Add a voiced frame to the trail and repaint."""
        self._trail.append((f1, f2))
        self._current = (f1, f2)
        self.update()

    def clear(self) -> None:
        """Clear all history points."""
        self._trail.clear()
        self._current = None
        self.update()

    def _hz_to_px(self, f1: float, f2: float, w: int, h: int) -> tuple[int, int]:
        x = int((f2 - _F2_MIN) / (_F2_MAX - _F2_MIN) * w)
        y = int((_F1_MAX - f1) / (_F1_MAX - _F1_MIN) * h)   # F1 axis inverted
        return x, y

    def _ellipse_rect(self, centre: dict, w: int, h: int):
        cx, cy = self._hz_to_px(centre["f1"], centre["f2"], w, h)
        rx = int(centre["r_f2"] / (_F2_MAX - _F2_MIN) * w)
        ry = int(centre["r_f1"] / (_F1_MAX - _F1_MIN) * h)
        return cx - rx, cy - ry, 2 * rx, 2 * ry

    def paintEvent(self, _event: object) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor(25, 25, 35))

        # Draw reference ellipses
        for centre, color in [(_FEMALE, QColor(60, 200, 100, 80)), (_MALE, QColor(200, 60, 60, 80))]:
            painter.setPen(QPen(color, 1))
            painter.setBrush(color)
            x, y, rw, rh = self._ellipse_rect(centre, w, h)
            painter.drawEllipse(x, y, rw, rh)

        # Draw trail (fading)
        trail = list(self._trail)
        for i, (f1, f2) in enumerate(trail[:-1]):
            alpha = int(40 + 160 * i / max(len(trail) - 1, 1))
            color = QColor(180, 180, 255, alpha)
            painter.setPen(QPen(color, 2))
            px, py = self._hz_to_px(f1, f2, w, h)
            painter.drawEllipse(px - 2, py - 2, 4, 4)

        # Draw "you are here" dot
        if self._current is not None:
            f1, f2 = self._current
            px, py = self._hz_to_px(f1, f2, w, h)
            dot_color = _dot_color(f1, f2)
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setBrush(dot_color)
            painter.drawEllipse(px - 6, py - 6, 12, 12)
