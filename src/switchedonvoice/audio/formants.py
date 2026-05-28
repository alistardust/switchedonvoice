"""Formant frequency estimation via LPC (librosa.lpc + numpy.roots).

Pipeline:
  1. Pre-emphasise the signal.
  2. Apply a Hamming window.
  3. Fit LPC coefficients.
  4. Find roots of the LPC polynomial.
  5. Keep roots inside the unit circle with positive imaginary part.
  6. Filter by bandwidth < 500 Hz and frequency in speech range.
  7. Return sorted formant frequencies in Hz.
"""
from __future__ import annotations
import numpy as np
import librosa

# Validated empirically in Spike 2 — change if spike results differ
LPC_ORDER: int = 14
_MIN_FREQ_HZ: float = 90.0
_MAX_BANDWIDTH_HZ: float = 500.0
_PRE_EMPHASIS: float = 0.97


def estimate_formants(audio: np.ndarray, sample_rate: int) -> list[float]:
    """Estimate formant frequencies from a voiced audio frame.

    Args:
        audio: Float32 audio samples at sample_rate.
        sample_rate: Sample rate in Hz. Recommend 16 kHz for LPC.

    Returns:
        Sorted list of formant frequencies in Hz (F1, F2, F3 ...).
        Returns empty list if audio is silent or no valid formants found.
    """
    if np.max(np.abs(audio)) < 1e-6:
        return []

    # Pre-emphasis to boost high-frequency content
    emphasised = np.append(audio[0], audio[1:] - _PRE_EMPHASIS * audio[:-1])
    windowed = emphasised * np.hamming(len(emphasised))

    lpc_coeffs = librosa.lpc(windowed.astype(np.float32), order=LPC_ORDER)
    roots = np.roots(lpc_coeffs)

    # Only roots inside unit circle with positive imaginary part
    roots = roots[np.abs(roots) < 1.0]
    roots = roots[roots.imag > 0]

    if len(roots) == 0:
        return []

    angles = np.angle(roots)
    freqs_hz = angles * sample_rate / (2 * np.pi)
    bandwidths_hz = -np.log(np.abs(roots)) * sample_rate / np.pi

    max_freq = sample_rate / 2 - 100
    mask = (
        (freqs_hz > _MIN_FREQ_HZ)
        & (freqs_hz < max_freq)
        & (bandwidths_hz < _MAX_BANDWIDTH_HZ)
    )
    formants = sorted(freqs_hz[mask].tolist())
    return formants
