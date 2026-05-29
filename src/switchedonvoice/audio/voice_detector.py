"""Voiced/unvoiced detection via RMS energy + Zero Crossing Rate."""
import numpy as np

# Tunable thresholds — may need adjustment for different mic gain levels
_RMS_THRESHOLD = 0.02
_ZCR_MAX = 0.18   # above this = unvoiced/noisy (fricatives have high ZCR)


def is_voiced(frame: np.ndarray) -> bool:
    """Return True if the frame appears to contain voiced speech.

    Uses RMS energy (must exceed threshold) AND ZCR (must be low enough
    to exclude fricatives and white noise). Both conditions must hold.

    Args:
        frame: Audio samples as float32 array, any sample rate.

    Returns:
        True if the frame is likely voiced, False otherwise.
    """
    if len(frame) == 0:
        return False
    rms = float(np.sqrt(np.mean(frame ** 2)))
    if rms < _RMS_THRESHOLD:
        return False
    zero_crossings = int(np.sum(np.diff(np.sign(frame)) != 0))
    zcr = zero_crossings / max(len(frame) - 1, 1)
    return zcr < _ZCR_MAX
