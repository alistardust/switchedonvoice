"""5-step onboarding wizard.

Steps:
    1. Mic permission  — info page (no action on Linux)
    2. Mic selector    — device QComboBox
    3. Ambient cal     — 10-second silence countdown, saves noise_floor_rms
    4. Baseline record — 30-second speech recording, saves F0/F2 stats
    5. Done            — summary and "Start training" button
"""
from __future__ import annotations

import logging
from pathlib import Path

import sounddevice as sd
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWizard,
    QWizardPage,
    QWidget,
)

from switchedonvoice.storage.settings import Settings, load_settings, save_settings
from switchedonvoice.ui.pitch_meter import PitchMeterWidget

_logger = logging.getLogger(__name__)

_AMBIENT_DURATION_SECS: int = 10
_BASELINE_DURATION_SECS: int = 30


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #


class _MicPermissionPage(QWizardPage):
    """Step 1: Explain microphone requirements."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle("Microphone Permission")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "SwitchedOnVoice needs access to your microphone.\n\n"
            "On Linux, microphone access is granted automatically. "
            "No action is needed.\n\n"
            "Click Next to continue."
        ))


class _MicSelectorPage(QWizardPage):
    """Step 2: Select audio input device."""

    def __init__(self, settings: Settings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self.setTitle("Select Microphone")
        self._combo = QComboBox()
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._populate)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Choose your microphone:"))
        layout.addWidget(self._combo)
        layout.addWidget(self._refresh_btn)
        self._populate()

    def _populate(self) -> None:
        """Populate device list from sounddevice."""
        self._combo.clear()
        try:
            devices = sd.query_devices()
        except (sd.PortAudioError, OSError) as exc:
            _logger.warning("Failed to query devices: %s", exc)
            self._combo.addItem("(no devices found)", userData=-1)
            return
        for i, dev in enumerate(devices):
            if isinstance(dev, dict) and dev.get("max_input_channels", 0) > 0:
                name = dev.get("name", "Unknown Device")
                channels = dev.get("max_input_channels", 0)
                self._combo.addItem(f"{name} (in: {channels}ch)", userData=dev.get("index", i))
        if self._combo.count() == 0:
            self._combo.addItem("(no input devices found)", userData=-1)

    def selected_device_index(self) -> int | None:
        """Return the selected device index, or None if none."""
        idx = self._combo.currentData()
        if isinstance(idx, int) and idx >= 0:
            return idx
        return None


class _AmbientCalPage(QWizardPage):
    """Step 3: Capture ambient noise floor."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle("Ambient Calibration")
        self._noise_floor: float | None = None

        self._instructions = QLabel(
            "Please remain silent for 10 seconds while we measure "
            "the background noise level in your environment."
        )
        self._instructions.setWordWrap(True)

        self._progress = QProgressBar()
        self._progress.setRange(0, _AMBIENT_DURATION_SECS)
        self._progress.setValue(0)

        self._status = QLabel("Click 'Start' when you are ready.")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._start_btn = QPushButton("Start")
        self._start_btn.clicked.connect(self._start)

        self._elapsed = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        layout = QVBoxLayout(self)
        layout.addWidget(self._instructions)
        layout.addWidget(self._progress)
        layout.addWidget(self._status)
        layout.addWidget(self._start_btn)

    def _start(self) -> None:
        """Begin ambient calibration countdown."""
        if self._timer.isActive():
            return
        self._start_btn.setEnabled(False)
        self._elapsed = 0
        self._timer.start()

    def _tick(self) -> None:
        """Advance countdown by one second."""
        self._elapsed += 1
        self._progress.setValue(self._elapsed)
        self._status.setText(f"Recording… {_AMBIENT_DURATION_SECS - self._elapsed}s remaining")
        if self._elapsed >= _AMBIENT_DURATION_SECS:
            self._timer.stop()
            # Placeholder RMS — real capture wired in Task 24
            self._noise_floor = 0.002
            self._status.setText("Calibration complete. Click Next.")
            self.completeChanged.emit()

    def isComplete(self) -> bool:
        """Page is complete once ambient calibration has run."""
        return self._noise_floor is not None

    def noise_floor_rms(self) -> float | None:
        """Return captured noise floor RMS, or None if not yet calibrated."""
        return self._noise_floor

    def cleanupPage(self) -> None:
        """Stop timer and reset state when navigating away from this page."""
        self._timer.stop()
        super().cleanupPage()


