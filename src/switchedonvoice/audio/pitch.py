"""F0 (fundamental frequency) estimation using pyworld.

Uses DIO + stonemask. Returns the median voiced F0 across the buffer,
or None if no voiced frames were detected.

Implementation note: DIO exhibits a known tail boundary effect where the last
1–3 frames drift 10–20 Hz from the true pitch (verified empirically — see
SPIKE_NOTES.md). The spec originally specified voiced[-1] but that conflicts
with the required ±5 Hz accuracy gate. np.median(voiced) satisfies both the
accuracy requirement (<0.2 Hz error on synthetic signals) and provides a stable
reading suitable for real-time display.
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
        Median voiced F0 in Hz across the buffer, or None if no voiced frames.
        Median chosen over voiced[-1] to avoid DIO tail boundary error (~20 Hz).
    """
    audio_f64 = audio.astype(np.float64)
    f0, time_axis = pw.dio(audio_f64, sample_rate, frame_period=frame_period_ms)
    f0_refined = pw.stonemask(audio_f64, f0, time_axis, sample_rate)
    voiced = f0_refined[f0_refined > 0]
    if len(voiced) == 0:
        return None
    return float(np.median(voiced))
