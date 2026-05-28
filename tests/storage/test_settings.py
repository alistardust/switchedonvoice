# tests/storage/test_settings.py
"""Tests for settings.json read/write."""
from pathlib import Path
import pytest
from switchedonvoice.storage.settings import Settings, load_settings, save_settings


@pytest.fixture()
def settings_path(tmp_path: Path) -> Path:
    return tmp_path / "settings.json"


def test_load_missing_returns_defaults(settings_path: Path) -> None:
    s = load_settings(settings_path)
    assert isinstance(s, Settings)
    assert s.device_index is None
    assert s.onboarding_complete is False


def test_save_and_reload(settings_path: Path) -> None:
    s = Settings(device_index=2, onboarding_complete=True,
                 baseline_f0=180.0, baseline_f0_std_dev=20.0, baseline_f2=1750.0)
    save_settings(settings_path, s)
    loaded = load_settings(settings_path)
    assert loaded.device_index == 2
    assert loaded.onboarding_complete is True
    assert loaded.baseline_f0 == pytest.approx(180.0)
    assert loaded.baseline_f0_std_dev == pytest.approx(20.0)
    assert loaded.baseline_f2 == pytest.approx(1750.0)


def test_save_is_valid_json(settings_path: Path) -> None:
    save_settings(settings_path, Settings())
    import json
    data = json.loads(settings_path.read_text())
    assert "device_index" in data
