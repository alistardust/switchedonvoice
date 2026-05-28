"""F0 (fundamental frequency) estimation using pyworld.

Uses DIO + stonemask. Returns the most recent voiced F0 value from the buffer,
or None if no voiced frames were detected.
"""
from __future__ import annotations
import numpy as np
import pyworld as pw


def estimate_f0(audio: np.ndarray, sample_rate: int, frame_period_ms: float = 10.0) -> float | None:
    """Estimate fundamental frequency from an audio buffer.

    Args:
        audio: Float64 audio samples.
        sample_rate: Sample rate in Hz.
        frame_period_ms: Frame period for DIO analysis in milliseconds.

    Returns:
        Most recent voiced F0 in Hz, or None if the buffer contains no voiced frames.
    """
    audio_f64 = audio.astype(np.float64)
    f0, time_axis = pw.dio(audio_f64, sample_rate, frame_period=frame_period_ms)
    f0_refined = pw.stonemask(audio_f64, f0, time_axis, sample_rate)
    voiced = f0_refined[f0_refined > 0]
    if len(voiced) == 0:
        return None
    return float(np.median(voiced))
