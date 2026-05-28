# tests/ui/test_pitch_meter.py
"""Smoke tests for PitchMeterWidget."""
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from switchedonvoice.ui.pitch_meter import PitchMeterWidget

import sys
_app = QApplication.instance() or QApplication(sys.argv)


def test_widget_constructs() -> None:
    w = PitchMeterWidget()
    assert w is not None


def test_set_f0_in_green_zone() -> None:
    w = PitchMeterWidget()
    w.set_f0(200.0)   # should not raise


def test_set_f0_none_clears_display() -> None:
    w = PitchMeterWidget()
    w.set_f0(None)    # no voiced frame — display should clear


def test_zone_for_green() -> None:
    from switchedonvoice.ui.pitch_meter import f0_zone_color
    color = f0_zone_color(200.0)
    assert color is not None


def test_zone_boundaries_all_5_zones() -> None:
    from switchedonvoice.ui.pitch_meter import f0_zone_color
    from PySide6.QtGui import QColor
    # Deep red: < 120
    assert f0_zone_color(100.0) == QColor(120, 0, 0)
    # Red: 120–164
    assert f0_zone_color(140.0) == QColor(200, 60, 60)
    assert f0_zone_color(120.0) == QColor(200, 60, 60)   # boundary: 120 is red
    # Yellow: 165–184
    assert f0_zone_color(165.0) == QColor(220, 200, 60)
    assert f0_zone_color(180.0) == QColor(220, 200, 60)
    # Green: 185–255
    assert f0_zone_color(185.0) == QColor(60, 200, 100)
    assert f0_zone_color(255.0) == QColor(60, 200, 100)  # 255 still green
    # Blue: > 255 (head voice — valid, not a warning)
    assert f0_zone_color(256.0) == QColor(80, 160, 255)
    assert f0_zone_color(400.0) == QColor(80, 160, 255)
