"""Smoke test for MainWindow."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PySide6.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)


def test_main_window_constructs(tmp_path: Path) -> None:
    """MainWindow constructs without crashing."""
    from switchedonvoice.ui.main_window import MainWindow
    from PySide6.QtWidgets import QWidget

    # Patch all I/O so test doesn't need real audio or DB
    with (
        patch("switchedonvoice.ui.main_window.init_db"),
        patch("switchedonvoice.ui.main_window.load_settings") as mock_settings,
        patch("switchedonvoice.ui.main_window.create_session", return_value=1),
        patch("switchedonvoice.ui.main_window.AudioCapture") as mock_capture,
        patch("switchedonvoice.ui.main_window.OnboardingWizard"),
        patch("switchedonvoice.ui.main_window.AnalysisPanel") as mock_analysis,
        patch("switchedonvoice.ui.main_window.ExercisePanel") as mock_exercise,
        patch("switchedonvoice.ui.main_window.ProgressPanel") as mock_progress,
        patch("switchedonvoice.ui.main_window.SettingsPanel") as mock_settings_panel,
    ):
        mock_settings.return_value = MagicMock(
            onboarding_complete=True,
            device_index=None,
            baseline_f2=None,
        )
        mock_capture.return_value.results = MagicMock()
        mock_capture.return_value.results.empty.return_value = True
        
        # Create actual QWidget instances for panels (PySide6 requires real Qt types)
        mock_analysis.return_value = QWidget()
        mock_analysis.return_value.update_result = MagicMock()
        mock_exercise.return_value = QWidget()
        mock_progress.return_value = QWidget()
        mock_progress.return_value.refresh = MagicMock()
        settings_widget = QWidget()
        settings_widget.device_changed = MagicMock()
        settings_widget.device_changed.connect = MagicMock()
        mock_settings_panel.return_value = settings_widget

        win = MainWindow()
        assert win is not None
        win._timer.stop()
        win._capture.stop()
