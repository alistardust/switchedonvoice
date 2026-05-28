"""Tests for vocal health warning logic."""
import pytest
from switchedonvoice.health import should_warn, WarningLevel


def test_no_warning_under_45_minutes() -> None:
    assert should_warn(elapsed_secs=2699) == WarningLevel.NONE


def test_yellow_warning_at_45_minutes() -> None:
    assert should_warn(elapsed_secs=2700) == WarningLevel.YELLOW


def test_red_warning_at_60_minutes() -> None:
    assert should_warn(elapsed_secs=3600) == WarningLevel.RED


def test_red_warning_persists_after_60_minutes() -> None:
    assert should_warn(elapsed_secs=4000) == WarningLevel.RED


def test_negative_elapsed_secs_raises() -> None:
    with pytest.raises(ValueError):
        should_warn(elapsed_secs=-1)
