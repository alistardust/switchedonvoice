"""Tests for voiced/unvoiced detection."""
import numpy as np
import pytest
from switchedonvoice.audio.voice_detector import is_voiced

SR = 16000


def make_sine(freq: float, duration: float = 0.05, amplitude: float = 0.5) -> np.ndarray:
    t = np.linspace(0, duration, int(SR * duration))
    return (np.sin(2 * np.pi * freq * t) * amplitude).astype(np.float32)


def make_silence(duration: float = 0.05) -> np.ndarray:
    return np.zeros(int(SR * duration), dtype=np.float32)


def make_noise(duration: float = 0.05) -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.uniform(-0.8, 0.8, int(SR * duration)).astype(np.float32)


def test_voiced_sine_returns_true() -> None:
    assert is_voiced(make_sine(200)) is True


def test_silence_returns_false() -> None:
    assert is_voiced(make_silence()) is False


def test_noise_returns_false() -> None:
    # High-ZCR noise should not be classified as voiced
    assert is_voiced(make_noise()) is False


def test_low_amplitude_sine_returns_false() -> None:
    # Below energy threshold
    assert is_voiced(make_sine(200, amplitude=0.001)) is False


def test_empty_frame_returns_false() -> None:
    assert is_voiced(np.array([], dtype=np.float32)) is False
