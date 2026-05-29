# tests/ui/test_exercise_panel.py
"""Tests for ExerciseCard timer state machine.

Covers: Start→Stop transition, countdown runs, completion reset,
and manual Stop before completion.
"""
import sys
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from switchedonvoice.ui.exercise_panel import ExerciseCard, EXERCISES

_app = QApplication.instance() or QApplication(sys.argv)


@pytest.fixture()
def timed_card(qtbot):
    """Return an ExerciseCard for 'Pitch Slide' (30 s timer)."""
    card = ExerciseCard(EXERCISES[0])  # "Pitch Slide", duration=30
    qtbot.addWidget(card)
    return card


def test_start_button_initial_label(timed_card) -> None:
    assert timed_card.start_button.text() == "Start"


def test_clicking_start_changes_label_to_stop(qtbot, timed_card) -> None:
    qtbot.mouseClick(timed_card.start_button, Qt.LeftButton)
    assert timed_card.start_button.text() == "Stop"


def test_clicking_stop_before_completion_resets_to_start(qtbot, timed_card) -> None:
    qtbot.mouseClick(timed_card.start_button, Qt.LeftButton)  # → Stop
    qtbot.mouseClick(timed_card.start_button, Qt.LeftButton)  # → Start (manual stop)
    assert timed_card.start_button.text() == "Start"
    # Countdown label should also reset to initial duration
    assert "30" in timed_card.countdown_label.text()
    # Completion message must NOT be visible after a manual stop
    assert not timed_card.completion_label.isVisible()


def test_timer_completion_resets_to_start(qtbot, timed_card) -> None:
    """When the QTimer fires (duration reached), button resets to 'Start'."""
    qtbot.mouseClick(timed_card.start_button, Qt.LeftButton)  # start
    # Directly invoke the timeout handler to simulate expiry without waiting 30s
    timed_card._on_timer_complete()
    assert timed_card.start_button.text() == "Start"
    assert "30" in timed_card.countdown_label.text()
    # Completion message MUST be visible after natural timer expiry
    assert timed_card.completion_label.isVisible()


def test_rapid_start_stop_start_does_not_corrupt_state(qtbot, timed_card) -> None:
    """Rapid Start→Stop→Start should not restart the timer from scratch mid-countdown."""
    qtbot.mouseClick(timed_card.start_button, Qt.LeftButton)  # Start
    qtbot.mouseClick(timed_card.start_button, Qt.LeftButton)  # Stop (manual)
    qtbot.mouseClick(timed_card.start_button, Qt.LeftButton)  # Start again
    # After a clean start, button should be "Stop" and timer running
    assert timed_card.start_button.text() == "Stop"
    assert timed_card._timer.isActive()
