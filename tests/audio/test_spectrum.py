"""Tests for FFT spectrum computation."""
import numpy as np
import pytest
from switchedonvoice.audio.spectrum import compute_spectrum

SR = 44100


def test_output_length_is_n_over_2_plus_1() -> None:
    audio = np.zeros(2048, dtype=np.float32)
    freqs, magnitudes = compute_spectrum(audio, SR)
    assert len(freqs) == 1025
    assert len(magnitudes) == 1025


def test_sine_peak_at_correct_bin() -> None:
    freq = 440.0
    n = 4096
    t = np.linspace(0, n / SR, n)
    audio = np.sin(2 * np.pi * freq * t).astype(np.float32)
    freqs, magnitudes = compute_spectrum(audio, SR)
    peak_freq = freqs[np.argmax(magnitudes)]
    assert abs(peak_freq - freq) < SR / n + 5.0  # within one bin + margin


def test_silence_has_near_zero_magnitude() -> None:
    silence = np.zeros(2048, dtype=np.float32)
    _, magnitudes = compute_spectrum(silence, SR)
    assert np.max(magnitudes) < -100.0   # well below any voiced signal
