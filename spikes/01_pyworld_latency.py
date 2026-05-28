"""Spike 1: Measure pyworld F0 estimation latency on short buffers.

Run: python spikes/01_pyworld_latency.py
Records to stdout. Copy findings to SPIKE_NOTES.md.
"""
import time
import numpy as np
import pyworld as pw

SR = 44100
BUFFER_MS = 200
N_SAMPLES = int(SR * BUFFER_MS / 1000)
N_TRIALS = 200

# Synthetic 200 Hz sine as stand-in for voice
t = np.linspace(0, BUFFER_MS / 1000, N_SAMPLES)
audio = (np.sin(2 * np.pi * 200 * t) * 0.5).astype(np.float64)

latencies_ms: list[float] = []
for _ in range(N_TRIALS):
    start = time.perf_counter()
    f0, time_axis = pw.dio(audio, SR, frame_period=10.0)
    f0 = pw.stonemask(audio, f0, time_axis, SR)
    elapsed = (time.perf_counter() - start) * 1000
    latencies_ms.append(elapsed)

arr = np.array(latencies_ms)
print(f"Buffer: {BUFFER_MS} ms | Trials: {N_TRIALS}")
print(f"Median latency : {np.median(arr):.2f} ms")
print(f"95th percentile: {np.percentile(arr, 95):.2f} ms")
print(f"Max            : {arr.max():.2f} ms")
voiced = f0[f0 > 0]
print(f"F0 estimate (last frame): {voiced[-1]:.1f} Hz" if len(voiced) else "No voiced frames")
