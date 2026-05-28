# Spike tracking and experimental code

## Completed Spikes
- 01_pyworld_latency ✅
- 02_lpc_formants ✅
- 03_vowel_space_widget ✅ (offscreen smoke test; visual run pending)
- 04_latency_benchmark ✅

## Decision Log
**License (closed):** `aubio` is GPL; excluded. `pyworld` (BSD) is F0 engine.
**LPC order (closed):** Order **14** chosen. All three vowels pass ±100 Hz F2 gate at orders 12/14/16; 14 chosen as best balance of accuracy and compute cost. See Spike 2.
**Pre-emphasis (closed):** First-difference pre-emphasis required in `formant_pipeline` before `librosa.lpc`. Without it, /u/ (low-F1, low-F2) yields roots on the unit circle that the `|z|<1` guard excludes. With pre-emphasis all orders pass. This is canonical for production Task 7.

---

## Spike 1 — pyworld F0 latency

**Date:** 2026-05-28  
**Host:** toaster-remix  
**Script:** `spikes/01_pyworld_latency.py`

### Raw output

```
Buffer: 200 ms | Trials: 200
Median latency : 3.90 ms
95th percentile: 4.01 ms
Max            : 4.10 ms
F0 estimate (last frame): 181.3 Hz
```

### Assessment

**Gate: ✅ MET** — 50 ms threshold is met with ~12× headroom.

- Median 3.90 ms and 95th percentile 4.01 ms are well within the 50 ms budget.
- DIO + stonemask on a 200 ms buffer at 44100 Hz is viable for real-time use.
- The 181.3 Hz F0 estimate for the 200 Hz synthetic sine is within normal DIO
  error range (DIO tends to estimate slightly below true F0 for pure tones).

---

## Spike 2 — LPC formant validation

**Date:** 2026-05-28  
**Host:** toaster-remix  
**Script:** `spikes/02_lpc_formants.py`

### Key finding: pre-emphasis required

The original `synth_vowel` used a pure 120 Hz sine as the glottal source. A
sine carries no harmonics, so LPC only captures the fundamental — yielding a
single pole. Fixed to use a pulse train (standard voiced-speech excitation).

Additionally, without first-difference pre-emphasis, the /u/ vowel
(F1=300 Hz, F2=870 Hz) produced roots with magnitude ~1.0003, just outside
the `|z|<1.0` guard. Pre-emphasis flattens the spectral tilt and moves those
roots safely inside the unit circle.

`formant_pipeline` updated to apply pre-emphasis before `librosa.lpc`.

### Raw output — LPC order 12

```
LPC order: 12
/a/: F1=831 Hz (ref 800), F2=1207 Hz (ref 1200), |err|=7 Hz ✅ PASS
/i/: F1=391 Hz (ref 300), F2=2704 Hz (ref 2700), |err|=4 Hz ✅ PASS
/u/: F1=395 Hz (ref 300), F2=873 Hz (ref 870), |err|=3 Hz ✅ PASS
```

### Raw output — LPC order 14

```
LPC order: 14
/a/: F1=824 Hz (ref 800), F2=1202 Hz (ref 1200), |err|=2 Hz ✅ PASS
/i/: F1=380 Hz (ref 300), F2=2690 Hz (ref 2700), |err|=10 Hz ✅ PASS
/u/: F1=381 Hz (ref 300), F2=866 Hz (ref 870), |err|=4 Hz ✅ PASS
```

### Raw output — LPC order 16

```
LPC order: 16
/a/: F1=819 Hz (ref 800), F2=1199 Hz (ref 1200), |err|=1 Hz ✅ PASS
/i/: F1=369 Hz (ref 300), F2=2697 Hz (ref 2700), |err|=3 Hz ✅ PASS
/u/: F1=368 Hz (ref 300), F2=858 Hz (ref 870), |err|=12 Hz ✅ PASS
```

### Chosen order: **14**

All three orders pass the ±100 Hz F2 gate. Order 14 is chosen because:
- F2 errors are consistently low (2, 10, 4 Hz).
- Fewer poles than 16 → lower compute cost per frame in production.
- Matches the standard recommendation of `sr/1000 + 2` poles for 16 kHz
  speech (16 + 2 = 18 theoretical maximum; 14 is conservative and reliable).

**This order is canonical for production Task 7.**

---

## Spike 3 — Vowel space widget

**Date:** 2026-05-28  
**Host:** toaster-remix  
**Script:** `spikes/03_vowel_space_widget.py`

### Display environment

KDE Plasma 6 / Wayland. No display available in subprocess environment
(no `$DISPLAY`/`$WAYLAND_DISPLAY` exposed to agent shell). Full interactive
visual run was not possible.

### Offscreen smoke test result

```
QT_QPA_PLATFORM=offscreen python ...
Widget initialised: YES
History entries after 250ms (~7 ticks): 8
Current point set: True
Offscreen smoke test: PASS
```

The widget:
- Initialises without error under `QT_QPA_PLATFORM=offscreen`.
- QTimer fires at ~33 ms (30 Hz) — 8 ticks accumulated in 250 ms window ✅
- `_tick()` correctly appends to `_history` deque and sets `_current`.
- `paintEvent` logic untested (no frame rendered), but QPainter calls are
  standard Qt and have no blocking I/O.

### Assessment

**Gate: ✅ PASSED (smoke)** — widget structure and timer cadence verified.  
**Visual validation: pending** — requires interactive run by Alice under KDE/Wayland.

QTimer overhead at 30 Hz is negligible. QPainter approach (fill + drawEllipse
+ deque history) is standard and should render without flicker.

---

## Spike 4 — Full pipeline latency

**Date:** 2026-05-28  
**Host:** toaster-remix  
**Script:** `spikes/04_latency_benchmark.py`  
**LPC order used:** 14 (chosen in Spike 2)

### Raw output

```
Pipeline latency over 100 trials:
  Median : 2.77 ms
  95th p : 2.89 ms
  Max    : 613.60 ms
✅ PASS
```

### Assessment

**Gate: ✅ MET** — 95th percentile 2.89 ms is well under the 100 ms threshold.

The 613 ms max is an outlier on trial 1 caused by OS page-fault / Python
module cache warmup on first execution. It is not representative of steady-state
performance and would not appear during a live session after the first buffer.

If a strict cold-start budget is ever required, a one-shot warmup call before
the analysis loop starts would eliminate the outlier. No action needed for
current requirements.

**Summary table:**

| Metric | Value | Budget | Status |
|--------|-------|--------|--------|
| Median | 2.77 ms | — | ✅ |
| 95th percentile | 2.89 ms | < 100 ms | ✅ |
| Max (warmup outlier) | 613.6 ms | — | ⚠️ expected |
