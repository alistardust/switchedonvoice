"""Spike 4: End-to-end pipeline latency: capture buffer → F0 → LPC → result.

Does NOT use a real microphone — uses a pre-generated buffer.
Target: < 100 ms total. Record in SPIKE_NOTES.md.

Run: python spikes/04_latency_benchmark.py
"""
import time
import numpy as np
import pyworld as pw
import librosa

SR_CAPTURE = 44100
SR_LPC = 16000
BUFFER_MS = 200
N_TRIALS = 100

t44 = np.linspace(0, BUFFER_MS / 1000, int(SR_CAPTURE * BUFFER_MS / 1000))
audio_44 = (np.sin(2 * np.pi * 200 * t44) * 0.5).astype(np.float64)

# Downsample for LPC
from scipy.signal import resample_poly
audio_16 = resample_poly(audio_44, SR_LPC, SR_CAPTURE).astype(np.float32)

latencies: list[float] = []
for _ in range(N_TRIALS):
    start = time.perf_counter()

    # F0
    f0, t_axis = pw.dio(audio_44, SR_CAPTURE, frame_period=10.0)
    f0 = pw.stonemask(audio_44, f0, t_axis, SR_CAPTURE)

    # LPC formants
    lpc = librosa.lpc(audio_16, order=14)
    roots = np.roots(lpc)
    roots = roots[np.abs(roots) < 1.0]
    roots = roots[roots.imag > 0]
    angles = np.angle(roots)
    freqs = sorted((angles * SR_LPC / (2 * np.pi)).tolist())

    elapsed = (time.perf_counter() - start) * 1000
    latencies.append(elapsed)

arr = np.array(latencies)
print(f"Pipeline latency over {N_TRIALS} trials:")
print(f"  Median : {np.median(arr):.2f} ms")
print(f"  95th p : {np.percentile(arr, 95):.2f} ms")
print(f"  Max    : {arr.max():.2f} ms")
gate = "✅ PASS" if np.percentile(arr, 95) < 100 else "⚠️  OVER 100ms — review"
print(gate)