class _BaselineRecordPage(QWizardPage):
    """Step 4: Record 30-second vocal baseline."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle("Vocal Baseline Recording")
        self._baseline_done = False

        self._instructions = QLabel(
            "Speak naturally for 30 seconds. Read a passage aloud, "
            "count, or have a conversation. This baseline will calibrate "
            "your pitch meter and progress tracking."
        )
        self._instructions.setWordWrap(True)

        self._progress = QProgressBar()
        self._progress.setRange(0, _BASELINE_DURATION_SECS)
        self._progress.setValue(0)

        self._pitch_meter = PitchMeterWidget()

        self._status = QLabel("Click 'Start Recording' when ready.")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._record_btn = QPushButton("Start Recording")
        self._record_btn.clicked.connect(self._start)

        self._elapsed = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        # Placeholder baseline values — real capture wired in Task 24
        self._baseline_f0: float | None = None
        self._baseline_f0_std: float | None = None
        self._baseline_f2: float | None = None
        self._baseline_f2_std: float | None = None

        layout = QVBoxLayout(self)
        layout.addWidget(self._instructions)
        layout.addWidget(self._progress)
        layout.addWidget(self._pitch_meter)
        layout.addWidget(self._status)
        layout.addWidget(self._record_btn)

    def _start(self) -> None:
        """Begin baseline recording countdown."""
        if self._timer.isActive():
            return
        self._record_btn.setEnabled(False)
        self._elapsed = 0
        self._timer.start()

    def _tick(self) -> None:
        """Advance countdown by one second."""
        self._elapsed += 1
        self._progress.setValue(self._elapsed)
        self._status.setText(f"Recording… {_BASELINE_DURATION_SECS - self._elapsed}s remaining")
        if self._elapsed >= _BASELINE_DURATION_SECS:
            self._timer.stop()
            # Placeholder baselines — real AudioCapture wired in Task 24
            self._baseline_f0 = 175.0
            self._baseline_f0_std = 20.0
            self._baseline_f2 = 1700.0
            self._baseline_f2_std = 145.0
            self._baseline_done = True
            self._status.setText("Recording complete. Click Next.")
            self.completeChanged.emit()

    def isComplete(self) -> bool:
        """Page is complete once baseline recording has run."""
        return self._baseline_done

    def baseline_values(self) -> tuple[float | None, float | None, float | None, float | None]:
        """Return (avg_f0, f0_std, avg_f2, f2_std), or Nones if not yet recorded."""
        return (
            self._baseline_f0,
            self._baseline_f0_std,
            self._baseline_f2,
            self._baseline_f2_std,
        )

    def cleanupPage(self) -> None:
        """Stop timer and reset state when navigating away from this page."""
        self._timer.stop()
        super().cleanupPage()


class _DonePage(QWizardPage):
    """Step 5: Summary and completion."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle("You're Ready!")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Setup complete! Your baseline has been saved.\n\n"
            "Click 'Start training' to begin your voice training journey."
        ))


# --------------------------------------------------------------------------- #
# Wizard
# --------------------------------------------------------------------------- #


class OnboardingWizard(QWizard):
    """5-step onboarding wizard for SwitchedOnVoice.

    Guides the user through microphone setup, ambient calibration,
    and baseline recording. Emits wizard_complete on acceptance.
    """

    wizard_complete = Signal()

    _PAGE_MIC_PERMISSION = 0
    _PAGE_MIC_SELECTOR = 1
    _PAGE_AMBIENT_CAL = 2
    _PAGE_BASELINE = 3
    _PAGE_DONE = 4

    def __init__(
        self,
        settings_path: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings_path = settings_path
        self._settings: Settings = (
            load_settings(settings_path) if settings_path else load_settings()
        )

        self.setWindowTitle("SwitchedOnVoice Setup")
        self.setMinimumSize(480, 360)

        self._mic_selector_page = _MicSelectorPage(self._settings)
        self._ambient_page = _AmbientCalPage()
        self._baseline_page = _BaselineRecordPage()

        self.addPage(_MicPermissionPage())
        self.addPage(self._mic_selector_page)
        self.addPage(self._ambient_page)
        self.addPage(self._baseline_page)
        self.addPage(_DonePage())

        self.setButtonText(QWizard.WizardButton.FinishButton, "Start training")

    def accept(self) -> None:
        """Persist settings, emit wizard_complete, then close.

        Note: wizard_complete is emitted before super().accept() so that
        connected slots receive it before the window is hidden.
        """
        try:
            self._persist_results()
        except Exception as exc:
            _logger.error("Failed to save onboarding settings: %s", exc, exc_info=True)
            return  # leave wizard open; user can retry
        self.wizard_complete.emit()
        super().accept()

    # ---------------------------------------------------------------------- #
    # Private
    # ---------------------------------------------------------------------- #

    def _persist_results(self) -> None:
        """Write calibration and baseline results to settings file."""
        # Reload to pick up any pre-written values (e.g. from test fixtures)
        if self._settings_path and self._settings_path.exists():
            self._settings = load_settings(self._settings_path)

        # Apply device selection
        device_idx = self._mic_selector_page.selected_device_index()
        if device_idx is not None:
            self._settings.device_index = device_idx

        # Apply ambient calibration
        noise_floor = self._ambient_page.noise_floor_rms()
        if noise_floor is not None:
            self._settings.noise_floor_rms = noise_floor

        # Apply baseline
        f0, f0_std, f2, f2_std = self._baseline_page.baseline_values()
        if f0 is not None:
            self._settings.baseline_f0 = f0
        if f0_std is not None:
            self._settings.baseline_f0_std_dev = f0_std
        if f2 is not None:
            self._settings.baseline_f2 = f2
        if f2_std is not None:
            self._settings.baseline_f2_std_dev = f2_std

        self._settings.onboarding_complete = True

        if self._settings_path:
            save_settings(self._settings_path, self._settings)
        else:
            save_settings(settings=self._settings)

