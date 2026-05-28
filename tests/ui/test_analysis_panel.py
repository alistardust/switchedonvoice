# tests/ui/test_analysis_panel.py
"""Smoke tests for AnalysisPanel."""
import sys
import numpy as np
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from switchedonvoice.ui.analysis_panel import AnalysisPanel
from switchedonvoice.audio.capture import AnalysisResult

_app = QApplication.instance() or QApplication(sys.argv)


def test_panel_constructs() -> None:
    assert AnalysisPanel() is not None


def test_update_voiced_result() -> None:
    panel = AnalysisPanel()
    result = AnalysisResult(
        f0=200.0, formants=[500.0, 1800.0, 2700.0], cpp=12.0,
        is_voiced=True,
        spectrum_freqs=np.linspace(0, 22050, 2049, dtype=np.float32),
        spectrum_db=np.full(2049, -40.0, dtype=np.float32),
    )
    panel.update_result(result)


def test_update_unvoiced_result() -> None:
    panel = AnalysisPanel()
    result = AnalysisResult(
        f0=None, formants=[], cpp=None,
        is_voiced=False,
        spectrum_freqs=np.linspace(0, 22050, 2049, dtype=np.float32),
        spectrum_db=np.full(2049, -80.0, dtype=np.float32),
    )
    panel.update_result(result)


def test_update_with_empty_waveform() -> None:
    panel = AnalysisPanel()
    result = AnalysisResult(
        f0=None, formants=[], cpp=None, is_voiced=False,
        spectrum_freqs=np.linspace(0, 22050, 2049, dtype=np.float32),
        spectrum_db=np.full(2049, -80.0, dtype=np.float32),
        raw_audio=np.zeros(0, dtype=np.float32),
    )
    panel.update_result(result)  # must not raise


def test_update_with_nan_waveform() -> None:
    panel = AnalysisPanel()
    raw = np.array([0.5, float("nan"), 0.3], dtype=np.float32)
    result = AnalysisResult(
        f0=200.0, formants=[500.0, 1800.0], cpp=12.0, is_voiced=True,
        spectrum_freqs=np.linspace(0, 22050, 2049, dtype=np.float32),
        spectrum_db=np.full(2049, -40.0, dtype=np.float32),
        raw_audio=raw,
    )
    panel.update_result(result)  # must not raise
