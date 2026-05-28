"""Top-level application window."""
from __future__ import annotations
import logging
import time
from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QLabel
from PySide6.QtCore import QTimer
from switchedonvoice.audio.capture import AudioCapture
from switchedonvoice.storage.db import init_db
from switchedonvoice.storage.settings import load_settings, save_settings
from switchedonvoice.storage.sessions import create_session, close_session, add_frame, get_streak, get_history_stats, get_all_sessions, update_session_milestones
from switchedonvoice.gamification.milestones import evaluate_milestones, SessionStats, HistoryStats
from switchedonvoice.health import should_warn, WarningLevel
from switchedonvoice.ui.analysis_panel import AnalysisPanel
from switchedonvoice.ui.exercise_panel import ExercisePanel
from switchedonvoice.ui.progress_panel import ProgressPanel
from switchedonvoice.ui.settings_panel import SettingsPanel
from switchedonvoice.onboarding.wizard import OnboardingWizard
import numpy as np

_DB_PATH = Path.home() / ".switchedonvoice" / "data.db"
_SETTINGS_PATH = Path.home() / ".switchedonvoice" / "settings.json"
_TIMER_INTERVAL_MS = 33  # ~30 Hz
_FRAME_DECIMATE_RATE = 5  # store every 5th analysis frame (~6 Hz at 30 Hz analysis)

_logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SwitchedOnVoice")
        self.resize(1100, 700)

        init_db(_DB_PATH)
        self._settings = load_settings(_SETTINGS_PATH)

        if not self._settings.onboarding_complete:
            wizard = OnboardingWizard(settings_path=_SETTINGS_PATH)
            wizard.exec()
            self._settings = load_settings(_SETTINGS_PATH)

        self._capture = AudioCapture(
            device_index=self._settings.device_index,
        )

        self._analysis_panel = AnalysisPanel()
        self._exercise_panel = ExercisePanel()
        self._progress_panel = ProgressPanel(db_path=_DB_PATH)
        self._settings_panel = SettingsPanel(settings_path=_SETTINGS_PATH)
        self._settings_panel.device_changed.connect(self._on_device_changed)

        tabs = QTabWidget()
        tabs.addTab(self._analysis_panel, "Analysis")
        tabs.addTab(self._exercise_panel, "Exercises")
        tabs.addTab(self._progress_panel, "Progress")
        tabs.addTab(self._settings_panel, "Settings")
        self.setCentralWidget(tabs)

        self._status_label = QLabel("")
        status_bar = QStatusBar()
        status_bar.addWidget(self._status_label)
        self.setStatusBar(status_bar)

        self._session_id = create_session(_DB_PATH)
        self._session_start = time.monotonic()
        self._f0_history: list[float] = []
        self._f2_history: list[float] = []
        self._frame_counter = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(_TIMER_INTERVAL_MS)
        self._capture.start()

    def _tick(self) -> None:
        while not self._capture.results.empty():
            try:
                result = self._capture.results.get_nowait()
            except Exception as exc:  # noqa: BLE001
                _logger.debug("Queue drain interrupted: %s", exc)
                break
            self._analysis_panel.update_result(result)

            if result.is_voiced and result.f0 is not None:
                self._f0_history.append(result.f0)
            if result.is_voiced and len(result.formants) >= 2:
                self._f2_history.append(result.formants[1])

            # Decimate storage
            self._frame_counter += 1
            if self._frame_counter % _FRAME_DECIMATE_RATE == 0:
                f1 = result.formants[0] if len(result.formants) >= 1 else None
                f2 = result.formants[1] if len(result.formants) >= 2 else None
                elapsed_ms = int((time.monotonic() - self._session_start) * 1000)
                try:
                    add_frame(_DB_PATH, self._session_id, elapsed_ms,
                              result.f0, f1, f2, result.cpp)
                except Exception as exc:
                    _logger.error("Failed to persist frame: %s", exc, exc_info=True)

        # Vocal health check
        elapsed = time.monotonic() - self._session_start
        level = should_warn(elapsed)
        if level == WarningLevel.RED:
            self._status_label.setText("⚠️  Please rest your voice — you've been training for over 60 minutes.")
        elif level == WarningLevel.YELLOW:
            self._status_label.setText("💛 Consider taking a break — 45 minutes of training completed.")
        else:
            self._status_label.setText("")

    def _on_device_changed(self, device_index: int) -> None:
        self._capture.stop()
        self._settings.device_index = device_index
        save_settings(_SETTINGS_PATH, self._settings)
        try:
            self._capture = AudioCapture(device_index=device_index)
            self._capture.start()
        except Exception as exc:
            _logger.error("Failed to start AudioCapture on device %s: %s", device_index, exc, exc_info=True)
            self._capture = AudioCapture(device_index=None)
            self._capture.start()

    def closeEvent(self, event: object) -> None:  # noqa: ANN001
        self._timer.stop()
        self._capture.stop()

        duration = time.monotonic() - self._session_start
        avg_f0 = float(np.mean(self._f0_history)) if self._f0_history else 0.0
        f0_std = float(np.std(self._f0_history)) if self._f0_history else 0.0
        avg_f2 = float(np.mean(self._f2_history)) if self._f2_history else 0.0

        # IMPORTANT: call close_session() FIRST — this persists the current session
        # to the DB. Only AFTER that do we query get_history_stats() so the current
        # session's contribution is included in milestone evaluation.
        # The session is initially closed with empty flags; we update them below.
        try:
            close_session(_DB_PATH, self._session_id, duration, avg_f0, f0_std, avg_f2,
                          milestone_flags={})

            # Now query history — current session is included
            session_stats = SessionStats(avg_f0=avg_f0, f0_std_dev=f0_std,
                                         avg_f2=avg_f2, duration_secs=duration)
            streak = get_streak(_DB_PATH)
            baseline_f2 = self._settings.baseline_f2 or 1400.0
            agg = get_history_stats(_DB_PATH, baseline_f2=baseline_f2)
            all_sessions = get_all_sessions(_DB_PATH)
            history = HistoryStats(
                total_sessions=len(all_sessions),
                streak=streak,
                total_practice_secs=agg.total_practice_secs,
                f2_above_baseline_streak=agg.f2_above_baseline_streak,
                f0_above_165_sessions=agg.f0_above_165_sessions,
                f0_above_185_sessions=agg.f0_above_185_sessions,
                baseline_f2=baseline_f2,
            )
            earned = evaluate_milestones(session_stats, history)
            # Always call update_session_milestones — back-fills flags even if none were earned
            # (empty dict is correct; it replaces the placeholder '{}' set by close_session above)
            flags = {m.value: True for m in earned}
            update_session_milestones(_DB_PATH, self._session_id, flags)
        except Exception as exc:
            _logger.error("Failed to persist session on close: %s", exc, exc_info=True)

        self._progress_panel.refresh()
        super().closeEvent(event)  # type: ignore[arg-type]
