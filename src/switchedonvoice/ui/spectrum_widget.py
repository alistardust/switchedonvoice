"""Spectrum display widget.

QPainter-based line plot of the magnitude spectrum.
  X axis: 0–8 kHz (clipped from full FFT range)
  Y axis: −90 dBFS to 0 dBFS
  Grid lines at −20, −40, −60 dBFS
  Spectrum line: green
  No Qt Charts dependency — pure QPainter on QWidget.
"""
from __future__ import annotations
import numpy as np
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtCore import QPointF

_DB_MIN = -90.0
_DB_MAX = 0.0
_FREQ_MAX_HZ = 8000.0
_GRID_LINES_DB = (-20.0, -40.0, -60.0)

_BG_COLOR = QColor(20, 20, 30)
_LINE_COLOR = QColor(60, 200, 100)       # green
_GRID_COLOR = QColor(60, 60, 80)
_AXIS_COLOR = QColor(120, 120, 140)


class SpectrumWidget(QWidget):
    """Magnitude spectrum line-plot widget (0–8 kHz, −90–0 dBFS)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(200, 120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._freqs: np.ndarray = np.zeros(0, dtype=np.float32)
        self._db: np.ndarray = np.zeros(0, dtype=np.float32)

    def update_spectrum(self, freqs: np.ndarray, db: np.ndarray) -> None:
        """Accept new spectrum data and schedule a repaint.

        Args:
            freqs: Frequency bins in Hz (float32 array, monotonically increasing).
            db:    Magnitude in dBFS (float32 array, same length as freqs).
        """
        self._freqs = freqs
        self._db = db
        self.update()

    def paintEvent(self, _event: object) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, _BG_COLOR)

        # Grid lines
        grid_pen = QPen(_GRID_COLOR, 1)
        painter.setPen(grid_pen)
        for db_level in _GRID_LINES_DB:
            y = self._db_to_y(db_level, h)
            painter.drawLine(0, y, w, y)

        if len(self._freqs) < 2:
            return

        # Clip to display range
        mask = self._freqs <= _FREQ_MAX_HZ
        freqs = self._freqs[mask]
        db = self._db[mask]
        if len(freqs) < 2:
            return

        # Build polyline
        f_max = freqs[-1]
        if f_max <= 0:
            return

        points: list[QPointF] = []
        for freq, level in zip(freqs, db):
            x = freq / _FREQ_MAX_HZ * w
            y = self._db_to_y(float(level), h)
            points.append(QPointF(x, y))

        painter.setPen(QPen(_LINE_COLOR, 1))
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

    def _db_to_y(self, db: float, h: int) -> int:
        """Map a dBFS value to a pixel Y coordinate (0=top, h=bottom)."""
        clamped = max(_DB_MIN, min(db, _DB_MAX))
        ratio = (clamped - _DB_MAX) / (_DB_MIN - _DB_MAX)   # 0 at top (0 dBFS), 1 at bottom (-90)
        return int(ratio * h)
