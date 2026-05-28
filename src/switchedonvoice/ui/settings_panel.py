"""Device selection and application settings panel."""
from __future__ import annotations

import logging
from pathlib import Path

import sounddevice as sd
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from switchedonvoice.storage.settings import Settings, load_settings, save_settings

_logger = logging.getLogger(__name__)

_DEFAULT_F0_TARGET_MIN: int = 185
_DEFAULT_F0_TARGET_MAX: int = 255


class SettingsPanel(QWidget):
    """Settings panel: device selector, F0 target range, and baseline re-record."""

    device_changed = Signal(int)  # emits new device_index when saved

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

        # --- Device selector ---
        device_group = QGroupBox("Audio Device")
        self._device_combo = QComboBox()
        self._refresh_button = QPushButton("Refresh")
        self._refresh_button.clicked.connect(self._populate_devices)

        device_row = QHBoxLayout()
        device_row.addWidget(self._device_combo, stretch=1)
        device_row.addWidget(self._refresh_button)

        device_layout = QVBoxLayout(device_group)
        device_layout.addLayout(device_row)

        # --- F0 target range ---
        f0_group = QGroupBox("F0 Target Range")
        self._f0_min_spin = QSpinBox()
        self._f0_min_spin.setRange(80, 400)
        self._f0_min_spin.setSuffix(" Hz")
        self._f0_min_spin.setValue(int(self._settings.f0_target_min))

        self._f0_max_spin = QSpinBox()
        self._f0_max_spin.setRange(80, 800)
        self._f0_max_spin.setSuffix(" Hz")
        self._f0_max_spin.setValue(int(self._settings.f0_target_max))

        f0_form = QFormLayout(f0_group)
        f0_form.addRow("F0 target min (Hz):", self._f0_min_spin)
        f0_form.addRow("F0 target max (Hz):", self._f0_max_spin)

        # --- Baseline ---
        baseline_group = QGroupBox("Vocal Baseline")
        self._baseline_button = QPushButton("Re-record baseline")
        self._baseline_button.clicked.connect(self._open_baseline_dialog)

        baseline_layout = QVBoxLayout(baseline_group)
        baseline_layout.addWidget(self._baseline_button)

        # --- Save ---
        self._save_button = QPushButton("Save Settings")
        self._save_button.clicked.connect(self._on_save)

        layout = QVBoxLayout(self)
        layout.addWidget(device_group)
        layout.addWidget(f0_group)
        layout.addWidget(baseline_group)
        layout.addWidget(self._save_button)
        layout.addStretch()

        self._populate_devices()

    # ---------------------------------------------------------------------- #
    # Private
    # ---------------------------------------------------------------------- #

    def _populate_devices(self) -> None:
        """Query sounddevice and repopulate the device combo box."""
        self._device_combo.clear()
        try:
            devices = sd.query_devices()
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Failed to query audio devices: %s", exc)
            self._device_combo.addItem("(no devices found)", userData=-1)
            return

        current_idx = self._settings.device_index
        select_row = 0
        for i, dev in enumerate(devices):
            if isinstance(dev, dict) and dev.get("max_input_channels", 0) > 0:
                label = f"{dev['name']} (in: {dev['max_input_channels']}ch)"
                self._device_combo.addItem(label, userData=dev.get("index", i))
                if dev.get("index", i) == current_idx:
                    select_row = self._device_combo.count() - 1

        if self._device_combo.count() == 0:
            self._device_combo.addItem("(no input devices found)", userData=-1)
        else:
            self._device_combo.setCurrentIndex(select_row)

    def _on_save(self) -> None:
        """Persist settings and emit device_changed if device was updated."""
        f0_min = float(self._f0_min_spin.value())
        f0_max = float(self._f0_max_spin.value())
        if f0_min >= f0_max:
            _logger.warning(
                "F0 target min (%s) must be less than max (%s) — save aborted",
                f0_min,
                f0_max,
            )
            return

        new_device_idx = self._device_combo.currentData()
        if not isinstance(new_device_idx, int) or new_device_idx < 0:
            new_device_idx = None

        old_device = self._settings.device_index
        self._settings.device_index = new_device_idx
        self._settings.f0_target_min = f0_min
        self._settings.f0_target_max = f0_max

        if self._settings_path:
            save_settings(self._settings_path, self._settings)
        else:
            save_settings(settings=self._settings)

        if new_device_idx is not None and new_device_idx != old_device:
            self.device_changed.emit(new_device_idx)

    def _open_baseline_dialog(self) -> None:
        """Open the baseline recording dialog."""
        from switchedonvoice.onboarding.baseline_dialog import BaselineRecordingDialog
        device_idx = self._device_combo.currentData()
        if not isinstance(device_idx, int) or device_idx < 0:
            device_idx = None
        dlg = BaselineRecordingDialog(device_index=device_idx, parent=self)
        dlg.exec()

