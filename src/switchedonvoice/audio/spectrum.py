"""FFT-based spectrum analysis using numpy directly.

Does NOT use librosa — librosa adds import overhead and has no streaming API.
numpy.fft.rfft is used directly for low-latency operation in the hot path.
"""
from __future__ import annotations
import numpy as np


def compute_spectrum(
    audio: np.ndarray,
    sample_rate: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute magnitude spectrum of an audio frame.

    Args:
        audio: Float32 audio samples.
        sample_rate: Sample rate in Hz.

    Returns:
        Tuple of (frequencies_hz, magnitude_db) arrays of equal length.
        Frequencies run from 0 to sample_rate/2.
        Magnitude is in dBFS (0 dBFS = full scale).
    """
    windowed = audio * np.hanning(len(audio))
    spectrum = np.fft.rfft(windowed)
    magnitude = np.abs(spectrum)
    # Normalise and convert to dBFS
    magnitude_db = 20 * np.log10(magnitude / len(audio) + 1e-12)
    freqs = np.fft.rfftfreq(len(audio), d=1.0 / sample_rate)
    return freqs.astype(np.float32), magnitude_db.astype(np.float32)
