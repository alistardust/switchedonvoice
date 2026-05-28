"""Time-domain waveform display widget.

Renders the most recent 200 ms of raw audio as a green line plot on a dark
background. Y axis is normalised to ±1.0. Fixed height of 80 px.
Updated by AnalysisPanel.update_result() on every incoming frame.
"""
from __future__ import annotations
import numpy as np
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPaintEvent, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QSizePolicy, QWidget


class WaveformWidget(QWidget):
    """Scrolling time-domain waveform display (200 ms window, fixed 80 px height)."""

    _BACKGROUND = QColor(20, 20, 20)
    _LINE_COLOR = QColor(60, 200, 100)  # green
    _LINE_WIDTH = 1.5

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._samples: np.ndarray = np.zeros(0, dtype=np.float32)
        self.setMinimumSize(200, 60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(80)

    def update_waveform(self, samples: np.ndarray) -> None:
        """Accept a new audio buffer (float32, any length) and schedule repaint.

        Note: Must be called from the GUI thread.

        Args:
            samples: Raw audio samples (float32, normalised to ±1.0).
        """
        self._samples = samples[-4096:] if len(samples) > 4096 else samples
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:
        """Render the waveform."""
        w, h = self.width(), self.height()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(0, 0, w, h, self._BACKGROUND)

        samples = self._samples
        if len(samples) < 2:
            return

        pen = QPen(self._LINE_COLOR)
        pen.setWidthF(self._LINE_WIDTH)
        painter.setPen(pen)

        n = len(samples)
        half_h = h / 2.0
        step = w / (n - 1)

        poly = QPolygonF()
        for i, amp in enumerate(samples):
            x = i * step
            # Clamp to ±1 then map to pixel height (0 at top)
            y = half_h - float(np.clip(amp, -1.0, 1.0)) * (half_h - 2)
            poly.append(QPointF(x, y))

        painter.drawPolyline(poly)
