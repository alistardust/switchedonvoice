# tests/ui/test_spectrum_widget.py
"""Smoke tests for SpectrumWidget."""
import sys
import numpy as np
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from switchedonvoice.ui.spectrum_widget import SpectrumWidget

_app = QApplication.instance() or QApplication(sys.argv)


def test_widget_constructs() -> None:
    assert SpectrumWidget() is not None


def test_update_spectrum_does_not_raise() -> None:
    w = SpectrumWidget()
    freqs = np.linspace(0, 22050, 2049).astype(np.float32)
    db = np.random.uniform(-80, 0, 2049).astype(np.float32)
    w.update_spectrum(freqs, db)
