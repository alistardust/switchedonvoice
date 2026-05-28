"""Cepstral Peak Prominence (CPP) computation.

CPP is the difference between the cepstral peak in the voiced range
(2ms–15ms, i.e., 66–500 Hz) and the linear regression trend at that
quefrency. Higher CPP = more periodic / less breathy voice.

Displayed as observation only — no target is set, no pass/fail.
"""
from __future__ import annotations
import numpy as np

_QUEFRENCY_MIN_MS = 2.0    # 500 Hz
_QUEFRENCY_MAX_MS = 15.0   # 66 Hz


def compute_cpp(audio: np.ndarray, sample_rate: int) -> float | None:
    """Compute Cepstral Peak Prominence of an audio frame.

    Args:
        audio: Float32 audio samples.
        sample_rate: Sample rate in Hz.

    Returns:
        CPP value in dB, or None if the frame is silent.
    """
    if np.max(np.abs(audio)) < 1e-6:
        return None

    # Power spectrum → log → IFFT = cepstrum
    spectrum = np.fft.rfft(audio.astype(np.float64))
    log_power = np.log(np.abs(spectrum) ** 2 + 1e-12)
    cepstrum = np.fft.irfft(log_power).real

    # Quefrency axis (in ms)
    n_samples = len(cepstrum)
    quefrency_ms = np.arange(n_samples) / sample_rate * 1000

    min_q = _QUEFRENCY_MIN_MS
    max_q = _QUEFRENCY_MAX_MS
    mask = (quefrency_ms >= min_q) & (quefrency_ms <= max_q)
    if not np.any(mask):
        return None

    region = cepstrum[mask]
    q_vals = quefrency_ms[mask]

    # Peak value
    peak_idx = int(np.argmax(region))
    peak_val = float(region[peak_idx])

    # Linear regression trend across the region
    coeffs = np.polyfit(q_vals, region, 1)
    trend_at_peak = float(np.polyval(coeffs, q_vals[peak_idx]))

    cpp = peak_val - trend_at_peak
    return cpp
