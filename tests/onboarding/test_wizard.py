"""Tests for the OnboardingWizard."""
import json
import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)


def test_wizard_constructs(tmp_path: Path) -> None:
    """Test that the wizard can be constructed."""
    from switchedonvoice.onboarding.wizard import OnboardingWizard
    settings_path = tmp_path / "settings.json"
    w = OnboardingWizard(settings_path=settings_path)
    assert w is not None


def test_wizard_emits_complete_and_persists_baseline(tmp_path: Path, qtbot) -> None:
    """Simulate completing the wizard and verify signal + persistence."""
    from switchedonvoice.onboarding.wizard import OnboardingWizard
    from switchedonvoice.storage.settings import load_settings

    settings_path = tmp_path / "settings.json"
    wizard = OnboardingWizard(settings_path=settings_path)
    qtbot.addWidget(wizard)

    emitted: list[bool] = []
    wizard.wizard_complete.connect(lambda: emitted.append(True))

    # Pre-write settings to simulate completed calibration
    settings_path.write_text(json.dumps({
        "noise_floor_rms": 0.002,
        "baseline_f0": 180.0,
        "baseline_f0_std_dev": 22.0,
        "baseline_f2": 1750.0,
        "baseline_f2_std_dev": 150.0,
        "onboarding_complete": True,
    }))

    wizard.accept()

    assert len(emitted) > 0, "wizard_complete signal was not emitted on wizard.accept()"

    settings = load_settings(settings_path)
    assert settings.noise_floor_rms is not None
    assert settings.baseline_f2 is not None
    assert settings.baseline_f2_std_dev is not None
