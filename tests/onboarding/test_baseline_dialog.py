"""Smoke test for BaselineRecordingDialog."""
import pytest


def test_baseline_dialog_constructs(qtbot):
    from switchedonvoice.onboarding.baseline_dialog import BaselineRecordingDialog
    dlg = BaselineRecordingDialog(device_index=None)
    qtbot.addWidget(dlg)
    assert dlg is not None
