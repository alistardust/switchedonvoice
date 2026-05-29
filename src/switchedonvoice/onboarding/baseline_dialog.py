"""Reusable baseline recording dialog.

Used by both the onboarding wizard and the settings panel.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_RECORD_DURATION_SECS: int = 30
_INSTRUCTIONS = (
    "Speak naturally for 30 seconds. "
    "This baseline will calibrate your pitch meter and progress tracking."
)


class BaselineRecordingDialog(QDialog):
    """Modal dialog for recording a 30-second vocal baseline.

    Captures audio, computes mean F0, F0 std dev, and mean F2 from voiced
    frames, then updates settings via save_settings.

    Note: In Phase 1 the recording is simulated (no live audio in dialog context).
    Full recording is wired in Task 24 (MainWindow integration).
    """

    def __init__(
        self,
        device_index: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._device_index = device_index
        self.setWindowTitle("Record Vocal Baseline")
        self.setModal(True)
        self.setMinimumWidth(360)

        self._instructions = QLabel(_INSTRUCTIONS)
        self._instructions.setWordWrap(True)
        self._instructions.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._progress = QProgressBar()
        self._progress.setRange(0, _RECORD_DURATION_SECS)
        self._progress.setValue(0)

        self._status_label = QLabel("Ready to record.")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._record_button = QPushButton("Start Recording")
        self._record_button.clicked.connect(self._on_record_clicked)

        self._close_button = QPushButton("Close")
        self._close_button.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self._instructions)
        layout.addWidget(self._progress)
        layout.addWidget(self._status_label)
        layout.addWidget(self._record_button)
        layout.addWidget(self._close_button)

    def _on_record_clicked(self) -> None:
        """Handle record button click — placeholder for Task 24 wiring."""
        self._record_button.setEnabled(False)
        self._status_label.setText(
            "Recording… (live audio capture wired in Task 24)"
        )

