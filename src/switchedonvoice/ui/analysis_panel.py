"""Analysis panel: composes pitch meter, waveform, vowel space, spectrum, and CPP label."""
from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
from switchedonvoice.audio.capture import AnalysisResult
from switchedonvoice.ui.pitch_meter import PitchMeterWidget
from switchedonvoice.ui.spectrum_widget import SpectrumWidget
from switchedonvoice.ui.vowel_space import VowelSpaceWidget
from switchedonvoice.ui.waveform_widget import WaveformWidget

_CPP_TOOLTIP = (
    "Cepstral Peak Prominence — a measure of voice quality and phonation regularity.\n"
    "Higher = more periodic / less breathy. "
    "Provided as an observation only; no target is set."
)


class AnalysisPanel(QWidget):
    """Main analysis display: pitch meter, waveform, vowel space, spectrum, and CPP."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pitch = PitchMeterWidget()
        self._waveform = WaveformWidget()
        self._vowel = VowelSpaceWidget()
        self._spectrum = SpectrumWidget()
        self._cpp_label = QLabel("CPP: —")
        self._cpp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cpp_label.setToolTip(_CPP_TOOLTIP)

        left = QVBoxLayout()
        left.addWidget(self._pitch)
        left.addWidget(self._cpp_label)
        left.addWidget(self._waveform)

        layout = QHBoxLayout(self)
        layout.addLayout(left)
        layout.addWidget(self._vowel, stretch=2)
        layout.addWidget(self._spectrum, stretch=3)

    def update_result(self, result: AnalysisResult) -> None:
        """Dispatch a new analysis frame to all child widgets.

        Note: Must be called from the GUI thread.

        Args:
            result: Analysis result from the audio pipeline.
        """
        self._pitch.set_f0(result.f0)
        if result.raw_audio is not None:
            self._waveform.update_waveform(result.raw_audio)
        if result.is_voiced and len(result.formants) >= 2:
            self._vowel.add_frame(f1=result.formants[0], f2=result.formants[1])
        if result.cpp is not None:
            self._cpp_label.setText(f"CPP: {result.cpp:.1f} dB")
        else:
            self._cpp_label.setText("CPP: —")
        self._spectrum.update_spectrum(result.spectrum_freqs, result.spectrum_db)
