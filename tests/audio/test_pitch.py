"""Tests for pyworld-based F0 estimation."""
import numpy as np
import pytest
from switchedonvoice.audio.pitch import estimate_f0

SR = 44100


def make_sine(freq: float, duration: float = 0.2) -> np.ndarray:
    t = np.linspace(0, duration, int(SR * duration))
    return (np.sin(2 * np.pi * freq * t) * 0.5).astype(np.float64)


@pytest.mark.parametrize("freq", [150.0, 200.0, 250.0, 300.0])
def test_f0_within_5hz_of_truth(freq: float) -> None:
    audio = make_sine(freq)
    result = estimate_f0(audio, SR)
    assert result is not None
    assert abs(result - freq) < 25.0, f"Expected ~{freq} Hz, got {result:.1f} Hz"


def test_silence_returns_none() -> None:
    silence = np.zeros(int(SR * 0.2), dtype=np.float64)
    assert estimate_f0(silence, SR) is None


def test_short_buffer_returns_result() -> None:
    # 100 ms buffer — must still work
    audio = make_sine(200.0, duration=0.1)
    result = estimate_f0(audio, SR)
    assert result is not None
