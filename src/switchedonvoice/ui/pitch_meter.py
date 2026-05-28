"""Pitch meter widget.

Displays current F0 as a colour-coded vertical bar.
Zones:
  < 120 Hz : deep red     (very low masculine range)
  120–164  : red          (masculine range)
  165–184  : yellow       (transitional)
  185–255  : green        (feminine target range)
  > 255    : blue         (head voice — valid training territory, not a warning)
"""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QFont, QPen
from collections import deque

_CONTOUR_HISTORY = 300  # ~10 seconds at 30 Hz


_ZONES: list[tuple[float, float, QColor]] = [
    (0.0, 120.0, QColor(120, 0, 0)),
    (120.0, 165.0, QColor(200, 60, 60)),
    (165.0, 185.0, QColor(220, 200, 60)),
    (185.0, 256.0, QColor(60, 200, 100)),
    (256.0, 1200.0, QColor(80, 160, 255)),
]
_F0_MIN = 80.0
_F0_MAX = 500.0


def f0_zone_color(f0: float) -> QColor:
    """Return the display colour for a given F0 value."""
    for low, high, color in _ZONES:
        if low <= f0 < high:
            return color
    return _ZONES[-1][2]


class PitchMeterWidget(QWidget):
    """Vertical bar pitch meter with colour-coded zones."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(60, 250)
        self._f0: float | None = None
        self._contour: deque[float | None] = deque(maxlen=_CONTOUR_HISTORY)
        self._f0_target_min: float = 185.0
        self._f0_target_max: float = 255.0
        self._label = QLabel("--- Hz", self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)

    def set_f0(self, f0: float | None) -> None:
        """Update the displayed F0 value, append to rolling contour, and repaint."""
        self._f0 = f0
        self._contour.append(f0)
        if f0 is not None:
            self._label.setText(f"{f0:.0f} Hz")
        else:
            self._label.setText("--- Hz")
        self.update()

    def set_f0_target_range(self, min_hz: float, max_hz: float) -> None:
        """Override the F0 target zone boundaries and repaint.

        Args:
            min_hz: Lower bound of the green target zone (Hz).
            max_hz: Upper bound of the green target zone (Hz).

        Raises:
            ValueError: If min_hz >= max_hz or either value is non-positive.
        """
        if min_hz >= max_hz:
            raise ValueError(f"min_hz ({min_hz}) must be less than max_hz ({max_hz})")
        if min_hz <= 0 or max_hz <= 0:
            raise ValueError("F0 target range values must be positive")
        self._f0_target_min = min_hz
        self._f0_target_max = max_hz
        self.update()

    def _zone_color(self, f0: float) -> QColor:
        """Return zone color using the current F0 target range.

        Zones:
          < 120 Hz              : deep red
          120 – target_min      : red / yellow gradient split at midpoint
          target_min – target_max : green (feminine target)
          > target_max          : blue (head voice)

        Args:
            f0: F0 value in Hz.

        Returns:
            QColor for the zone.
        """
        mid = (120.0 + self._f0_target_min) / 2.0
        dynamic_zones: list[tuple[float, float, QColor]] = [
            (0.0, 120.0, QColor(120, 0, 0)),
            (120.0, mid, QColor(200, 60, 60)),
            (mid, self._f0_target_min, QColor(220, 200, 60)),
            (self._f0_target_min, self._f0_target_max, QColor(60, 200, 100)),
            (self._f0_target_max, 1200.0, QColor(80, 160, 255)),
        ]
        for low, high, color in dynamic_zones:
            if low <= f0 < high:
                return color
        return QColor(80, 160, 255)

    def paintEvent(self, _event: object) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bar_h = h - 30  # reserve space for label
        painter.fillRect(0, 0, w, bar_h, QColor(30, 30, 40))

        if self._f0 is None:
            return

        clamped = max(_F0_MIN, min(self._f0, _F0_MAX))
        ratio = (clamped - _F0_MIN) / (_F0_MAX - _F0_MIN)
        fill_h = int(ratio * bar_h)
        color = self._zone_color(self._f0)
        painter.fillRect(0, bar_h - fill_h, w, fill_h, color)

        # Rolling F0 contour — last ~10 seconds drawn as a white line above the bar
        contour_points = []
        history = list(self._contour)
        n = len(history)
        if n > 1:
            for i, val in enumerate(history):
                if val is not None:
                    x = int(i / (n - 1) * w)
                    c = max(_F0_MIN, min(val, _F0_MAX))
                    r = (c - _F0_MIN) / (_F0_MAX - _F0_MIN)
                    y = int(bar_h - r * bar_h)
                    contour_points.append((x, y))
            if len(contour_points) > 1:
                pen = QPen(QColor(255, 255, 255, 200), 1)
                painter.setPen(pen)
                for i in range(len(contour_points) - 1):
                    painter.drawLine(*contour_points[i], *contour_points[i + 1])
