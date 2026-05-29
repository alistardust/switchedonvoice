"""Spike 2: Validate librosa.lpc + numpy.roots formant pipeline.

Uses synthetic vowel-like signals. Compare F1/F2 estimates against
textbook reference values for /a/ /i/ /u/.

References (average female):
  /a/: F1≈800 Hz, F2≈1200 Hz
  /i/: F1≈300 Hz, F2≈2700 Hz
  /u/: F1≈300 Hz, F2≈870 Hz
Acceptance: F2 within ±100 Hz of reference.

Run: python spikes/02_lpc_formants.py
"""
from __future__ import annotations
import numpy as np
import librosa

SR = 16000
LPC_ORDER = 14  # test 12, 14, 16


def formant_pipeline(audio: np.ndarray, sr: int, order: int) -> list[float]:
    """Return list of formant frequencies in Hz, ascending.

    Applies first-difference pre-emphasis before LPC so that low-frequency-
    dominant vowels (/u/) do not produce roots sitting on the unit circle
    that would otherwise be excluded by the magnitude guard.
    """
    # Pre-emphasis: flatten spectral tilt so LPC fits formants, not slope
    audio_f64 = np.diff(audio.astype(np.float64), prepend=audio[0])
    audio_f64 /= np.max(np.abs(audio_f64)) + 1e-9
    lpc_coeffs = librosa.lpc(audio_f64.astype(np.float32), order=order)
    # Roots of the A(z) polynomial
    roots = np.roots(lpc_coeffs)
    # Keep roots inside unit circle with positive imaginary part
    roots = roots[np.abs(roots) < 1.0]
    roots = roots[roots.imag > 0]
    # Convert to frequency and bandwidth
    angles = np.angle(roots)
    freqs = angles * sr / (2 * np.pi)
    bandwidths = -np.log(np.abs(roots)) * sr / np.pi
    # Keep only formant-range candidates
    mask = (freqs > 90) & (freqs < sr / 2 - 100) & (bandwidths < 500)
    freqs = freqs[mask]
    return sorted(freqs.tolist())


def synth_vowel(f1: float, f2: float, sr: int = SR, duration: float = 0.3) -> np.ndarray:
    """Very rough two-formant vowel synthesis via resonator cascade.

    Uses a pulse train (not a sine) as the glottal source so LPC has
    harmonics to fit — a pure sine carries no overtones and yields only
    one pole.
    """
    n = int(sr * duration)
    # Pulse train at 120 Hz (realistic voiced-speech excitation)
    period = int(sr / 120)
    signal = np.zeros(n)
    signal[::period] = 1.0
    for freq in (f1, f2):
        bw = 80.0
        r = np.exp(-np.pi * bw / sr)
        cos_w = np.cos(2 * np.pi * freq / sr)
        b = [1.0, 0.0, 0.0]
        a = [1.0, -2 * r * cos_w, r ** 2]
        from scipy.signal import lfilter
        signal = lfilter(b, a, signal)
    signal = signal / (np.max(np.abs(signal)) + 1e-9)
    return signal.astype(np.float32)


VOWELS = {
    "/a/": (800, 1200),
    "/i/": (300, 2700),
    "/u/": (300, 870),
}

print(f"LPC order: {LPC_ORDER}")
for label, (ref_f1, ref_f2) in VOWELS.items():
    sig = synth_vowel(ref_f1, ref_f2)
    formants = formant_pipeline(sig, SR, LPC_ORDER)
    f1_est = formants[0] if len(formants) > 0 else float("nan")
    f2_est = formants[1] if len(formants) > 1 else float("nan")
    f2_err = abs(f2_est - ref_f2) if not np.isnan(f2_est) else float("nan")
    gate = "✅ PASS" if f2_err <= 100 else "❌ FAIL"
    print(f"{label}: F1={f1_est:.0f} Hz (ref {ref_f1}), F2={f2_est:.0f} Hz (ref {ref_f2}), |err|={f2_err:.0f} Hz {gate}")
