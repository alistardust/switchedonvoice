"""Tests for Cepstral Peak Prominence computation."""
import numpy as np
import pytest
from switchedonvoice.audio.cpp import compute_cpp

SR = 16000


def make_periodic(freq: float = 200.0, sr: int = SR, duration: float = 0.2) -> np.ndarray:
    """Synthesize a periodic signal with strong harmonic content.

    Uses a sum of harmonics (sawtooth approximation) rather than a pure sine,
    which produces negligible CPP due to having only one cepstral peak.
    """
    t = np.linspace(0, duration, int(sr * duration))
    signal = np.zeros_like(t)
    for k in range(1, 20):
        signal += np.sin(2 * np.pi * freq * k * t) / k
    signal = signal / np.max(np.abs(signal)) * 0.5
    return signal.astype(np.float32)


def test_periodic_signal_has_positive_cpp() -> None:
    cpp = compute_cpp(make_periodic(), SR)
    assert cpp is not None
    assert cpp > 0.0


def test_noise_has_lower_cpp_than_periodic() -> None:
    rng = np.random.default_rng(0)
    noise = rng.uniform(-0.5, 0.5, int(SR * 0.2)).astype(np.float32)
    cpp_periodic = compute_cpp(make_periodic(), SR)
    cpp_noise = compute_cpp(noise, SR)
    assert cpp_periodic is not None
    assert cpp_noise is not None
    assert cpp_periodic > cpp_noise


def test_silence_returns_none() -> None:
    silence = np.zeros(int(SR * 0.2), dtype=np.float32)
    assert compute_cpp(silence, SR) is None
