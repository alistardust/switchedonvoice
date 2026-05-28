"""Tests for LPC-based formant estimation."""
import numpy as np
import pytest
from scipy.signal import lfilter
from switchedonvoice.audio.formants import estimate_formants

SR = 16000


def synth_vowel(f1: float, f2: float, sr: int = SR, duration: float = 0.3) -> np.ndarray:
    """Synthesize a vowel-like signal with two dominant resonances.

    Uses a pulse train excitation at 120 Hz (as validated in Spike 2).
    A sine excitation was trialled but does not excite all harmonics
    sufficiently for the LPC to resolve both formants reliably.
    """
    n = int(sr * duration)
    period = int(sr / 120)
    signal = np.zeros(n)
    for i in range(0, n, period):
        signal[i] = 1.0
    for freq in (f1, f2):
        bw = 80.0
        r = np.exp(-np.pi * bw / sr)
        cos_w = np.cos(2 * np.pi * freq / sr)
        b = [1.0, 0.0, 0.0]
        a = [1.0, -2 * r * cos_w, r ** 2]
        signal = lfilter(b, a, signal)
    mx = np.max(np.abs(signal))
    return (signal / (mx + 1e-9)).astype(np.float32)


@pytest.mark.parametrize("ref_f1,ref_f2", [
    (800, 1200),   # /a/
    (300, 2700),   # /i/
    (300, 870),    # /u/
])
def test_f2_within_100hz(ref_f1: float, ref_f2: float) -> None:
    audio = synth_vowel(ref_f1, ref_f2)
    formants = estimate_formants(audio, SR)
    assert len(formants) >= 2, "Expected at least F1 and F2"
    assert abs(formants[1] - ref_f2) < 100.0, (
        f"F2 estimate {formants[1]:.0f} Hz too far from reference {ref_f2} Hz"
    )


def test_returns_ascending_list() -> None:
    audio = synth_vowel(500, 1500)
    formants = estimate_formants(audio, SR)
    assert formants == sorted(formants)


def test_silence_returns_empty() -> None:
    silence = np.zeros(int(SR * 0.2), dtype=np.float32)
    formants = estimate_formants(silence, SR)
    assert formants == []
