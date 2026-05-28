# tests/ui/test_vowel_space.py
"""Smoke tests for VowelSpaceWidget."""
import sys
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from switchedonvoice.ui.vowel_space import VowelSpaceWidget

_app = QApplication.instance() or QApplication(sys.argv)


def test_widget_constructs() -> None:
    w = VowelSpaceWidget()
    assert w is not None


def test_add_frame_does_not_raise() -> None:
    w = VowelSpaceWidget()
    w.add_frame(f1=500.0, f2=1800.0)


def test_clear_does_not_raise() -> None:
    w = VowelSpaceWidget()
    w.add_frame(500.0, 1800.0)
    w.clear()
