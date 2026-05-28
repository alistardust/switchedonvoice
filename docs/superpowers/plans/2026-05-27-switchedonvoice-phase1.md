# SwitchedOnVoice Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real-time desktop voice feminization training tool with pitch/formant/CPP analysis, a vowel space display, gamification milestones, and an onboarding wizard.

**Architecture:** Single-process Python desktop app (PySide6 + sounddevice). A sounddevice callback feeds a lock-free deque; an analysis thread reads it at ~30 Hz, computes F0 (pyworld), voiced detection (RMS+ZCR), formants (librosa.lpc + numpy.roots), spectrum (numpy.fft.rfft), and CPP; results are posted to a queue.Queue; a QTimer at 30 Hz polls the queue and drives widget repaints. Phase 2 (Tauri + stdio IPC) is out of scope here — all DSP code is kept subprocess-portable regardless.

**Tech Stack:** Python 3.11+, PySide6 (LGPL), sounddevice, pyworld (BSD), librosa, numpy, scipy, SQLite (stdlib), uv for package management.

---

## Chunk 0: Repo Scaffold

### Task 0: Repository structure, tooling, and empty module stubs

> **License decision (closed):** `aubio` is GPL-licensed and is excluded from this project entirely. `pyworld` (BSD) is the confirmed F0 engine throughout. No further spike or decision is needed on this point.

**Files:**
- Create: `pyproject.toml`
- Create: `LICENSE`
- Create: `.gitignore`
- Create: `README.md`
- Create: `run.py`
- Create: `src/switchedonvoice/__init__.py`
- Create: `src/switchedonvoice/audio/__init__.py`
- Create: `src/switchedonvoice/audio/capture.py`
- Create: `src/switchedonvoice/audio/pitch.py`
- Create: `src/switchedonvoice/audio/voice_detector.py`
- Create: `src/switchedonvoice/audio/formants.py`
- Create: `src/switchedonvoice/audio/spectrum.py`
- Create: `src/switchedonvoice/audio/cpp.py`
- Create: `src/switchedonvoice/ui/__init__.py`
- Create: `src/switchedonvoice/ui/main_window.py`
- Create: `src/switchedonvoice/ui/analysis_panel.py`
- Create: `src/switchedonvoice/ui/pitch_meter.py`
- Create: `src/switchedonvoice/ui/vowel_space.py`
- Create: `src/switchedonvoice/ui/spectrum_widget.py`
- Create: `src/switchedonvoice/ui/exercise_panel.py`
- Create: `src/switchedonvoice/ui/progress_panel.py`
- Create: `src/switchedonvoice/ui/settings_panel.py`
- Create: `src/switchedonvoice/ui/waveform_widget.py`
- Create: `src/switchedonvoice/storage/__init__.py`
- Create: `src/switchedonvoice/storage/db.py`
- Create: `src/switchedonvoice/storage/sessions.py`
- Create: `src/switchedonvoice/storage/settings.py`
- Create: `src/switchedonvoice/gamification/__init__.py`
- Create: `src/switchedonvoice/gamification/milestones.py`
- Create: `src/switchedonvoice/onboarding/__init__.py`
- Create: `src/switchedonvoice/onboarding/wizard.py`
- Create: `src/switchedonvoice/onboarding/baseline_dialog.py`
- Create: `src/switchedonvoice/health.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/audio/__init__.py`
- Create: `tests/storage/__init__.py`
- Create: `tests/gamification/__init__.py`
- Create: `tests/ui/__init__.py`
- Create: `spikes/SPIKE_NOTES.md`
- Create: `spikes/01_pyworld_latency.py`
- Create: `spikes/02_lpc_formants.py`
- Create: `spikes/03_vowel_space_widget.py`
- Create: `spikes/04_latency_benchmark.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "switchedonvoice"
version = "0.1.0"
description = "Open source voice feminization training tool"
readme = "README.md"
license = { file = "LICENSE" }
requires-python = ">=3.11"
dependencies = [
    "PySide6>=6.6",
    "sounddevice>=0.4",
    "pyworld>=0.3",       # F0 estimation (BSD licence) — aubio excluded: it is GPL
    "librosa>=0.10",
    "numpy>=1.26",
    "scipy>=1.12",
    "structlog>=24",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-cov>=5",
    "ruff>=0.4",
    "mypy>=1.10",
]

[tool.hatch.build.targets.wheel]
packages = ["src/switchedonvoice"]

[tool.ruff]
line-length = 88
select = ["E","W","F","I","N","B","C4","UP","S","ANN"]

[tool.mypy]
strict = true
python_version = "3.11"
```

- [ ] **Step 2: Create `LICENSE`**

Write the standard MIT license text with `Copyright (c) 2026 Alice Thomas`.

- [ ] **Step 2a: Initialise git repository**

```bash
git init
git branch -M main
```

- [ ] **Step 2b: Create `.gitignore`**

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.venv/
.eggs/

# uv / pip
uv.lock
pip-log.txt

# Test and coverage
.pytest_cache/
.coverage
htmlcov/

# Editor
.idea/
.vscode/
*.swp
*.swo

# macOS
.DS_Store
```

- [ ] **Step 3: Create skeleton `README.md`**

```markdown
# SwitchedOnVoice

Real-time voice feminization training — pitch, resonance, and gamification.

## Requirements
- Python 3.11+
- A microphone

## Install
```bash
pip install uv
uv pip install -e ".[dev]"
```

## Run
```bash
python run.py
```
```

- [ ] **Step 4: Create `run.py`**

```python
"""Entry point for SwitchedOnVoice."""
import sys
from PySide6.QtWidgets import QApplication
from switchedonvoice.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

> **Note:** `run.py` imports `MainWindow`, which has only a docstring stub until Chunk 7 is
> complete. Running `python run.py` will fail with an ImportError until after Task 24.
> Do not run it at this stage.

- [ ] **Step 5a: Create audio module stubs**

```python
# src/switchedonvoice/audio/capture.py
"""sounddevice stream with lock-free deque ring buffer."""
# src/switchedonvoice/audio/pitch.py
"""F0 estimation using pyworld (DIO + stonemask). aubio excluded: GPL licence."""
# src/switchedonvoice/audio/voice_detector.py
"""Voiced/unvoiced detection via RMS energy + ZCR."""
# src/switchedonvoice/audio/formants.py
"""Formant estimation via LPC (librosa.lpc + numpy.roots)."""
# src/switchedonvoice/audio/spectrum.py
"""FFT-based spectrum analysis using numpy.fft.rfft."""
# src/switchedonvoice/audio/cpp.py
"""Cepstral Peak Prominence computation."""
```

Create each file with its docstring only.

- [ ] **Step 5b: Create UI module stubs**

Create each with its docstring:
- `src/switchedonvoice/ui/main_window.py` — `"""Top-level application window."""`
- `src/switchedonvoice/ui/analysis_panel.py` — `"""Analysis panel: pitch meter, vowel space, waveform, spectrum, CPP."""`
- `src/switchedonvoice/ui/pitch_meter.py` — `"""Colour-coded vertical pitch meter widget."""`
- `src/switchedonvoice/ui/vowel_space.py` — `"""F1×F2 vowel space scatter widget."""`
- `src/switchedonvoice/ui/waveform_widget.py` — `"""Time-domain waveform display widget."""`
- `src/switchedonvoice/ui/spectrum_widget.py` — `"""Frequency-domain spectrum display widget."""`
- `src/switchedonvoice/ui/exercise_panel.py` — `"""Exercise selection and guided practice panel."""`
- `src/switchedonvoice/ui/progress_panel.py` — `"""Progress history, milestones, and weekly chart panel."""`
- `src/switchedonvoice/ui/settings_panel.py` — `"""Device selection and application settings panel."""`

- [ ] **Step 5c: Create storage and gamification stubs**

Create each with its docstring:
- `src/switchedonvoice/storage/db.py` — `"""SQLite schema initialisation and connection management."""`
- `src/switchedonvoice/storage/sessions.py` — `"""Session CRUD, streak calculation, and aggregate stats."""`
- `src/switchedonvoice/storage/settings.py` — `"""Settings persistence via JSON."""`
- `src/switchedonvoice/gamification/milestones.py` — `"""Acoustic-tied milestone evaluation engine."""`
- `src/switchedonvoice/onboarding/wizard.py` — `"""5-step onboarding wizard."""`
- `src/switchedonvoice/onboarding/baseline_dialog.py` — `"""Reusable baseline recording dialog."""`
- `src/switchedonvoice/health.py` — `"""Vocal health warnings based on session elapsed time."""`

- [ ] **Step 5d: Create test stubs, spike files, and package init files**

```bash
# Package __init__.py files (empty — mark directories as Python packages)
touch src/switchedonvoice/__init__.py
touch src/switchedonvoice/audio/__init__.py
touch src/switchedonvoice/ui/__init__.py
touch src/switchedonvoice/storage/__init__.py
touch src/switchedonvoice/gamification/__init__.py
touch src/switchedonvoice/onboarding/__init__.py

# Test stubs
touch tests/__init__.py tests/conftest.py
touch tests/audio/__init__.py tests/storage/__init__.py
touch tests/gamification/__init__.py tests/ui/__init__.py
touch spikes/SPIKE_NOTES.md
touch spikes/01_pyworld_latency.py spikes/02_lpc_formants.py
touch spikes/03_vowel_space_widget.py spikes/04_latency_benchmark.py
```

- [ ] **Step 6: Install dependencies**

```bash
uv pip install -e ".[dev]"
```

Expected: all packages install without error.

- [ ] **Step 7: Verify import works**

```bash
python -c "import switchedonvoice; print('ok')"
```

Expected: `ok`

- [ ] **Step 7b: Create LICENSE file**

```bash
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2024 Alice Thomas

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
```

- [ ] **Step 8: Create GitHub repository**

```bash
gh repo create alistardust/switchedonvoice \
  --public \
  --description "Open source voice feminization training tool for trans women"
git remote add origin https://github.com/alistardust/switchedonvoice.git
```

Expected: GitHub repo created with no auto-generated files (no server-side LICENSE, README, or .gitignore). Remote `origin` set. Do **not** push yet — wait for the initial commit in Step 9.

- [ ] **Step 9: Commit scaffold and push**

```bash
git add .
git commit -m "chore: initial project scaffold

Skeleton structure, pyproject.toml, stubs for all planned modules.
No implementation yet — spikes come next.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push -u origin main
```

---

## Chunk 1: Technical Spikes

> **F0 engine decision (closed):** `aubio` is GPL-licensed and is excluded from this project. `pyworld` (BSD) is the confirmed F0 engine. No spike is needed to validate this decision — Spike 1 validates pyworld's suitability on this hardware.

> Complete all four spikes before writing any production code. Spikes are throwaway scripts — do NOT test them with pytest. Just run them manually and record findings in `spikes/SPIKE_NOTES.md`.
>
> **Acceptance gates that block later chunks:**
> - Spike 1: pyworld F0 latency < 50 ms on 200 ms buffer (or document actual figure and adjust architecture)
> - Spike 2: Estimated F2 within ±100 Hz of reference for /a/, /i/, /u/ vowels (synthetic signals pass; optionally validate against a real recording if available)
> - Spike 3: Vowel space widget renders live scatter without flicker at 30 Hz
> - Spike 4: DSP compute time (F0 + LPC on pre-generated buffer) < 100 ms. Note: this does NOT measure true end-to-end latency. True E2E = Spike 1 capture latency + this DSP time + QTimer poll (~33 ms). Document all three contributors.

### Task 1: Spike 1 — pyworld short-buffer F0 latency

**Files:**
- Modify: `spikes/01_pyworld_latency.py`
- Modify: `spikes/SPIKE_NOTES.md`

- [ ] **Step 1: Write the spike script**

```python
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
```

- [ ] **Step 2: Run the spike**

```bash
python spikes/01_pyworld_latency.py
```

- [ ] **Step 3: Record findings in `SPIKE_NOTES.md`**

Add a section `## Spike 1 — pyworld F0 latency` with the raw output, date, and hardware. Note whether the 50 ms gate is met. If NOT met, document the actual figure and note that the analysis loop sleep interval needs adjustment.

---

### Task 2: Spike 2 — LPC formant validation

**Files:**
- Modify: `spikes/02_lpc_formants.py`
- Modify: `spikes/SPIKE_NOTES.md`

- [ ] **Step 1: Write the spike script**

```python
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
    """Return list of formant frequencies in Hz, ascending."""
    lpc_coeffs = librosa.lpc(audio, order=order)
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
    """Very rough two-formant vowel synthesis via resonator cascade."""
    n = int(sr * duration)
    t = np.arange(n) / sr
    signal = np.sin(2 * np.pi * 120 * t)  # 120 Hz glottal source
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
```

- [ ] **Step 2: Run spike for orders 12, 14, 16**

Change `LPC_ORDER` to each value and run:
```bash
python spikes/02_lpc_formants.py
```

- [ ] **Step 3: Record findings in `SPIKE_NOTES.md`**

Add `## Spike 2 — LPC formant validation`. Record the raw output for each LPC order (12, 14, 16). State which order is chosen and why.

- [ ] **Step 4 (optional but recommended): Validate against a real recording**

If you have a ~300 ms recording of yourself saying /a/, /i/, /u/ clearly, run the chosen LPC order against it:

```python
import soundfile as sf
audio, sr = sf.read("your_recording.wav")
# downsample to 16000 Hz if needed, then call formant_pipeline()
```

Record the error vs. textbook reference values in `SPIKE_NOTES.md`. If real-speech error is significantly larger than synthetic (> ±200 Hz on F2), try LPC order 16 or 18. If all orders fail on real speech, fall back to opensmile per the existing fallback note.

**If no order passes the ±100 Hz gate for all three vowels:** Before continuing, run an `opensmile` comparison. Install: `uv pip install opensmile`. Extract F1/F2 from the same synthetic signals using opensmile and compare. Document in SPIKE_NOTES.md. If opensmile passes, update `formants.py` to use opensmile as primary and add it to `pyproject.toml` dependencies.

---

### Task 3: Spike 3 — Vowel space QWidget

**Files:**
- Modify: `spikes/03_vowel_space_widget.py`
- Modify: `spikes/SPIKE_NOTES.md`

- [ ] **Step 1: Write the spike**

```python
"""Spike 3: Prototype the F1×F2 vowel space scatter widget.

Generates random F1/F2 pairs at 30 Hz to simulate live updates.
Check: no flicker, "you are here" dot visible, reference ellipses visible.

Run: python spikes/03_vowel_space_widget.py
"""
import sys
import math
import random
from collections import deque
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

# Reference ellipse centres (F1, F2) and radii for cis-female speech
FEMALE_CENTRE = (450, 1800)
FEMALE_RADIUS = (200, 500)
MALE_CENTRE = (600, 1300)
MALE_RADIUS = (200, 400)

F1_RANGE = (200, 900)    # y-axis (inverted: low F1 at top)
F2_RANGE = (700, 3000)   # x-axis


class VowelSpaceWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(400, 350)
        self.setWindowTitle("Vowel Space Spike")
        self._history: deque[tuple[float, float]] = deque(maxlen=60)  # ~2s at 30Hz
        self._current: tuple[float, float] | None = None
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(33)  # ~30 Hz

    def _tick(self) -> None:
        f1 = random.gauss(FEMALE_CENTRE[0], 80)
        f2 = random.gauss(FEMALE_CENTRE[1], 200)
        self._history.append((f1, f2))
        self._current = (f1, f2)
        self.update()

    def _to_px(self, f1: float, f2: float) -> tuple[int, int]:
        w, h = self.width(), self.height()
        pad = 30
        x = int(pad + (f2 - F2_RANGE[0]) / (F2_RANGE[1] - F2_RANGE[0]) * (w - 2 * pad))
        # F1 axis is inverted (higher F1 = lower formant frequency = bottom)
        y = int(pad + (1 - (f1 - F1_RANGE[0]) / (F1_RANGE[1] - F1_RANGE[0])) * (h - 2 * pad))
        return x, y

    def paintEvent(self, _event: object) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(20, 20, 30))

        # Reference ellipses
        for centre, radius, color in [
            (FEMALE_CENTRE, FEMALE_RADIUS, QColor(80, 200, 120, 60)),
            (MALE_CENTRE, MALE_RADIUS, QColor(200, 80, 80, 60)),
        ]:
            cx, cy = self._to_px(*centre)
            rx = int(radius[1] / (F2_RANGE[1] - F2_RANGE[0]) * (self.width() - 60))
            ry = int(radius[0] / (F1_RANGE[1] - F1_RANGE[0]) * (self.height() - 60))
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - rx, cy - ry, 2 * rx, 2 * ry)

        # History dots
        painter.setPen(Qt.PenStyle.NoPen)
        for i, (f1, f2) in enumerate(self._history):
            alpha = int(60 + 180 * i / max(len(self._history), 1))
            painter.setBrush(QBrush(QColor(100, 180, 255, alpha)))
            x, y = self._to_px(f1, f2)
            painter.drawEllipse(x - 3, y - 3, 6, 6)

        # Current position
        if self._current:
            x, y = self._to_px(*self._current)
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(x - 6, y - 6, 12, 12)


app = QApplication(sys.argv)
w = VowelSpaceWidget()
w.show()
sys.exit(app.exec())
```

- [ ] **Step 2: Run and evaluate**

```bash
python spikes/03_vowel_space_widget.py
```

**Measurable acceptance criteria:**
- Let the window run for at least 10 seconds.
- Add a temporary `print(f"{time.monotonic():.3f}")` at the top of `_tick` to verify timing. In 10 seconds (~300 ticks), no more than 1 gap > 66 ms between ticks is acceptable.
- Visual: "you are here" dot moves on every tick, reference ellipses are correctly shaped and legible, history trail fades from dim (old) to bright (recent).
- Failure: if dot freezes > 100 ms or ellipses render as rectangles, record the issue in SPIKE_NOTES.md and add `self.setUpdatesEnabled(False)` / `True` guards around batch repaint.

- [ ] **Step 3: Record in `SPIKE_NOTES.md`**

Add `## Spike 3 — Vowel space widget`. Note any flicker issues, QWidget.update() overhead, whether QPainter approach is viable.

---

### Task 4: Spike 4 — DSP compute benchmark

**Files:**
- Modify: `spikes/04_latency_benchmark.py`
- Modify: `spikes/SPIKE_NOTES.md`

> **Scope:** This spike measures the compute time for the F0 + LPC pipeline on a pre-generated buffer. It does NOT measure capture latency (sounddevice callback overhead) or display latency (Qt repaint). True end-to-end latency = capture callback interval + this DSP time + QTimer poll delay (~33ms). Use Spike 1 for capture latency and assess display latency manually.

- [ ] **Step 1: Write the spike**

```python
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
```

- [ ] **Step 2: Run the spike**

```bash
python spikes/04_latency_benchmark.py
```

- [ ] **Step 3: Record in `SPIKE_NOTES.md`**

Add `## Spike 4 — Full pipeline latency`. Note whether < 100 ms gate is met. If not, identify the bottleneck and proposed mitigation (e.g., reduce LPC buffer, use shorter pyworld frame period).

- [ ] **Step 4: Commit all spike work**

```bash
git add spikes/
git commit -m "chore(spikes): add four technical spikes with SPIKE_NOTES

Spike 1: pyworld latency
Spike 2: LPC formant validation
Spike 3: vowel space widget
Spike 4: full pipeline benchmark

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push
```

---

## Chunk 2: Audio Engine

> **F0 engine (confirmed):** `pyworld` is used throughout this chunk. `aubio` is GPL-licensed and excluded. Tasks 6–10 use pyworld unconditionally.

> **Prerequisite:** All four spikes must be complete and their acceptance gates met. Use the empirically validated LPC order from Spike 2. Use the buffer size validated in Spike 1.

### Task 5: Voice detector

**Files:**
- Modify: `src/switchedonvoice/audio/voice_detector.py`
- Create: `tests/audio/test_voice_detector.py`

Background: The voice detector gates ALL downstream analysis. On unvoiced frames (silence, fricatives, noise), formant estimates are garbage and must be excluded from the vowel space display.

- [ ] **Step 1: Write failing tests**

```python
# tests/audio/test_voice_detector.py
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/audio/test_voice_detector.py -v
```

Expected: `ImportError` or `AttributeError` (function not yet implemented).

- [ ] **Step 3: Implement `is_voiced`**

```python
# src/switchedonvoice/audio/voice_detector.py
"""Voiced/unvoiced detection via RMS energy + Zero Crossing Rate."""
import numpy as np

# Tunable thresholds — may need adjustment for different mic gain levels
_RMS_THRESHOLD = 0.02
_ZCR_MAX = 0.35   # above this = unvoiced/noisy (fricatives have high ZCR)


def is_voiced(frame: np.ndarray) -> bool:
    """Return True if the frame appears to contain voiced speech.

    Uses RMS energy (must exceed threshold) AND ZCR (must be low enough
    to exclude fricatives and white noise). Both conditions must hold.

    Args:
        frame: Audio samples as float32 array, any sample rate.

    Returns:
        True if the frame is likely voiced, False otherwise.
    """
    rms = float(np.sqrt(np.mean(frame ** 2)))
    if rms < _RMS_THRESHOLD:
        return False
    zero_crossings = int(np.sum(np.abs(np.diff(np.sign(frame)))))
    zcr = zero_crossings / max(len(frame) - 1, 1)
    return zcr < _ZCR_MAX
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/audio/test_voice_detector.py -v
```

Expected: all 4 pass.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/audio/voice_detector.py tests/audio/test_voice_detector.py
git commit -m "feat(audio): add voiced/unvoiced detector (RMS + ZCR)

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 6: Pitch estimator (pyworld F0)

**Files:**
- Modify: `src/switchedonvoice/audio/pitch.py`
- Create: `tests/audio/test_pitch.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/audio/test_pitch.py
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
    assert abs(result - freq) < 5.0, f"Expected ~{freq} Hz, got {result:.1f} Hz"


def test_silence_returns_none() -> None:
    silence = np.zeros(int(SR * 0.2), dtype=np.float64)
    assert estimate_f0(silence, SR) is None


def test_short_buffer_returns_result() -> None:
    # 100 ms buffer — must still work
    audio = make_sine(200.0, duration=0.1)
    result = estimate_f0(audio, SR)
    assert result is not None
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/audio/test_pitch.py -v
```

- [ ] **Step 3: Implement `estimate_f0`**

```python
# src/switchedonvoice/audio/pitch.py
"""F0 (fundamental frequency) estimation using pyworld.

Uses DIO + stonemask. Returns the most recent voiced F0 value from the buffer,
or None if no voiced frames were detected.
"""
from __future__ import annotations
import numpy as np
import pyworld as pw


def estimate_f0(audio: np.ndarray, sample_rate: int, frame_period_ms: float = 10.0) -> float | None:
    """Estimate fundamental frequency from an audio buffer.

    Args:
        audio: Float64 audio samples.
        sample_rate: Sample rate in Hz.
        frame_period_ms: Frame period for DIO analysis in milliseconds.

    Returns:
        Most recent voiced F0 in Hz, or None if the buffer contains no voiced frames.
    """
    # pyworld requires float64
    audio_f64 = audio.astype(np.float64)
    f0, time_axis = pw.dio(audio_f64, sample_rate, frame_period=frame_period_ms)
    f0_refined = pw.stonemask(audio_f64, f0, time_axis, sample_rate)
    voiced = f0_refined[f0_refined > 0]
    if len(voiced) == 0:
        return None
    return float(voiced[-1])
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/audio/test_pitch.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/audio/pitch.py tests/audio/test_pitch.py
git commit -m "feat(audio): add pyworld F0 estimator

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 7: Formant estimator (LPC)

**Files:**
- Modify: `src/switchedonvoice/audio/formants.py`
- Create: `tests/audio/test_formants.py`

Use the LPC order validated in Spike 2. Default to 14 if the spike showed 14 is acceptable.

- [ ] **Step 1: Write failing tests**

```python
# tests/audio/test_formants.py
"""Tests for LPC-based formant estimation."""
import numpy as np
import pytest
from scipy.signal import lfilter
from switchedonvoice.audio.formants import estimate_formants

SR = 16000


def synth_vowel(f1: float, f2: float, sr: int = SR, duration: float = 0.3) -> np.ndarray:
    """Synthesize a vowel-like signal with two dominant resonances."""
    n = int(sr * duration)
    t = np.arange(n) / sr
    signal = np.sin(2 * np.pi * 120 * t)
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/audio/test_formants.py -v
```

- [ ] **Step 3: Implement `estimate_formants`**

```python
# src/switchedonvoice/audio/formants.py
"""Formant frequency estimation via LPC (librosa.lpc + numpy.roots).

Pipeline:
  1. Pre-emphasise the signal.
  2. Apply a Hamming window.
  3. Fit LPC coefficients.
  4. Find roots of the LPC polynomial.
  5. Keep roots inside the unit circle with positive imaginary part.
  6. Filter by bandwidth < 500 Hz and frequency in speech range.
  7. Return sorted formant frequencies in Hz.
"""
from __future__ import annotations
import numpy as np
import librosa

# Validated empirically in Spike 2 — change if spike results differ
LPC_ORDER: int = 14
_MIN_FREQ_HZ: float = 90.0
_MAX_BANDWIDTH_HZ: float = 500.0
_PRE_EMPHASIS: float = 0.97


def estimate_formants(audio: np.ndarray, sample_rate: int) -> list[float]:
    """Estimate formant frequencies from a voiced audio frame.

    Args:
        audio: Float32 audio samples at sample_rate.
        sample_rate: Sample rate in Hz. Recommend 16 kHz for LPC.

    Returns:
        Sorted list of formant frequencies in Hz (F1, F2, F3 ...).
        Returns empty list if audio is silent or no valid formants found.
    """
    if np.max(np.abs(audio)) < 1e-6:
        return []

    # Pre-emphasis to boost high-frequency content
    emphasised = np.append(audio[0], audio[1:] - _PRE_EMPHASIS * audio[:-1])
    windowed = emphasised * np.hamming(len(emphasised))

    lpc_coeffs = librosa.lpc(windowed.astype(np.float32), order=LPC_ORDER)
    roots = np.roots(lpc_coeffs)

    # Only roots inside unit circle with positive imaginary part
    roots = roots[np.abs(roots) < 1.0]
    roots = roots[roots.imag > 0]

    if len(roots) == 0:
        return []

    angles = np.angle(roots)
    freqs_hz = angles * sample_rate / (2 * np.pi)
    bandwidths_hz = -np.log(np.abs(roots)) * sample_rate / np.pi

    max_freq = sample_rate / 2 - 100
    mask = (
        (freqs_hz > _MIN_FREQ_HZ)
        & (freqs_hz < max_freq)
        & (bandwidths_hz < _MAX_BANDWIDTH_HZ)
    )
    formants = sorted(freqs_hz[mask].tolist())
    return formants
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/audio/test_formants.py -v
```

Expected: all pass. If F2 tolerance test fails, revisit LPC order.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/audio/formants.py tests/audio/test_formants.py
git commit -m "feat(audio): add LPC formant estimator (librosa.lpc + numpy.roots)

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 8: Spectrum analyser

**Files:**
- Modify: `src/switchedonvoice/audio/spectrum.py`
- Create: `tests/audio/test_spectrum.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/audio/test_spectrum.py
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
    assert np.max(magnitudes) < 1e-9
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/audio/test_spectrum.py -v
```

- [ ] **Step 3: Implement `compute_spectrum`**

```python
# src/switchedonvoice/audio/spectrum.py
"""FFT-based spectrum analysis using numpy directly.

Does NOT use librosa — librosa adds import overhead and has no streaming API.
numpy.fft.rfft is used directly for low-latency operation in the hot path.
"""
from __future__ import annotations
import numpy as np


def compute_spectrum(
    audio: np.ndarray,
    sample_rate: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute magnitude spectrum of an audio frame.

    Args:
        audio: Float32 audio samples.
        sample_rate: Sample rate in Hz.

    Returns:
        Tuple of (frequencies_hz, magnitude_db) arrays of equal length.
        Frequencies run from 0 to sample_rate/2.
        Magnitude is in dBFS (0 dBFS = full scale).
    """
    windowed = audio * np.hanning(len(audio))
    spectrum = np.fft.rfft(windowed)
    magnitude = np.abs(spectrum)
    # Normalise and convert to dBFS
    magnitude_db = 20 * np.log10(magnitude / len(audio) + 1e-12)
    freqs = np.fft.rfftfreq(len(audio), d=1.0 / sample_rate)
    return freqs.astype(np.float32), magnitude_db.astype(np.float32)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/audio/test_spectrum.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/audio/spectrum.py tests/audio/test_spectrum.py
git commit -m "feat(audio): add FFT spectrum analyser

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 9: CPP (Cepstral Peak Prominence)

**Files:**
- Modify: `src/switchedonvoice/audio/cpp.py`
- Create: `tests/audio/test_cpp.py`

CPP is displayed as an observation only — no target, no pass/fail colouring. It correlates with voice quality/breathiness.

- [ ] **Step 1: Write failing tests**

```python
# tests/audio/test_cpp.py
"""Tests for Cepstral Peak Prominence computation."""
import numpy as np
import pytest
from switchedonvoice.audio.cpp import compute_cpp

SR = 16000


def make_periodic(freq: float = 200.0, sr: int = SR, duration: float = 0.2) -> np.ndarray:
    t = np.linspace(0, duration, int(sr * duration))
    return (np.sin(2 * np.pi * freq * t) * 0.5).astype(np.float32)


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
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/audio/test_cpp.py -v
```

- [ ] **Step 3: Implement `compute_cpp`**

```python
# src/switchedonvoice/audio/cpp.py
"""Cepstral Peak Prominence (CPP) computation.

CPP is the difference between the cepstral peak in the voiced range
(2ms–15ms, i.e., 66–500 Hz) and the linear regression trend at that
quefrency. Higher CPP = more periodic / less breathy voice.

Displayed as observation only — no target is set, no pass/fail.
"""
from __future__ import annotations
import numpy as np

_QUEFRENCY_MIN_MS = 2.0    # 500 Hz
_QUEFRENCY_MAX_MS = 15.0   # 66 Hz


def compute_cpp(audio: np.ndarray, sample_rate: int) -> float | None:
    """Compute Cepstral Peak Prominence of an audio frame.

    Args:
        audio: Float32 audio samples.
        sample_rate: Sample rate in Hz.

    Returns:
        CPP value in dB, or None if the frame is silent.
    """
    if np.max(np.abs(audio)) < 1e-6:
        return None

    # Power spectrum → log → IFFT = cepstrum
    spectrum = np.fft.rfft(audio.astype(np.float64))
    log_power = np.log(np.abs(spectrum) ** 2 + 1e-12)
    cepstrum = np.fft.irfft(log_power).real

    # Quefrency axis (in ms)
    n_samples = len(cepstrum)
    quefrency_ms = np.arange(n_samples) / sample_rate * 1000

    min_q = _QUEFRENCY_MIN_MS
    max_q = _QUEFRENCY_MAX_MS
    mask = (quefrency_ms >= min_q) & (quefrency_ms <= max_q)
    if not np.any(mask):
        return None

    region = cepstrum[mask]
    q_vals = quefrency_ms[mask]

    # Peak value
    peak_idx = int(np.argmax(region))
    peak_val = float(region[peak_idx])

    # Linear regression trend across the region
    coeffs = np.polyfit(q_vals, region, 1)
    trend_at_peak = float(np.polyval(coeffs, q_vals[peak_idx]))

    cpp = peak_val - trend_at_peak
    return cpp
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/audio/test_cpp.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/audio/cpp.py tests/audio/test_cpp.py
git commit -m "feat(audio): add Cepstral Peak Prominence computation

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 10: Audio capture and analysis thread

**Files:**
- Modify: `src/switchedonvoice/audio/capture.py`
- Create: `tests/audio/test_capture.py`

This is the core real-time loop. The sounddevice callback is intentionally minimal — it only appends to the deque. All DSP is in the analysis thread.

- [ ] **Step 1: Write failing tests**

```python
# tests/audio/test_capture.py
"""Tests for AudioCapture — mock sounddevice, test queue output."""
import queue
import time
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from switchedonvoice.audio.capture import AudioCapture, AnalysisResult


def make_capture() -> AudioCapture:
    return AudioCapture(device_index=None, sample_rate=44100)


def test_analysis_result_is_dataclass() -> None:
    r = AnalysisResult(f0=200.0, formants=[800.0, 1200.0], cpp=12.5, is_voiced=True,
                       spectrum_freqs=np.array([0.0]), spectrum_db=np.array([-60.0]))
    assert r.f0 == 200.0
    assert r.is_voiced is True


def test_capture_creates_queue() -> None:
    cap = make_capture()
    assert isinstance(cap.results, queue.Queue)


def test_stop_before_start_is_safe() -> None:
    cap = make_capture()
    cap.stop()  # Should not raise


def test_analysis_loop_produces_result_for_voiced_frame() -> None:
    """Analysis thread should emit an AnalysisResult when fed audio data."""
    import threading
    from collections import deque

    cap = make_capture()

    # Inject a 200 Hz sine wave (voiced) directly into the deque
    sr = cap._sample_rate
    t = np.linspace(0, 0.2, int(sr * 0.2), dtype=np.float32)
    voiced_audio = np.sin(2 * np.pi * 200 * t) * 0.5
    cap._buffer.append(voiced_audio)

    # Run one cycle of the analysis loop manually
    cap._stop_event.clear()
    stop_after_one = threading.Event()

    original_loop = cap._analysis_loop

    def one_shot_loop() -> None:
        import time as _time
        n_buf = int(cap._sample_rate * 0.2)
        chunks: list[np.ndarray] = []
        while cap._buffer:
            chunks.append(cap._buffer.popleft())
        if chunks:
            raw = np.concatenate(chunks)
            if len(raw) > n_buf:
                raw = raw[-n_buf:]
            # Trigger the normal analysis path via the capture module's helpers
            from switchedonvoice.audio.voice_detector import is_voiced as _is_voiced
            from switchedonvoice.audio.pitch import estimate_f0 as _f0
            from switchedonvoice.audio.formants import estimate_formants as _formants
            from switchedonvoice.audio.spectrum import compute_spectrum as _spectrum
            from switchedonvoice.audio.cpp import compute_cpp as _cpp
            from scipy.signal import resample_poly
            voiced = _is_voiced(raw)
            f0 = _f0(raw.astype(np.float64), cap._sample_rate) if voiced else None
            lpc = resample_poly(raw, 16000, cap._sample_rate).astype(np.float32)
            formants = _formants(lpc, 16000) if voiced else []
            cpp_val = _cpp(lpc, 16000) if voiced else None
            freqs, db = _spectrum(raw, cap._sample_rate)
            cap.results.put_nowait(AnalysisResult(
                f0=f0, formants=formants, cpp=cpp_val,
                is_voiced=voiced, spectrum_freqs=freqs, spectrum_db=db,
            ))
        stop_after_one.set()

    one_shot_loop()
    assert not cap.results.empty(), "Analysis of voiced frame produced no result"
    result = cap.results.get_nowait()
    assert isinstance(result, AnalysisResult)


def test_analysis_loop_handles_silence() -> None:
    """Analysis thread should emit an unvoiced result for silent audio."""
    cap = make_capture()
    silence = np.zeros(int(cap._sample_rate * 0.2), dtype=np.float32)
    cap._buffer.append(silence)

    from switchedonvoice.audio.voice_detector import is_voiced as _is_voiced
    from switchedonvoice.audio.spectrum import compute_spectrum as _spectrum
    raw = silence
    voiced = _is_voiced(raw)
    freqs, db = _spectrum(raw, cap._sample_rate)
    cap.results.put_nowait(AnalysisResult(
        f0=None, formants=[], cpp=None, is_voiced=voiced,
        spectrum_freqs=freqs, spectrum_db=db,
    ))
    result = cap.results.get_nowait()
    assert result.is_voiced is False
    assert result.f0 is None


def test_start_stop_integration() -> None:
    """Drive the real start()/callback/thread path via mocked sounddevice."""
    import threading
    from unittest.mock import patch, MagicMock

    cap = make_capture()
    sr = cap._sample_rate
    t = np.linspace(0, 0.2, int(sr * 0.2), dtype=np.float32)
    voiced_audio = np.sin(2 * np.pi * 200 * t) * 0.5

    mock_stream = MagicMock()
    mock_stream_instance = MagicMock()
    mock_stream.return_value = mock_stream_instance

    with patch("switchedonvoice.audio.capture.sd.InputStream", mock_stream):
        cap.start()
        # Simulate callback as sounddevice would call it
        fake_indata = voiced_audio.reshape(-1, 1)
        cap._audio_callback(fake_indata, len(fake_indata), None, MagicMock())
        # Give the analysis thread one cycle
        import time as _time
        _time.sleep(0.1)
        cap.stop()

    # Should have at least attempted to produce a result
    mock_stream_instance.start.assert_called_once()
    mock_stream_instance.stop.assert_called_once()
    assert cap.results.qsize() > 0, "Analysis thread should have produced at least one result"


def test_audio_callback_logs_input_overflow() -> None:
    """Callback should log a warning when sounddevice reports input overflow."""
    import sounddevice as sd
    import structlog

    cap = make_capture()
    sr = cap._sample_rate
    audio = np.zeros((512, 1), dtype=np.float32)

    # Create a status that reports overflow
    # sounddevice.CallbackFlags doesn't have a direct constructor;
    # simulate by checking that the callback handles a truthy status gracefully
    class FakeStatus:
        input_overflow = True
        def __bool__(self) -> bool:
            return True

    import structlog.testing
    with structlog.testing.capture_logs() as logs:
        cap._audio_callback(audio, 512, None, FakeStatus())  # type: ignore[arg-type]

    # Overflow frames should still be appended (don't drop — log only)
    assert len(cap._buffer) == 1
    # An input_overflow warning must have been logged
    assert any(
        entry.get("event") == "audio_capture_input_overflow"
        for entry in logs
    ), f"Expected input_overflow warning, got: {logs}"
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/audio/test_capture.py -v
```

- [ ] **Step 3: Implement `AudioCapture`**

```python
# src/switchedonvoice/audio/capture.py
"""sounddevice audio capture with lock-free deque + analysis thread.

Architecture:
  sounddevice callback   → deque (lock-free append/popleft)
  analysis thread        → reads deque, runs DSP, posts to results queue
  Qt main thread (30Hz)  → polls results queue via QTimer
"""
from __future__ import annotations
import queue
import threading
import time
from collections import deque
from dataclasses import dataclass, field

import numpy as np
import sounddevice as sd
import structlog
from scipy.signal import resample_poly

from switchedonvoice.audio.voice_detector import is_voiced
from switchedonvoice.audio.pitch import estimate_f0
from switchedonvoice.audio.formants import estimate_formants
from switchedonvoice.audio.spectrum import compute_spectrum
from switchedonvoice.audio.cpp import compute_cpp

_log = structlog.get_logger(__name__)

_SAMPLE_RATE_CAPTURE = 44100
_SAMPLE_RATE_LPC = 16000
_BUFFER_DURATION_S = 0.2       # 200 ms buffer fed to analysis
_ANALYSIS_INTERVAL_S = 0.033   # ~30 Hz analysis rate
_BLOCK_SIZE = 512


@dataclass
class AnalysisResult:
    """Holds one analysis frame result for delivery to the UI."""
    f0: float | None
    formants: list[float]
    cpp: float | None
    is_voiced: bool
    spectrum_freqs: np.ndarray
    spectrum_db: np.ndarray
    raw_audio: np.ndarray | None = None  # the 200 ms buffer used for this frame; for waveform display


class AudioCapture:
    """Manages microphone capture and real-time DSP analysis.

    Usage:
        cap = AudioCapture(device_index=None, sample_rate=44100)
        cap.start()
        # poll cap.results (queue.Queue) in a QTimer at 30 Hz
        cap.stop()
    """

    def __init__(self, device_index: int | None, sample_rate: int = _SAMPLE_RATE_CAPTURE) -> None:
        self._device_index = device_index
        self._sample_rate = sample_rate
        self._buffer: deque[np.ndarray] = deque()
        self.results: queue.Queue[AnalysisResult] = queue.Queue(maxsize=10)
        self._stream: sd.InputStream | None = None
        self._analysis_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start the microphone stream and analysis thread."""
        self._stop_event.clear()
        self._stream = sd.InputStream(
            device=self._device_index,
            samplerate=self._sample_rate,
            channels=1,
            dtype="float32",
            blocksize=_BLOCK_SIZE,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self._analysis_thread.start()

    def stop(self) -> None:
        """Stop the stream and analysis thread cleanly."""
        self._stop_event.set()
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if self._analysis_thread is not None:
            self._analysis_thread.join(timeout=1.0)
            self._analysis_thread = None

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,  # noqa: ARG002
        time_info: object,  # noqa: ARG002
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            if status.input_overflow:
                _log.warning("audio_capture_input_overflow")
            else:
                _log.warning("audio_capture_status", status=str(status))
        # Minimal work in callback — just copy the block into the deque
        self._buffer.append(indata[:, 0].copy())

    def _analysis_loop(self) -> None:
        n_buffer_samples = int(self._sample_rate * _BUFFER_DURATION_S)
        while not self._stop_event.is_set():
            time.sleep(_ANALYSIS_INTERVAL_S)
            # Drain deque into a contiguous analysis buffer
            chunks: list[np.ndarray] = []
            while self._buffer:
                chunks.append(self._buffer.popleft())
            if not chunks:
                continue
            raw = np.concatenate(chunks)
            if len(raw) > n_buffer_samples:
                raw = raw[-n_buffer_samples:]

            voiced = is_voiced(raw)
            f0 = estimate_f0(raw.astype(np.float64), self._sample_rate) if voiced else None

            # Downsample for LPC
            lpc_audio = resample_poly(raw, _SAMPLE_RATE_LPC, self._sample_rate).astype(np.float32)
            formants = estimate_formants(lpc_audio, _SAMPLE_RATE_LPC) if voiced else []

            cpp = compute_cpp(lpc_audio, _SAMPLE_RATE_LPC) if voiced else None
            freqs, db = compute_spectrum(raw, self._sample_rate)

            result = AnalysisResult(
                f0=f0,
                formants=formants,
                cpp=cpp,
                is_voiced=voiced,
                spectrum_freqs=freqs,
                spectrum_db=db,
                raw_audio=raw,
            )
            try:
                self.results.put_nowait(result)
            except queue.Full:
                pass  # Drop frame — UI is behind. This is intentional.
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/audio/test_capture.py -v
```

- [ ] **Step 5: Run all audio tests**

```bash
pytest tests/audio/ -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/switchedonvoice/audio/capture.py tests/audio/test_capture.py
git commit -m "feat(audio): add AudioCapture with analysis thread

Sounddevice callback → deque → analysis thread → queue.Queue.
~30 Hz analysis rate, voiced/unvoiced gating, F0/formants/CPP/spectrum.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push
```

---

## Chunk 3: Storage Layer

### Task 11: SQLite schema and migrations

**Files:**
- Modify: `src/switchedonvoice/storage/db.py`
- Create: `tests/storage/test_db.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/storage/test_db.py
"""Tests for SQLite schema initialisation and migration."""
import sqlite3
import tempfile
from pathlib import Path
import pytest
from switchedonvoice.storage.db import init_db, get_connection


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


def test_init_creates_sessions_table(db_path: Path) -> None:
    init_db(db_path)
    con = sqlite3.connect(db_path)
    cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
    assert cur.fetchone() is not None
    con.close()


def test_init_creates_frames_table(db_path: Path) -> None:
    init_db(db_path)
    con = sqlite3.connect(db_path)
    cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='frames'")
    assert cur.fetchone() is not None
    con.close()


def test_init_is_idempotent(db_path: Path) -> None:
    init_db(db_path)
    init_db(db_path)  # Second call must not raise


def test_get_connection_returns_connection(db_path: Path) -> None:
    init_db(db_path)
    con = get_connection(db_path)
    assert isinstance(con, sqlite3.Connection)
    con.close()


def test_sessions_table_has_expected_columns(db_path: Path) -> None:
    init_db(db_path)
    con = sqlite3.connect(db_path)
    cur = con.execute("PRAGMA table_info(sessions)")
    columns = {row[1] for row in cur.fetchall()}
    con.close()
    expected = {"id", "date", "duration_secs", "avg_f0", "f0_std_dev", "avg_f2", "milestone_flags_json"}
    assert expected.issubset(columns)


def test_frames_table_has_expected_columns(db_path: Path) -> None:
    init_db(db_path)
    con = sqlite3.connect(db_path)
    cur = con.execute("PRAGMA table_info(frames)")
    columns = {row[1] for row in cur.fetchall()}
    con.close()
    expected = {"id", "session_id", "timestamp_ms", "f0", "f1", "f2", "cpp"}
    assert expected.issubset(columns)


def test_schema_version_is_set(db_path: Path) -> None:
    init_db(db_path)
    con = sqlite3.connect(db_path)
    version = con.execute("PRAGMA user_version").fetchone()[0]
    con.close()
    assert version == 1  # bump this with each schema migration
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/storage/test_db.py -v
```

- [ ] **Step 3: Implement `db.py`**

```python
# src/switchedonvoice/storage/db.py
"""SQLite schema initialisation and connection management.

Schema:
  sessions(id, date, duration_secs, avg_f0, f0_std_dev, avg_f2, milestone_flags_json)
  frames(session_id, timestamp_ms, f0, f1, f2, cpp)

Frames are stored at 5–10 Hz (decimated by the caller). A 60-min session
generates approximately 18,000 rows.
"""
import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    date             TEXT NOT NULL,
    duration_secs    REAL,
    avg_f0           REAL,
    f0_std_dev       REAL,
    avg_f2           REAL,
    milestone_flags_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS frames (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  INTEGER NOT NULL REFERENCES sessions(id),
    timestamp_ms INTEGER NOT NULL,
    f0          REAL,
    f1          REAL,
    f2          REAL,
    cpp         REAL
);

CREATE INDEX IF NOT EXISTS idx_frames_session ON frames(session_id);
"""


_CURRENT_SCHEMA_VERSION = 1


def _migrate(con: sqlite3.Connection) -> None:
    """Run schema migrations in version order.

    Each block is idempotent. To add a migration:
      1. Add an ``elif version < N`` block here.
      2. Bump ``_CURRENT_SCHEMA_VERSION`` above.
    Never remove or reorder existing migration blocks.
    """
    version: int = con.execute("PRAGMA user_version").fetchone()[0]
    if version < 1:
        # v0 → v1: tables are created by _SCHEMA above; just stamp the version.
        con.execute(f"PRAGMA user_version = {_CURRENT_SCHEMA_VERSION}")


def init_db(db_path: Path) -> None:
    """Create tables and run any pending schema migrations.

    Args:
        db_path: Path to the SQLite database file. Created if absent.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(_SCHEMA)
    _migrate(con)
    con.commit()
    con.close()


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Return an open connection with WAL mode and foreign keys enabled.

    The caller is responsible for closing the connection.

    Args:
        db_path: Path to an initialised SQLite database.

    Returns:
        Open sqlite3.Connection.
    """
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/storage/test_db.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/storage/db.py tests/storage/test_db.py
git commit -m "feat(storage): add SQLite schema and init

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 12: Session CRUD and streak calculation

**Files:**
- Modify: `src/switchedonvoice/storage/sessions.py`
- Create: `tests/storage/test_sessions.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/storage/test_sessions.py
"""Tests for session CRUD and streak calculation.

Type note:
  sessions.py defines ``HistoryAggregates`` — the DB aggregate type returned
  by ``get_history_stats()``.  milestones.py defines ``HistoryStats`` — the
  evaluation type consumed by ``evaluate_milestones()``.  These are distinct.
  ``main_window.closeEvent`` bridges them: it calls ``get_history_stats()`` to
  produce a ``HistoryAggregates``, constructs a ``HistoryStats`` from it, and
  passes that to ``evaluate_milestones()``.
"""
import json
from datetime import date, timedelta
from pathlib import Path
import pytest
from switchedonvoice.storage.db import init_db
from switchedonvoice.storage.sessions import (
    HistoryAggregates,
    create_session,
    close_session,
    add_frame,
    get_streak,
    get_all_sessions,
    get_history_stats,
)


@pytest.fixture()
def db(tmp_path: Path) -> Path:
    p = tmp_path / "test.db"
    init_db(p)
    return p


def test_create_and_close_session(db: Path) -> None:
    session_id = create_session(db)
    assert isinstance(session_id, int)
    close_session(db, session_id, duration_secs=300.0, avg_f0=185.0,
                  f0_std_dev=25.0, avg_f2=1800.0, milestone_flags={})
    # Verify stored values
    import sqlite3 as _sqlite3
    con = _sqlite3.connect(db)
    row = con.execute(
        "SELECT duration_secs, avg_f0, f0_std_dev, avg_f2, milestone_flags_json "
        "FROM sessions WHERE id = ?",
        (session_id,),
    ).fetchone()
    con.close()
    assert row is not None
    assert row[0] == pytest.approx(300.0)
    assert row[1] == pytest.approx(185.0)
    assert row[2] == pytest.approx(25.0)
    assert row[3] == pytest.approx(1800.0)
    assert json.loads(row[4]) == {}


def test_add_frame(db: Path) -> None:
    session_id = create_session(db)
    add_frame(db, session_id, timestamp_ms=1000, f0=185.0, f1=500.0, f2=1800.0, cpp=12.0)


def test_get_all_sessions(db: Path) -> None:
    sid = create_session(db)
    close_session(db, sid, 60.0, 180.0, 20.0, 1700.0, {})
    sessions = get_all_sessions(db)
    assert len(sessions) == 1


def test_streak_empty_db(db: Path) -> None:
    assert get_streak(db) == 0


def test_streak_consecutive_days(db: Path) -> None:
    today = date.today()
    for i in range(3):
        d = (today - timedelta(days=i)).isoformat()
        sid = create_session(db)
        close_session(db, sid, 60.0, 180.0, 20.0, 1700.0, {}, date_override=d)
    assert get_streak(db) == 3


def test_streak_broken(db: Path) -> None:
    today = date.today()
    for i in [0, 2]:  # gap on day 1
        d = (today - timedelta(days=i)).isoformat()
        sid = create_session(db)
        close_session(db, sid, 60.0, 180.0, 20.0, 1700.0, {}, date_override=d)
    assert get_streak(db) == 1


def test_streak_multiple_sessions_same_day_count_once(db: Path) -> None:
    today = date.today().isoformat()
    for _ in range(3):
        sid = create_session(db)
        close_session(db, sid, 60.0, 180.0, 20.0, 1700.0, {}, date_override=today)
    assert get_streak(db) == 1


def test_streak_no_session_today_is_zero(db: Path) -> None:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    sid = create_session(db)
    close_session(db, sid, 60.0, 180.0, 20.0, 1700.0, {}, date_override=yesterday)
    assert get_streak(db) == 0


# --- get_history_stats (HistoryAggregates) ---

def test_get_history_stats_empty_db(db: Path) -> None:
    stats = get_history_stats(db, baseline_f2=1600.0)
    assert isinstance(stats, HistoryAggregates)
    assert stats.total_practice_secs == 0
    assert stats.f0_above_165_sessions == 0
    assert stats.f0_above_185_sessions == 0
    assert stats.streak == 0
    assert stats.f2_above_baseline_streak == 0


def test_get_history_stats_totals(db: Path) -> None:
    for _ in range(3):
        sid = create_session(db)
        close_session(db, sid, duration_secs=600.0, avg_f0=190.0,
                      f0_std_dev=20.0, avg_f2=1950.0, milestone_flags={})
    stats = get_history_stats(db, baseline_f2=1600.0)
    assert stats.total_practice_secs == pytest.approx(1800.0)
    assert stats.f0_above_165_sessions == 3
    assert stats.f0_above_185_sessions == 3


def test_get_history_stats_f0_boundaries(db: Path) -> None:
    """avg_f0 == 165 should NOT count as above 165 (strict greater-than)."""
    sid = create_session(db)
    close_session(db, sid, 60.0, avg_f0=165.0, f0_std_dev=0.0, avg_f2=1700.0,
                  milestone_flags={})
    stats = get_history_stats(db, baseline_f2=1600.0)
    assert stats.f0_above_165_sessions == 0

    sid2 = create_session(db)
    close_session(db, sid2, 60.0, avg_f0=165.1, f0_std_dev=0.0, avg_f2=1700.0,
                  milestone_flags={})
    stats2 = get_history_stats(db, baseline_f2=1600.0)
    assert stats2.f0_above_165_sessions == 1


def test_get_history_stats_f2_streak(db: Path) -> None:
    """Sessions with avg_f2 > baseline * 1.20 contribute to f2_above_baseline_streak."""
    baseline_f2 = 1600.0
    threshold = baseline_f2 * 1.20  # 1920.0
    today = date.today()
    for i in range(3):
        d = (today - timedelta(days=2 - i)).isoformat()
        sid = create_session(db)
        close_session(db, sid, 60.0, 185.0, 20.0, avg_f2=threshold + 1.0,
                      milestone_flags={}, date_override=d)
    stats = get_history_stats(db, baseline_f2=baseline_f2)
    assert stats.f2_above_baseline_streak >= 3


def test_get_history_stats_streak_is_non_zero_when_session_today(db: Path) -> None:
    """get_history_stats() returns a non-zero streak when today has a session."""
    sid = create_session(db)
    close_session(db, sid, 60.0, avg_f0=190.0, f0_std_dev=20.0,
                  avg_f2=1900.0, milestone_flags={})
    stats = get_history_stats(db, baseline_f2=1600.0)
    assert stats.streak >= 1, "Streak should be non-zero immediately after a session is recorded today"
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/storage/test_sessions.py -v
```

- [ ] **Step 3: Implement `sessions.py`**

```python
# src/switchedonvoice/storage/sessions.py
"""Session CRUD and streak calculation."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from switchedonvoice.storage.db import get_connection
import json


def create_session(db_path: Path) -> int:
    """Insert a new session row and return its ID."""
    con = get_connection(db_path)
    cur = con.execute(
        "INSERT INTO sessions (date) VALUES (?)",
        (date.today().isoformat(),),
    )
    session_id = cur.lastrowid
    con.commit()
    con.close()
    assert session_id is not None
    return session_id


def close_session(
    db_path: Path,
    session_id: int,
    duration_secs: float,
    avg_f0: float,
    f0_std_dev: float,
    avg_f2: float,
    milestone_flags: dict[str, bool],
    date_override: str | None = None,
) -> None:
    """Update session summary statistics on close."""
    con = get_connection(db_path)
    row_date = date_override or date.today().isoformat()
    con.execute(
        """UPDATE sessions
           SET date=?, duration_secs=?, avg_f0=?, f0_std_dev=?, avg_f2=?, milestone_flags_json=?
           WHERE id=?""",
        (row_date, duration_secs, avg_f0, f0_std_dev, avg_f2,
         json.dumps(milestone_flags), session_id),
    )
    con.commit()
    con.close()


def update_session_milestones(db_path: Path, session_id: int, flags: dict[str, bool]) -> None:
    """Patch the milestone_flags_json on a session that has already been closed.

    Used by ``main_window.closeEvent`` after evaluating milestones — the session
    is closed first (to include it in aggregate queries), then this function
    back-fills the earned flags.

    Args:
        db_path: Path to the SQLite database.
        session_id: Row id of the session to update.
        flags: Mapping of milestone id → True for each newly earned milestone.
    """
    con = get_connection(db_path)
    con.execute(
        "UPDATE sessions SET milestone_flags_json=? WHERE id=?",
        (json.dumps(flags), session_id),
    )
    con.commit()
    con.close()


def add_frame(
    db_path: Path,
    session_id: int,
    timestamp_ms: int,
    f0: float | None,
    f1: float | None,
    f2: float | None,
    cpp: float | None,
) -> None:
    """Insert a single decimated frame row."""
    con = get_connection(db_path)
    con.execute(
        "INSERT INTO frames (session_id, timestamp_ms, f0, f1, f2, cpp) VALUES (?,?,?,?,?,?)",
        (session_id, timestamp_ms, f0, f1, f2, cpp),
    )
    con.commit()
    con.close()


def get_all_sessions(db_path: Path) -> list[dict[str, Any]]:
    """Return all session rows as dicts, newest first."""
    con = get_connection(db_path)
    cur = con.execute("SELECT * FROM sessions ORDER BY id DESC")
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    con.close()
    return rows


def get_streak(db_path: Path) -> int:
    """Return current consecutive day streak (count of days up to and including today).

    A streak is the longest sequence of days ending today where at least one
    session exists.
    """
    con = get_connection(db_path)
    cur = con.execute(
        "SELECT DISTINCT date FROM sessions WHERE date IS NOT NULL ORDER BY date DESC"
    )
    dates = [row[0] for row in cur.fetchall()]
    con.close()

    if not dates:
        return 0

    streak = 0
    check = date.today()
    for d_str in dates:
        d = date.fromisoformat(d_str)
        if d == check:
            streak += 1
            check -= timedelta(days=1)
        elif d < check:
            break
    return streak


@dataclass
class HistoryAggregates:
    """Aggregated counts needed for milestone evaluation, derived from the database.

    This is the DB aggregate type returned by ``get_history_stats()``.
    It is NOT the same as ``HistoryStats`` in ``milestones.py``, which is the
    evaluation type consumed by ``evaluate_milestones()``.

    ``main_window.closeEvent`` bridges them:
      1. Calls ``close_session()`` to persist the current session.
      2. Calls ``get_history_stats()`` → ``HistoryAggregates``.
      3. Constructs a ``HistoryStats`` from the aggregates.
      4. Passes ``HistoryStats`` to ``evaluate_milestones()``.
    """
    total_practice_secs: float     # cumulative sum of all session duration_secs
    streak: int                    # current consecutive-day streak
    f0_above_165_sessions: int     # count of sessions where avg_f0 > 165 Hz
    f0_above_185_sessions: int     # count of sessions where avg_f0 > 185 Hz
    f2_above_baseline_streak: int  # consecutive sessions (most recent first) where avg_f2 > 120% of baseline


def get_history_stats(db_path: Path, baseline_f2: float) -> HistoryAggregates:
    """Query aggregate session stats needed for milestone evaluation.

    Args:
        db_path: Path to the SQLite database.
        baseline_f2: User's baseline F2 in Hz (from Settings). Used to compute
            the F2 above-baseline streak.

    Returns:
        HistoryAggregates with cumulative and streak counters.
    """
    con = get_connection(db_path)

    row = con.execute(
        "SELECT COALESCE(SUM(duration_secs), 0.0) FROM sessions WHERE duration_secs IS NOT NULL"
    ).fetchone()
    total_practice_secs = float(row[0])

    row165 = con.execute(
        "SELECT COUNT(*) FROM sessions WHERE avg_f0 > 165.0"
    ).fetchone()
    f0_above_165 = int(row165[0])

    row185 = con.execute(
        "SELECT COUNT(*) FROM sessions WHERE avg_f0 > 185.0"
    ).fetchone()
    f0_above_185 = int(row185[0])

    # F2 streak: count most-recent consecutive sessions above 120% of baseline
    threshold = baseline_f2 * 1.20 if baseline_f2 > 0 else float("inf")
    rows = con.execute(
        "SELECT avg_f2 FROM sessions WHERE avg_f2 IS NOT NULL ORDER BY id DESC"
    ).fetchall()
    f2_streak = 0
    for (avg_f2,) in rows:
        if avg_f2 is not None and avg_f2 > threshold:
            f2_streak += 1
        else:
            break

    con.close()
    current_streak = get_streak(db_path)
    return HistoryAggregates(
        total_practice_secs=total_practice_secs,
        streak=current_streak,
        f0_above_165_sessions=f0_above_165,
        f0_above_185_sessions=f0_above_185,
        f2_above_baseline_streak=f2_streak,
    )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/storage/test_sessions.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/storage/sessions.py tests/storage/test_sessions.py
git commit -m "feat(storage): add session CRUD and streak calculation

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 13: Settings persistence

**Files:**
- Modify: `src/switchedonvoice/storage/settings.py`
- Create: `tests/storage/test_settings.py`

Settings are stored at `~/.switchedonvoice/settings.json`.

- [ ] **Step 1: Write failing tests**

```python
# tests/storage/test_settings.py
"""Tests for settings.json read/write."""
from pathlib import Path
import pytest
from switchedonvoice.storage.settings import Settings, load_settings, save_settings


@pytest.fixture()
def settings_path(tmp_path: Path) -> Path:
    return tmp_path / "settings.json"


def test_load_missing_returns_defaults(settings_path: Path) -> None:
    s = load_settings(settings_path)
    assert isinstance(s, Settings)
    assert s.device_index is None
    assert s.onboarding_complete is False


def test_save_and_reload(settings_path: Path) -> None:
    s = Settings(device_index=2, onboarding_complete=True,
                 baseline_f0=180.0, baseline_f0_std_dev=20.0, baseline_f2=1750.0)
    save_settings(settings_path, s)
    loaded = load_settings(settings_path)
    assert loaded.device_index == 2
    assert loaded.onboarding_complete is True
    assert loaded.baseline_f0 == pytest.approx(180.0)
    assert loaded.baseline_f0_std_dev == pytest.approx(20.0)
    assert loaded.baseline_f2 == pytest.approx(1750.0)


def test_save_is_valid_json(settings_path: Path) -> None:
    save_settings(settings_path, Settings())
    import json
    data = json.loads(settings_path.read_text())
    assert "device_index" in data
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/storage/test_settings.py -v
```

- [ ] **Step 3: Implement `settings.py`**

```python
# src/switchedonvoice/storage/settings.py
"""Settings persistence via ~/.switchedonvoice/settings.json."""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict, field
from pathlib import Path

_DEFAULT_SETTINGS_PATH = Path.home() / ".switchedonvoice" / "settings.json"


@dataclass
class Settings:
    """Application settings with sensible defaults."""
    device_index: int | None = None
    onboarding_complete: bool = False
    baseline_f0: float | None = None
    baseline_f0_std_dev: float | None = None
    baseline_f2: float | None = None
    noise_floor_rms: float | None = None


def load_settings(path: Path = _DEFAULT_SETTINGS_PATH) -> Settings:
    """Load settings from JSON file. Returns defaults if file is absent or corrupt.

    Args:
        path: Path to settings.json.

    Returns:
        Settings instance populated from file, or default Settings on any read error.
    """
    if not path.exists():
        return Settings()
    try:
        data = json.loads(path.read_text())
        return Settings(
            device_index=data.get("device_index"),
            onboarding_complete=bool(data.get("onboarding_complete", False)),
            baseline_f0=data.get("baseline_f0"),
            baseline_f0_std_dev=data.get("baseline_f0_std_dev"),
            baseline_f2=data.get("baseline_f2"),
            noise_floor_rms=data.get("noise_floor_rms"),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return Settings()


def save_settings(path: Path = _DEFAULT_SETTINGS_PATH, settings: Settings | None = None) -> None:
    """Write settings to JSON file.

    Args:
        path: Path to settings.json. Parent directories are created if absent.
        settings: Settings to write. Writes defaults if None.
    """
    if settings is None:
        settings = Settings()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(settings), indent=2))
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/storage/test_settings.py -v
```

- [ ] **Step 5: Run all storage tests**

```bash
pytest tests/storage/ -v
```

- [ ] **Step 6: Commit**

```bash
git add src/switchedonvoice/storage/settings.py tests/storage/test_settings.py
git commit -m "feat(storage): add settings persistence

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push
```

---

## Chunk 4: Gamification

### Task 14: Milestones engine

**Files:**
- Modify: `src/switchedonvoice/gamification/milestones.py`
- Create: `tests/gamification/test_milestones.py`

The 7 milestones are tied to real acoustic change, not arbitrary time. Each milestone fires once and is recorded in `sessions.milestone_flags_json`.

- [ ] **Step 1: Write failing tests**

```python
# tests/gamification/test_milestones.py
"""Tests for gamification milestone evaluation."""
import pytest
from switchedonvoice.gamification.milestones import (
    MilestoneID,
    evaluate_milestones,
    SessionStats,
    HistoryStats,
)


def make_session(avg_f0: float = 180.0, f0_std_dev: float = 25.0,
                 avg_f2: float = 1700.0, duration_secs: float = 600.0) -> SessionStats:
    return SessionStats(avg_f0=avg_f0, f0_std_dev=f0_std_dev,
                        avg_f2=avg_f2, duration_secs=duration_secs)


def make_history(total_sessions: int = 1, streak: int = 1,
                 f2_above_baseline_streak: int = 0,
                 f0_above_165_sessions: int = 0,
                 f0_above_185_sessions: int = 0,
                 baseline_f2: float = 1400.0,
                 total_practice_secs: float = 0.0,
                 already_earned: set[str] | None = None) -> HistoryStats:
    return HistoryStats(
        total_sessions=total_sessions,
        streak=streak,
        f2_above_baseline_streak=f2_above_baseline_streak,
        f0_above_165_sessions=f0_above_165_sessions,
        f0_above_185_sessions=f0_above_185_sessions,
        baseline_f2=baseline_f2,
        total_practice_secs=total_practice_secs,
        already_earned=already_earned or set(),
    )


def test_first_10_minutes_requires_cumulative_600s() -> None:
    # 400s in history + 300s this session = 700s total → earns it
    earned = evaluate_milestones(
        make_session(duration_secs=300.0),
        make_history(total_practice_secs=700.0),
    )
    assert MilestoneID.FIRST_TEN_MINUTES in earned


def test_first_10_minutes_not_earned_if_cumulative_under_600s() -> None:
    earned = evaluate_milestones(
        make_session(duration_secs=300.0),
        make_history(total_practice_secs=500.0),
    )
    assert MilestoneID.FIRST_TEN_MINUTES not in earned


def test_f0_floor_lifter_triggers_at_165hz() -> None:
    earned = evaluate_milestones(
        make_session(avg_f0=166.0),
        make_history(f0_above_165_sessions=0),
    )
    assert MilestoneID.F0_FLOOR_LIFTER in earned


def test_f0_floor_lifter_not_triggered_at_exactly_165hz() -> None:
    earned = evaluate_milestones(
        make_session(avg_f0=165.0),
        make_history(f0_above_165_sessions=0),
    )
    assert MilestoneID.F0_FLOOR_LIFTER not in earned


def test_feminine_frequency_requires_3_sessions() -> None:
    earned = evaluate_milestones(
        make_session(avg_f0=190.0),
        make_history(f0_above_185_sessions=2),
    )
    assert MilestoneID.FEMININE_FREQUENCY in earned

    earned2 = evaluate_milestones(
        make_session(avg_f0=190.0),
        make_history(f0_above_185_sessions=1),
    )
    assert MilestoneID.FEMININE_FREQUENCY not in earned2


def test_intonation_explorer_requires_std_dev_above_30hz() -> None:
    earned_yes = evaluate_milestones(
        make_session(f0_std_dev=31.0),
        make_history(),
    )
    earned_no = evaluate_milestones(
        make_session(f0_std_dev=29.9),
        make_history(),
    )
    assert MilestoneID.INTONATION_EXPLORER in earned_yes
    assert MilestoneID.INTONATION_EXPLORER not in earned_no


def test_intonation_explorer_exact_boundary_30hz() -> None:
    """30.0 Hz is the boundary — strictly greater-than, so 30.0 must NOT earn."""
    earned = evaluate_milestones(make_session(f0_std_dev=30.0), make_history())
    assert MilestoneID.INTONATION_EXPLORER not in earned


def test_vowel_space_shift_requires_3_consecutive_sessions() -> None:
    # F2 = 1400 baseline → threshold = 1680. Streak of 3 with current avg_f2 > 1680 → earns
    earned_yes = evaluate_milestones(
        make_session(avg_f2=1700.0),
        make_history(f2_above_baseline_streak=3, baseline_f2=1400.0),
    )
    earned_no = evaluate_milestones(
        make_session(avg_f2=1700.0),
        make_history(f2_above_baseline_streak=2, baseline_f2=1400.0),
    )
    assert MilestoneID.VOWEL_SPACE_SHIFT in earned_yes
    assert MilestoneID.VOWEL_SPACE_SHIFT not in earned_no


def test_vowel_space_shift_exact_threshold() -> None:
    """avg_f2 exactly at baseline_f2 * 1.20 must NOT earn (strictly greater-than)."""
    baseline_f2 = 1400.0
    exact_threshold_f2 = baseline_f2 * 1.20  # 1680.0
    earned = evaluate_milestones(
        make_session(avg_f2=exact_threshold_f2),
        make_history(f2_above_baseline_streak=3, baseline_f2=baseline_f2),
    )
    assert MilestoneID.VOWEL_SPACE_SHIFT not in earned


def test_week_warrior_requires_7_day_streak() -> None:
    earned_7 = evaluate_milestones(make_session(), make_history(streak=7))
    earned_6 = evaluate_milestones(make_session(), make_history(streak=6))
    assert MilestoneID.WEEK_WARRIOR in earned_7
    assert MilestoneID.WEEK_WARRIOR not in earned_6


def test_month_strong_requires_30_day_streak() -> None:
    earned_30 = evaluate_milestones(make_session(), make_history(streak=30))
    earned_29 = evaluate_milestones(make_session(), make_history(streak=29))
    assert MilestoneID.MONTH_STRONG in earned_30
    assert MilestoneID.MONTH_STRONG not in earned_29


def test_already_earned_milestones_not_re_awarded() -> None:
    earned = evaluate_milestones(
        make_session(duration_secs=700, f0_std_dev=35.0),
        make_history(total_practice_secs=700.0, already_earned={
            MilestoneID.FIRST_TEN_MINUTES.value,
            MilestoneID.INTONATION_EXPLORER.value,
        }),
    )
    assert MilestoneID.FIRST_TEN_MINUTES not in earned
    assert MilestoneID.INTONATION_EXPLORER not in earned


def test_f0_floor_lifter_not_re_awarded_when_already_earned() -> None:
    """Earning F0 Floor Lifter once should never award it again, even if F0 stays high."""
    earned_first = evaluate_milestones(
        make_session(avg_f0=166.0),
        make_history(already_earned=set()),
    )
    assert MilestoneID.F0_FLOOR_LIFTER in earned_first

    earned_second = evaluate_milestones(
        make_session(avg_f0=200.0),
        make_history(already_earned={MilestoneID.F0_FLOOR_LIFTER.value}),
    )
    assert MilestoneID.F0_FLOOR_LIFTER not in earned_second
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/gamification/test_milestones.py -v
```

- [ ] **Step 3: Implement `milestones.py`**

```python
# src/switchedonvoice/gamification/milestones.py
"""Gamification milestone evaluation.

7 milestones tied to real acoustic progress. Each is earned once only.
The set of earned milestone IDs is stored as JSON in sessions.milestone_flags_json.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class MilestoneID(str, Enum):
    """Stable string IDs for persistence — do not rename without a migration."""
    FIRST_TEN_MINUTES = "first_ten_minutes"
    F0_FLOOR_LIFTER = "f0_floor_lifter"
    FEMININE_FREQUENCY = "feminine_frequency"
    INTONATION_EXPLORER = "intonation_explorer"
    VOWEL_SPACE_SHIFT = "vowel_space_shift"
    WEEK_WARRIOR = "week_warrior"
    MONTH_STRONG = "month_strong"


@dataclass
class SessionStats:
    """Statistics computed from the just-completed session."""
    avg_f0: float
    f0_std_dev: float
    avg_f2: float
    duration_secs: float


@dataclass
class HistoryStats:
    """Aggregated statistics from the user's history, including this session."""
    total_sessions: int
    streak: int
    total_practice_secs: float       # cumulative sum of all session durations
    f2_above_baseline_streak: int    # consecutive sessions where mean F2 > 120% of baseline
    f0_above_165_sessions: int       # cumulative sessions with avg_f0 > 165 Hz
    f0_above_185_sessions: int       # cumulative sessions with avg_f0 > 185 Hz
    baseline_f2: float
    already_earned: set[str] = field(default_factory=set)


_F2_SHIFT_THRESHOLD = 1.20   # 20% above baseline
_F0_STD_DEV_THRESHOLD = 30.0  # Hz — intonation marker


def evaluate_milestones(session: SessionStats, history: HistoryStats) -> set[MilestoneID]:
    """Return the set of milestones newly earned this session.

    Does not mutate the history. The caller is responsible for persisting
    newly earned milestones to the database.

    Args:
        session: Stats from the session just completed.
        history: Cumulative history including the current session's contribution.

    Returns:
        Set of MilestoneID values earned for the first time this session.
    """
    newly_earned: set[MilestoneID] = set()

    def _check(mid: MilestoneID, condition: bool) -> None:
        if condition and mid.value not in history.already_earned:
            newly_earned.add(mid)

    _check(MilestoneID.FIRST_TEN_MINUTES, history.total_practice_secs >= 600)
    # F0 Floor Lifter fires the FIRST time avg_f0 exceeds 165 Hz.
    # "First time" is enforced by the already_earned guard in _check():
    # if MilestoneID.F0_FLOOR_LIFTER is already in history.already_earned,
    # _check() is a no-op and the milestone is NOT re-awarded.
    _check(MilestoneID.F0_FLOOR_LIFTER, session.avg_f0 > 165.0)
    _check(MilestoneID.FEMININE_FREQUENCY, history.f0_above_185_sessions >= 3)
    _check(MilestoneID.INTONATION_EXPLORER, session.f0_std_dev > _F0_STD_DEV_THRESHOLD)
    _check(
        MilestoneID.VOWEL_SPACE_SHIFT,
        history.f2_above_baseline_streak >= 3
        and history.baseline_f2 > 0
        and session.avg_f2 > history.baseline_f2 * _F2_SHIFT_THRESHOLD,
    )
    _check(MilestoneID.WEEK_WARRIOR, history.streak >= 7)
    _check(MilestoneID.MONTH_STRONG, history.streak >= 30)

    return newly_earned
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/gamification/test_milestones.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/gamification/milestones.py tests/gamification/test_milestones.py
git commit -m "feat(gamification): add milestones engine (7 acoustic-tied milestones)

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push
```

---

## Chunk 5: UI Widgets

> All UI tests in this chunk are smoke tests (widget constructs without crash, basic property checks). Full visual correctness is verified by manual inspection during integration.

### Task 15: Pitch meter widget

**Files:**
- Modify: `src/switchedonvoice/ui/pitch_meter.py`
- Create: `tests/ui/__init__.py`
- Create: `tests/ui/test_pitch_meter.py`

Pitch zones: <120Hz deep red | 120–164 red | 165–184 yellow | 185–255 green | >255 blue (head voice — NOT a warning).

- [ ] **Step 1: Write failing smoke test**

```python
# tests/ui/test_pitch_meter.py
"""Smoke tests for PitchMeterWidget."""
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from switchedonvoice.ui.pitch_meter import PitchMeterWidget

import sys
_app = QApplication.instance() or QApplication(sys.argv)


def test_widget_constructs() -> None:
    w = PitchMeterWidget()
    assert w is not None


def test_set_f0_in_green_zone() -> None:
    w = PitchMeterWidget()
    w.set_f0(200.0)   # should not raise


def test_set_f0_none_clears_display() -> None:
    w = PitchMeterWidget()
    w.set_f0(None)    # no voiced frame — display should clear


def test_zone_for_green() -> None:
    from switchedonvoice.ui.pitch_meter import f0_zone_color
    color = f0_zone_color(200.0)
    assert color is not None


def test_zone_boundaries_all_5_zones() -> None:
    from switchedonvoice.ui.pitch_meter import f0_zone_color
    from PySide6.QtGui import QColor
    # Deep red: < 120
    assert f0_zone_color(100.0) == QColor(120, 0, 0)
    # Red: 120–164
    assert f0_zone_color(140.0) == QColor(200, 60, 60)
    assert f0_zone_color(120.0) == QColor(200, 60, 60)   # boundary: 120 is red
    # Yellow: 165–184
    assert f0_zone_color(165.0) == QColor(220, 200, 60)
    assert f0_zone_color(180.0) == QColor(220, 200, 60)
    # Green: 185–255
    assert f0_zone_color(185.0) == QColor(60, 200, 100)
    assert f0_zone_color(255.0) == QColor(60, 200, 100)  # 255 still green
    # Blue: > 255 (head voice — valid, not a warning)
    assert f0_zone_color(256.0) == QColor(80, 160, 255)
    assert f0_zone_color(400.0) == QColor(80, 160, 255)
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/ui/test_pitch_meter.py -v
```

- [ ] **Step 3: Implement `pitch_meter.py`**

```python
# src/switchedonvoice/ui/pitch_meter.py
"""Pitch meter widget.

Displays current F0 as a colour-coded vertical bar.
Zones:
  < 120 Hz : deep red     (very low masculine range)
  120–164  : red          (masculine range)
  165–184  : yellow       (transitional)
  185–255  : green        (feminine target range)
  > 255    : blue         (head voice — valid training territory, not a warning)
"""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QFont, QPen
from collections import deque

_CONTOUR_HISTORY = 300  # ~10 seconds at 30 Hz


_ZONES: list[tuple[float, float, QColor]] = [
    (0.0, 120.0, QColor(120, 0, 0)),
    (120.0, 165.0, QColor(200, 60, 60)),
    (165.0, 185.0, QColor(220, 200, 60)),
    (185.0, 256.0, QColor(60, 200, 100)),
    (256.0, 1200.0, QColor(80, 160, 255)),
]
_F0_MIN = 80.0
_F0_MAX = 500.0


def f0_zone_color(f0: float) -> QColor:
    """Return the display colour for a given F0 value."""
    for low, high, color in _ZONES:
        if low <= f0 < high:
            return color
    return _ZONES[-1][2]


class PitchMeterWidget(QWidget):
    """Vertical bar pitch meter with colour-coded zones."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(60, 250)
        self._f0: float | None = None
        self._contour: deque[float | None] = deque(maxlen=_CONTOUR_HISTORY)
        self._label = QLabel("--- Hz", self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)

    def set_f0(self, f0: float | None) -> None:
        """Update the displayed F0 value, append to rolling contour, and repaint."""
        self._f0 = f0
        self._contour.append(f0)
        if f0 is not None:
            self._label.setText(f"{f0:.0f} Hz")
        else:
            self._label.setText("--- Hz")
        self.update()

    def paintEvent(self, _event: object) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bar_h = h - 30  # reserve space for label
        painter.fillRect(0, 0, w, bar_h, QColor(30, 30, 40))

        if self._f0 is None:
            return

        clamped = max(_F0_MIN, min(self._f0, _F0_MAX))
        ratio = (clamped - _F0_MIN) / (_F0_MAX - _F0_MIN)
        fill_h = int(ratio * bar_h)
        color = f0_zone_color(self._f0)
        painter.fillRect(0, bar_h - fill_h, w, fill_h, color)

        # Rolling F0 contour — last ~10 seconds drawn as a white line above the bar
        contour_points = []
        history = list(self._contour)
        n = len(history)
        if n > 1:
            for i, val in enumerate(history):
                if val is not None:
                    x = int(i / (n - 1) * w)
                    c = max(_F0_MIN, min(val, _F0_MAX))
                    r = (c - _F0_MIN) / (_F0_MAX - _F0_MIN)
                    y = int(bar_h - r * bar_h)
                    contour_points.append((x, y))
            if len(contour_points) > 1:
                pen = QPen(QColor(255, 255, 255, 200), 1)
                painter.setPen(pen)
                for i in range(len(contour_points) - 1):
                    painter.drawLine(*contour_points[i], *contour_points[i + 1])
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/ui/test_pitch_meter.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/ui/pitch_meter.py tests/ui/
git commit -m "feat(ui): add pitch meter widget with colour-coded zones

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 16: Vowel space widget

**Files:**
- Modify: `src/switchedonvoice/ui/vowel_space.py`
- Create: `tests/ui/test_vowel_space.py`

This is the primary resonance display. F1×F2 scatter with "you are here" dot, trail of last ~2 seconds, and reference ellipses for male/female ranges.

- [ ] **Step 1: Write failing smoke test**

```python
# tests/ui/test_vowel_space.py
"""Smoke tests for VowelSpaceWidget."""
import sys
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from switchedonvoice.ui.vowel_space import VowelSpaceWidget

_app = QApplication.instance() or QApplication(sys.argv)


def test_widget_constructs() -> None:
    w = VowelSpaceWidget()
    assert w is not None


def test_add_frame_does_not_raise() -> None:
    w = VowelSpaceWidget()
    w.add_frame(f1=500.0, f2=1800.0)


def test_clear_does_not_raise() -> None:
    w = VowelSpaceWidget()
    w.add_frame(500.0, 1800.0)
    w.clear()
```

- [ ] **Step 2: Implement `vowel_space.py`**

```python
# src/switchedonvoice/ui/vowel_space.py
"""Vowel space (F1×F2) scatter widget.

Reference ellipse centres (from published acoustic data):
  Female: F1=450 Hz, F2=1800 Hz, radii ±200 Hz (F1), ±500 Hz (F2)
  Male:   F1=600 Hz, F2=1300 Hz, radii ±200 Hz (F1), ±400 Hz (F2)

Axes (standard vowel-chart orientation):
  X axis: F2, 500 Hz (left) → 3000 Hz (right) — high F2 = fronted vowel
  Y axis: F1, 900 Hz (top) → 200 Hz (bottom) — low F1 = closed vowel

"You are here" dot colour:
  Green  : within female ellipse (F1 and F2 both within female radii)
  Yellow : between male and female ellipses
  Red    : within male ellipse (F1 and F2 both within male radii)
"""
from __future__ import annotations
from collections import deque
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtCore import Qt

_TRAIL_LEN = 60   # ~2 seconds of history at 30 Hz

# Reference ellipse centres and radii [Hz]
_FEMALE = {"f1": 450.0, "f2": 1800.0, "r_f1": 200.0, "r_f2": 500.0}
_MALE   = {"f1": 600.0, "f2": 1300.0, "r_f1": 200.0, "r_f2": 400.0}

_F2_MIN, _F2_MAX = 500.0, 3000.0
_F1_MIN, _F1_MAX = 200.0, 900.0


def _in_ellipse(f1: float, f2: float, centre: dict) -> bool:
    """Return True if (f1, f2) lies inside the ellipse defined by centre.

    Uses the proper ellipse equation: (dx/r_f1)² + (dy/r_f2)² ≤ 1
    This is NOT a bounding-box test — corners of the bounding box are outside.
    """
    return (
        (f1 - centre["f1"]) ** 2 / centre["r_f1"] ** 2
        + (f2 - centre["f2"]) ** 2 / centre["r_f2"] ** 2
    ) <= 1.0


def _dot_color(f1: float, f2: float) -> QColor:
    if _in_ellipse(f1, f2, _FEMALE):
        return QColor(60, 200, 100)    # green
    if _in_ellipse(f1, f2, _MALE):
        return QColor(200, 60, 60)     # red
    return QColor(220, 200, 60)        # yellow — between ellipses


class VowelSpaceWidget(QWidget):
    """F1×F2 scatter plot with reference ellipses and rolling history trail."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(250, 220)
        self._trail: deque[tuple[float, float]] = deque(maxlen=_TRAIL_LEN)
        self._current: tuple[float, float] | None = None

    def add_frame(self, f1: float, f2: float) -> None:
        """Add a voiced frame to the trail and repaint."""
        self._trail.append((f1, f2))
        self._current = (f1, f2)
        self.update()

    def clear(self) -> None:
        """Clear all history points."""
        self._trail.clear()
        self._current = None
        self.update()

    def _hz_to_px(self, f1: float, f2: float, w: int, h: int) -> tuple[int, int]:
        x = int((f2 - _F2_MIN) / (_F2_MAX - _F2_MIN) * w)
        y = int((_F1_MAX - f1) / (_F1_MAX - _F1_MIN) * h)   # F1 axis inverted
        return x, y

    def _ellipse_rect(self, centre: dict, w: int, h: int):
        cx, cy = self._hz_to_px(centre["f1"], centre["f2"], w, h)
        rx = int(centre["r_f2"] / (_F2_MAX - _F2_MIN) * w)
        ry = int(centre["r_f1"] / (_F1_MAX - _F1_MIN) * h)
        return cx - rx, cy - ry, 2 * rx, 2 * ry

    def paintEvent(self, _event: object) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, QColor(25, 25, 35))

        # Draw reference ellipses
        for centre, color in [(_FEMALE, QColor(60, 200, 100, 80)), (_MALE, QColor(200, 60, 60, 80))]:
            painter.setPen(QPen(color, 1))
            painter.setBrush(color)
            x, y, rw, rh = self._ellipse_rect(centre, w, h)
            painter.drawEllipse(x, y, rw, rh)

        # Draw trail (fading)
        trail = list(self._trail)
        for i, (f1, f2) in enumerate(trail[:-1]):
            alpha = int(40 + 160 * i / max(len(trail) - 1, 1))
            color = QColor(180, 180, 255, alpha)
            painter.setPen(QPen(color, 2))
            px, py = self._hz_to_px(f1, f2, w, h)
            painter.drawEllipse(px - 2, py - 2, 4, 4)

        # Draw "you are here" dot
        if self._current is not None:
            f1, f2 = self._current
            px, py = self._hz_to_px(f1, f2, w, h)
            dot_color = _dot_color(f1, f2)
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setBrush(dot_color)
            painter.drawEllipse(px - 6, py - 6, 12, 12)
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/ui/test_vowel_space.py -v
```

- [ ] **Step 4: Commit**

```bash
git add src/switchedonvoice/ui/vowel_space.py tests/ui/test_vowel_space.py
git commit -m "feat(ui): add vowel space F1×F2 scatter widget

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 17: Spectrum widget

**Files:**
- Modify: `src/switchedonvoice/ui/spectrum_widget.py`
- Create: `tests/ui/test_spectrum_widget.py`

Displays the magnitude spectrum as a line plot. Y-axis: dBFS. X-axis: 0–8 kHz (sufficient for voice analysis).

- [ ] **Step 1: Write failing smoke test**

```python
# tests/ui/test_spectrum_widget.py
"""Smoke tests for SpectrumWidget."""
import sys
import numpy as np
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from switchedonvoice.ui.spectrum_widget import SpectrumWidget

_app = QApplication.instance() or QApplication(sys.argv)


def test_widget_constructs() -> None:
    assert SpectrumWidget() is not None


def test_update_spectrum_does_not_raise() -> None:
    w = SpectrumWidget()
    freqs = np.linspace(0, 22050, 2049).astype(np.float32)
    db = np.random.uniform(-80, 0, 2049).astype(np.float32)
    w.update_spectrum(freqs, db)
```

- [ ] **Step 2: Implement `spectrum_widget.py`**

QPainter-based line plot. Clip display to 0–8 kHz. Y range: −90 dBFS to 0 dBFS. Draw horizontal grid lines at −20, −40, −60 dBFS. Colour the line green. No Qt Charts dependency.

- [ ] **Step 3: Run tests**

```bash
pytest tests/ui/test_spectrum_widget.py -v
```

- [ ] **Step 4: Commit**

```bash
git add src/switchedonvoice/ui/spectrum_widget.py tests/ui/test_spectrum_widget.py
git commit -m "feat(ui): add spectrum display widget (QPainter line plot)

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 18: Analysis panel (wires live data to widgets)

**Files:**
- Modify: `src/switchedonvoice/ui/analysis_panel.py`
- Create: `src/switchedonvoice/ui/waveform_widget.py`
- Create: `tests/ui/test_analysis_panel.py`

The analysis panel holds the pitch meter, vowel space, waveform, spectrum, and CPP widgets. It exposes `update_result(AnalysisResult)` which is called by the QTimer in main_window.

Spec refs: waveform display — spec lines 137–143, 234–243.

- [ ] **Step 1: Write failing smoke test**

```python
# tests/ui/test_analysis_panel.py
"""Smoke tests for AnalysisPanel."""
import sys
import numpy as np
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from switchedonvoice.ui.analysis_panel import AnalysisPanel
from switchedonvoice.audio.capture import AnalysisResult

_app = QApplication.instance() or QApplication(sys.argv)


def test_panel_constructs() -> None:
    assert AnalysisPanel() is not None


def test_update_voiced_result() -> None:
    panel = AnalysisPanel()
    result = AnalysisResult(
        f0=200.0, formants=[500.0, 1800.0, 2700.0], cpp=12.0,
        is_voiced=True,
        spectrum_freqs=np.linspace(0, 22050, 2049, dtype=np.float32),
        spectrum_db=np.full(2049, -40.0, dtype=np.float32),
    )
    panel.update_result(result)


def test_update_unvoiced_result() -> None:
    panel = AnalysisPanel()
    result = AnalysisResult(
        f0=None, formants=[], cpp=None,
        is_voiced=False,
        spectrum_freqs=np.linspace(0, 22050, 2049, dtype=np.float32),
        spectrum_db=np.full(2049, -80.0, dtype=np.float32),
    )
    panel.update_result(result)
```

- [ ] **Step 2: Implement `waveform_widget.py`**

```python
# src/switchedonvoice/ui/waveform_widget.py
"""Time-domain waveform display widget.

Spec refs: lines 137–143, 234–243.
Renders the most recent 200 ms of raw audio as a green line plot on a dark
background. Y axis is normalised to ±1.0. The widget is updated by
AnalysisPanel.update_result() on every incoming frame.
"""
from __future__ import annotations
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QWidget, QSizePolicy


class WaveformWidget(QWidget):
    """Scrolling time-domain waveform display (200 ms window)."""

    _BACKGROUND = QColor(20, 20, 20)
    _LINE_COLOR = QColor(60, 200, 100)    # green
    _LINE_WIDTH = 1.5

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._samples: np.ndarray = np.zeros(0, dtype=np.float32)
        self.setMinimumSize(200, 60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(80)

    def update_waveform(self, samples: np.ndarray) -> None:
        """Accept a new audio buffer (float32, any length) and repaint."""
        self._samples = samples[-4096:] if len(samples) > 4096 else samples
        self.update()

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        w, h = self.width(), self.height()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(0, 0, w, h, self._BACKGROUND)

        samples = self._samples
        if len(samples) < 2:
            return

        pen = QPen(self._LINE_COLOR)
        pen.setWidthF(self._LINE_WIDTH)
        painter.setPen(pen)

        n = len(samples)
        half_h = h / 2.0
        step = w / (n - 1)

        poly = QPolygonF()
        for i, amp in enumerate(samples):
            x = i * step
            # Clamp to ±1 then map to pixel height (0 at top)
            y = half_h - float(np.clip(amp, -1.0, 1.0)) * (half_h - 2)
            poly.append(QPointF(x, y))

        painter.drawPolyline(poly)
        painter.end()
```

- [ ] **Step 3: Implement `analysis_panel.py`**

Compose `PitchMeterWidget`, `VowelSpaceWidget`, `WaveformWidget`, `SpectrumWidget`, and a CPP `QLabel` in a horizontal or grid layout. `update_result(result)` dispatches to each child. Freeze vowel space updates on unvoiced frames (do not add garbage formants).

The CPP display is a `QLabel` showing "CPP: 12.3 dB" or "CPP: —". It has no colour coding (CPP is observation-only). Add a tooltip: "Cepstral Peak Prominence — a measure of voice quality and phonation regularity. Higher = more periodic/less breathy. Provided as an observation only; no target is set."

```python
# src/switchedonvoice/ui/analysis_panel.py
"""Analysis panel: composes pitch meter, waveform, vowel space, spectrum, and CPP label."""
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from switchedonvoice.ui.pitch_meter import PitchMeterWidget
from switchedonvoice.ui.waveform_widget import WaveformWidget
from switchedonvoice.ui.vowel_space import VowelSpaceWidget
from switchedonvoice.ui.spectrum_widget import SpectrumWidget
from switchedonvoice.audio.capture import AnalysisResult


class AnalysisPanel(QWidget):
    """Main analysis display: pitch meter, waveform, vowel space, spectrum, and CPP."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pitch = PitchMeterWidget()
        self._waveform = WaveformWidget()
        self._vowel = VowelSpaceWidget()
        self._spectrum = SpectrumWidget()
        self._cpp_label = QLabel("CPP: —")
        self._cpp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cpp_label.setToolTip(
            "Cepstral Peak Prominence — a measure of voice quality and phonation regularity.\n"
            "Higher = more periodic / less breathy. Provided as an observation only; no target is set."
        )

        left = QVBoxLayout()
        left.addWidget(self._pitch)
        left.addWidget(self._cpp_label)
        left.addWidget(self._waveform)

        layout = QHBoxLayout(self)
        layout.addLayout(left)
        layout.addWidget(self._vowel, stretch=2)
        layout.addWidget(self._spectrum, stretch=3)

    def update_result(self, result: AnalysisResult) -> None:
        """Dispatch a new analysis frame to all child widgets."""
        self._pitch.set_f0(result.f0)
        if result.raw_audio is not None:
            self._waveform.update_waveform(result.raw_audio)
        if result.is_voiced and len(result.formants) >= 2:
            self._vowel.add_frame(f1=result.formants[0], f2=result.formants[1])
        if result.cpp is not None:
            self._cpp_label.setText(f"CPP: {result.cpp:.1f} dB")
        else:
            self._cpp_label.setText("CPP: —")
        self._spectrum.update_spectrum(result.spectrum_freqs, result.spectrum_db)
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/ui/test_analysis_panel.py -v
```

- [ ] **Step 4: Run all UI tests**

```bash
pytest tests/ui/ -v
```

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/ui/analysis_panel.py src/switchedonvoice/ui/waveform_widget.py tests/ui/test_analysis_panel.py
git commit -m "feat(ui): add analysis panel with waveform, pitch, vowel, spectrum widgets

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push
```

---

## Chunk 6: UI Panels

### Task 19: Exercise panel

**Files:**
- Modify: `src/switchedonvoice/ui/exercise_panel.py`
- Create: `tests/ui/test_exercise_panel.py`

Each exercise card shows: name, description, 2–3 sentences of physical technique, and a "Start" button. No tests beyond smoke — exercise content is static data.

- [ ] **Step 1: Define exercise data**

In `exercise_panel.py`, define a list of exercise dictionaries:

```python
EXERCISES = [
    {
        "name": "Pitch Slide",
        "description": "Slide your pitch smoothly into your target zone and hold.",
        "technique": (
            "Start at your habitual pitch. Imagine your voice becoming lighter and smaller. "
            "Slide upward into your target zone and hold it steady for 5 seconds. "
            "Watch the pitch meter bar — aim for the green zone."
        ),
    },
    {
        "name": "Vowel Resonance",
        "description": "Shift your vowel resonance forward to raise F2.",
        "technique": (
            "Say 'ee' (as in 'see') with a bright, forward feeling in your mouth. "
            "Raise the front of your tongue toward your hard palate while sustaining the sound. "
            "Watch the F2 dot on the vowel map move right and up."
        ),
    },
    {
        "name": "Free Practice",
        "description": "Talk, read aloud, or experiment freely.",
        "technique": (
            "No rules — talk, read aloud, or experiment. "
            "Watch the meters and notice what changes your voice. "
            "This session is recorded for your progress history."
        ),
    },
]
```

- [ ] **Step 2: Implement the panel**

Build a scrollable list of exercise cards (QWidget per card, QScrollArea container). Each card: bold title, description, technique text in a lighter colour, Start button with timer behaviour:

- Start button label is **"Start"** initially.
- When clicked, start a `QTimer` with a duration specific to each exercise (e.g., 30 seconds for "Pitch Slide", 30 s for "Vowel Resonance", no limit for "Free Practice"). Change button label to **"Stop"**.
- Display a `countdown_label: QLabel` that counts down from the exercise duration. Update it every second from the `QTimer.timeout` signal.
- When the timer fires (duration reached), call a `_on_timer_complete()` method that: stops the timer, shows a `completion_label: QLabel` with text "Done! 🎉" (set `completion_label.setVisible(True)`), resets the button label to **"Start"**, and resets the countdown label to the initial duration.
- If "Stop" is clicked before completion, stop the timer and reset to "Start" state **without** showing the completion label (call `completion_label.setVisible(False)`).
- `completion_label` starts hidden (`setVisible(False)` in `__init__`).
- For "Free Practice" (no time limit), the Start/Stop toggle has no countdown and no completion event; it simply starts/stops the session.
- Expose `ExerciseCard` at module level so tests can instantiate individual cards directly.

- [ ] **Step 3: Write timer state machine tests**

```python
# tests/ui/test_exercise_panel.py
"""Tests for ExerciseCard timer state machine.

Covers: Start→Stop transition, countdown runs, completion reset,
and manual Stop before completion.
"""
import sys
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from switchedonvoice.ui.exercise_panel import ExerciseCard, EXERCISES

_app = QApplication.instance() or QApplication(sys.argv)


@pytest.fixture()
def timed_card(qtbot):
    """Return an ExerciseCard for 'Pitch Slide' (30 s timer)."""
    card = ExerciseCard(EXERCISES[0])  # "Pitch Slide", duration=30
    qtbot.addWidget(card)
    return card


def test_start_button_initial_label(timed_card) -> None:
    assert timed_card.start_button.text() == "Start"


def test_clicking_start_changes_label_to_stop(qtbot, timed_card) -> None:
    qtbot.mouseClick(timed_card.start_button, Qt.LeftButton)
    assert timed_card.start_button.text() == "Stop"


def test_clicking_stop_before_completion_resets_to_start(qtbot, timed_card) -> None:
    qtbot.mouseClick(timed_card.start_button, Qt.LeftButton)  # → Stop
    qtbot.mouseClick(timed_card.start_button, Qt.LeftButton)  # → Start (manual stop)
    assert timed_card.start_button.text() == "Start"
    # Countdown label should also reset to initial duration
    assert "30" in timed_card.countdown_label.text()
    # Completion message must NOT be visible after a manual stop
    assert not timed_card.completion_label.isVisible()


def test_timer_completion_resets_to_start(qtbot, timed_card) -> None:
    """When the QTimer fires (duration reached), button resets to 'Start'."""
    qtbot.mouseClick(timed_card.start_button, Qt.LeftButton)  # start
    # Directly invoke the timeout handler to simulate expiry without waiting 30s
    timed_card._on_timer_complete()
    assert timed_card.start_button.text() == "Start"
    assert "30" in timed_card.countdown_label.text()
    # Completion message MUST be visible after natural timer expiry
    assert timed_card.completion_label.isVisible()
```

- [ ] **Step 4: Run timer tests to confirm failure**

```bash
pytest tests/ui/test_exercise_panel.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/ui/exercise_panel.py tests/ui/test_exercise_panel.py
git commit -m "feat(ui): add exercise panel with technique guidance

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 20: Progress panel

**Files:**
- Modify: `src/switchedonvoice/ui/progress_panel.py`

Shows: current streak, list of earned milestones (with date earned), weekly average chart (F0 mean and F0 std dev per calendar week), and a session history table (date, duration, avg F0, F0 std dev, avg F2).

- [ ] **Step 1: Implement `progress_panel.py`**

Takes a `db_path: Path` on construction. Calls `get_all_sessions()` and `get_streak()` to populate. Add a `refresh()` method called after each session closes.

**Session history:** `QTableWidget` with columns: Date, Duration (min), Avg F0 (Hz), F0 Std Dev (Hz), Avg F2 (Hz).

**Milestone badges:** One `QLabel` per milestone with coloured background (earned: green with date text; unearned: grey). Display each badge as: `"🏆 <milestone name>\n<date earned>"` or `"<milestone name>\n(not yet earned)"`.

**Weekly average chart:** Use `QPainter` to draw a simple bar or line chart. Group sessions by ISO calendar week (`date.isocalendar().week`). For each week, compute the mean F0 and mean F0 std dev from that week's sessions. Draw two series: F0 mean (green line) and F0 std dev (yellow line). Label axes. No Qt Charts dependency — use pure QPainter on a `QWidget` subclass `WeeklyChartWidget` (defined in the same file).

- [ ] **Step 2: Smoke test + data verification test**

```python
# in tests/ui/test_progress_panel.py
import pytest
from datetime import date
from pathlib import Path

@pytest.fixture()
def db(tmp_path: Path):
    from switchedonvoice.storage.db import init_db
    p = tmp_path / "test.db"
    init_db(p)
    return p


def test_panel_constructs(db):
    from switchedonvoice.ui.progress_panel import ProgressPanel
    panel = ProgressPanel(db_path=db)
    assert panel is not None


def test_session_table_reflects_inserted_data(db):
    from switchedonvoice.storage.sessions import create_session, close_session
    from switchedonvoice.ui.progress_panel import ProgressPanel

    sid = create_session(db)
    close_session(db, sid, duration_secs=300.0, avg_f0=185.0, f0_std_dev=28.0,
                  avg_f2=1850.0, milestone_flags={})

    panel = ProgressPanel(db_path=db)
    table = panel._history_table   # access the QTableWidget via test seam
    assert table.rowCount() == 1

    # Columns: Date, Duration (min), Avg F0 (Hz), F0 Std Dev (Hz), Avg F2 (Hz)
    col_headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
    assert "F0 Std Dev (Hz)" in col_headers

    f0_col = col_headers.index("Avg F0 (Hz)")
    std_col = col_headers.index("F0 Std Dev (Hz)")
    f2_col  = col_headers.index("Avg F2 (Hz)")
    assert float(table.item(0, f0_col).text()) == pytest.approx(185.0, abs=0.1)
    assert float(table.item(0, std_col).text()) == pytest.approx(28.0, abs=0.1)
    assert float(table.item(0, f2_col).text()) == pytest.approx(1850.0, abs=0.1)
```

Note: expose `_history_table` as a public-enough name for tests (prefix underscore is a convention, not enforced). Alternatively, add a `history_table` property. Either is fine.

- [ ] **Step 3: Commit**

```bash
git add src/switchedonvoice/ui/progress_panel.py tests/ui/test_progress_panel.py
git commit -m "feat(ui): add progress panel (streak, milestones, session history)

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 21: Settings panel

**Files:**
- Modify: `src/switchedonvoice/ui/settings_panel.py`
- Create: `src/switchedonvoice/onboarding/baseline_dialog.py`

Device selector (QComboBox populated from sounddevice.query_devices()), save button, and a "Re-record baseline" button. Emits a Qt signal when device changes so MainWindow can restart capture.

- [ ] **Step 1: Implement `settings_panel.py`**

```python
from PySide6.QtCore import Signal

class SettingsPanel(QWidget):
    device_changed = Signal(int)   # emits new device_index
```

Populate device list on `__init__` and on a "Refresh" button. Persist selected device via `save_settings`.

**F0 target range overrides (spec lines 153–155):** Add two `QSpinBox` widgets labelled "F0 target min (Hz)" and "F0 target max (Hz)". Default values: 185 and 255. Store in `Settings` as `f0_target_min` and `f0_target_max`. Persist on save. The pitch meter zones in `pitch_meter.py` should read these values from `Settings` rather than hardcoding the boundaries (update `PitchMeterWidget` to accept optional min/max on construction or as a setter).

**Re-record baseline button:** A `QPushButton("Re-record baseline")`. When clicked, open a modal `QDialog` that reuses the onboarding baseline recording page logic: capture 30 seconds of audio, compute mean F0 / F0 std dev / mean F2 from voiced frames, update the settings file via `save_settings`, and show a confirmation. Extract the baseline recording page into a shared `BaselineRecordingDialog` in `src/switchedonvoice/onboarding/baseline_dialog.py` (avoids circular imports). Both the settings panel and the onboarding wizard use this dialog.

- [ ] **Step 2: Smoke test for `baseline_dialog.py`**

```python
# tests/onboarding/test_baseline_dialog.py
def test_baseline_dialog_constructs(qtbot):
    from switchedonvoice.onboarding.baseline_dialog import BaselineRecordingDialog
    dlg = BaselineRecordingDialog(device_index=None)
    assert dlg is not None
```

- [ ] **Step 3: Commit**

```bash
git add src/switchedonvoice/ui/settings_panel.py \
        src/switchedonvoice/onboarding/baseline_dialog.py \
        tests/onboarding/test_baseline_dialog.py
git commit -m "feat(ui): add settings panel with device selector, F0 range overrides, and baseline re-record

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push
```

---

## Chunk 7: Onboarding, Health, Main Window, and Wiring

### Task 22: Vocal health warnings

**Files:**
- Modify: `src/switchedonvoice/health.py`
- Create: `tests/test_health.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_health.py
"""Tests for vocal health warning logic."""
import pytest
from switchedonvoice.health import should_warn, WarningLevel


def test_no_warning_under_45_minutes() -> None:
    assert should_warn(elapsed_secs=2699) == WarningLevel.NONE


def test_yellow_warning_at_45_minutes() -> None:
    assert should_warn(elapsed_secs=2700) == WarningLevel.YELLOW


def test_red_warning_at_60_minutes() -> None:
    assert should_warn(elapsed_secs=3600) == WarningLevel.RED


def test_red_warning_persists_after_60_minutes() -> None:
    assert should_warn(elapsed_secs=4000) == WarningLevel.RED
```

- [ ] **Step 2: Implement `health.py`**

```python
# src/switchedonvoice/health.py
"""Vocal health warnings based on session elapsed time."""
from enum import Enum

_YELLOW_THRESHOLD_SECS = 45 * 60
_RED_THRESHOLD_SECS = 60 * 60


class WarningLevel(Enum):
    NONE = "none"
    YELLOW = "yellow"   # "Consider taking a break"
    RED = "red"         # "Please rest your voice"


def should_warn(elapsed_secs: float) -> WarningLevel:
    """Return the appropriate warning level for the given elapsed time."""
    if elapsed_secs >= _RED_THRESHOLD_SECS:
        return WarningLevel.RED
    if elapsed_secs >= _YELLOW_THRESHOLD_SECS:
        return WarningLevel.YELLOW
    return WarningLevel.NONE
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/test_health.py -v
```

- [ ] **Step 4: Commit**

```bash
git add src/switchedonvoice/health.py tests/test_health.py
git commit -m "feat: add vocal health warnings (45 min and 60 min)

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 23: Onboarding wizard

**Files:**
- Modify: `src/switchedonvoice/onboarding/wizard.py`
- Modify: `src/switchedonvoice/storage/settings.py`

5-step wizard. Each step is a QWizardPage. Uses QWizard.

Steps:
1. **Mic permission** — display info, no user action needed on Linux
2. **Mic selector** — same device QComboBox as settings panel, shared component
3. **Ambient calibration** — "Remain silent for 10 seconds" + countdown timer; captures 10 seconds of audio, computes RMS mean as the noise floor, stores as `noise_floor_rms` in `Settings`. Add `noise_floor_rms: float | None = None` to the `Settings` dataclass and `load_settings` / `save_settings`.
4. **Baseline recording** — "Speak naturally for 30 seconds" + progress bar + live pitch meter; extracts habitual F0 mean, F0 std dev, F2 mean, and **F2 std dev** on completion, stores to `Settings`. All four values are required by the Vowel Space Shift milestone evaluation.
5. **Done** — show labelled screenshot of the main UI, "Start training" button

- [ ] **Step 1: Update `Settings` dataclass in `settings.py`**

Add `baseline_f2_std_dev: float | None = None` alongside the existing `baseline_f2` field. Update `load_settings()` and `save_settings()` to serialise/deserialise it. On the baseline recording page, compute F2 std dev from voiced frames using `numpy.std()` (same frame set as F2 mean) and store it.

Also add `f0_target_min: int = 185` and `f0_target_max: int = 255` if not already present (from Task 21 spinboxes).

- [ ] **Step 2: Implement `wizard.py`**

Implement all 5 pages as QWizardPage subclasses. On the baseline page, start `AudioCapture` for 30 seconds, collect `AnalysisResult` objects, compute mean F0, F0 std dev, mean F2, and F2 std dev from voiced frames, and store to `Settings` via `save_settings`. Emit a `wizard_complete` Qt signal on the final page with the computed baseline.

- [ ] **Step 3: Smoke test (with persistence and signal verification)**

```python
def test_wizard_constructs(tmp_path):
    from switchedonvoice.onboarding.wizard import OnboardingWizard
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    settings_path = tmp_path / "settings.json"
    w = OnboardingWizard(settings_path=settings_path)
    assert w is not None


def test_wizard_emits_complete_and_persists_baseline(tmp_path, qtbot):
    """
    Simulate completing the wizard by calling accept() on the ambient and
    baseline pages, then verify:
    - settings.json is written with noise_floor_rms and baseline_f2
    - wizard_complete signal would have been emitted
    """
    import json
    from switchedonvoice.onboarding.wizard import OnboardingWizard
    from switchedonvoice.storage.settings import load_settings

    settings_path = tmp_path / "settings.json"
    wizard = OnboardingWizard(settings_path=settings_path)

    # Track wizard_complete signal
    emitted: list[bool] = []
    wizard.wizard_complete.connect(lambda: emitted.append(True))

    # Fake ambient calibration completion by directly writing the settings
    # (the real wizard page does this via AudioCapture; we skip capture here)
    import json as _json
    settings_path.write_text(_json.dumps({
        "noise_floor_rms": 0.002,
        "baseline_f0": 180.0,
        "baseline_f0_std_dev": 22.0,
        "baseline_f2": 1750.0,
        "baseline_f2_std_dev": 150.0,
        "onboarding_complete": True,
    }))

    # Simulate finishing the wizard
    wizard.accept()

    # The wizard's accept() override MUST emit wizard_complete before calling super().accept()
    assert len(emitted) > 0, "wizard_complete signal was not emitted on wizard.accept()"

    settings = load_settings(settings_path)
    assert settings.noise_floor_rms is not None
    assert settings.baseline_f2 is not None
    assert settings.baseline_f2_std_dev is not None
```

- [ ] **Step 4: Commit**

```bash
git add src/switchedonvoice/onboarding/wizard.py \
        src/switchedonvoice/storage/settings.py
git commit -m "feat(onboarding): add 5-step wizard with baseline calibration (incl. F2 std dev)

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 24: Main window and final wiring

**Files:**
- Modify: `src/switchedonvoice/ui/main_window.py`

This is the top-level integration. MainWindow:
- On startup: checks `Settings.onboarding_complete`; if False, shows `OnboardingWizard` modally
- Creates `AudioCapture` with device from settings
- Creates a `QTabWidget` with tabs: Analysis, Exercises, Progress, Settings
- Starts a `QTimer` at 30 Hz that drains `capture.results` and calls `analysis_panel.update_result()`
- Shows vocal health warnings in a status bar area
- On `SettingsPanel.device_changed`: stops capture, updates device, restarts capture
- On close: stops capture, closes session with computed stats, evaluates milestones, refreshes progress panel

- [ ] **Step 1: Implement `main_window.py`**

```python
# src/switchedonvoice/ui/main_window.py
"""Top-level application window."""
from __future__ import annotations
import time
from pathlib import Path
from PySide6.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QLabel
from PySide6.QtCore import QTimer
from switchedonvoice.audio.capture import AudioCapture
from switchedonvoice.storage.db import init_db
from switchedonvoice.storage.settings import load_settings, save_settings
from switchedonvoice.storage.sessions import create_session, close_session, add_frame, get_streak, get_history_stats, get_all_sessions, update_session_milestones
from switchedonvoice.gamification.milestones import evaluate_milestones, SessionStats, HistoryStats
from switchedonvoice.health import should_warn, WarningLevel
from switchedonvoice.ui.analysis_panel import AnalysisPanel
from switchedonvoice.ui.exercise_panel import ExercisePanel
from switchedonvoice.ui.progress_panel import ProgressPanel
from switchedonvoice.ui.settings_panel import SettingsPanel
from switchedonvoice.onboarding.wizard import OnboardingWizard
import numpy as np

_DB_PATH = Path.home() / ".switchedonvoice" / "data.db"
_SETTINGS_PATH = Path.home() / ".switchedonvoice" / "settings.json"
_TIMER_INTERVAL_MS = 33  # ~30 Hz
_FRAME_DECIMATE_RATE = 5  # store every 5th analysis frame (~6 Hz at 30 Hz analysis)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SwitchedOnVoice")
        self.resize(1100, 700)

        init_db(_DB_PATH)
        self._settings = load_settings(_SETTINGS_PATH)

        if not self._settings.onboarding_complete:
            wizard = OnboardingWizard(settings_path=_SETTINGS_PATH)
            wizard.exec()
            self._settings = load_settings(_SETTINGS_PATH)

        self._capture = AudioCapture(
            device_index=self._settings.device_index,
        )

        self._analysis_panel = AnalysisPanel()
        self._exercise_panel = ExercisePanel()
        self._progress_panel = ProgressPanel(db_path=_DB_PATH)
        self._settings_panel = SettingsPanel(settings_path=_SETTINGS_PATH)
        self._settings_panel.device_changed.connect(self._on_device_changed)

        tabs = QTabWidget()
        tabs.addTab(self._analysis_panel, "Analysis")
        tabs.addTab(self._exercise_panel, "Exercises")
        tabs.addTab(self._progress_panel, "Progress")
        tabs.addTab(self._settings_panel, "Settings")
        self.setCentralWidget(tabs)

        self._status_label = QLabel("")
        status_bar = QStatusBar()
        status_bar.addWidget(self._status_label)
        self.setStatusBar(status_bar)

        self._session_id = create_session(_DB_PATH)
        self._session_start = time.monotonic()
        self._f0_history: list[float] = []
        self._f2_history: list[float] = []
        self._frame_counter = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(_TIMER_INTERVAL_MS)
        self._capture.start()

    def _tick(self) -> None:
        while not self._capture.results.empty():
            try:
                result = self._capture.results.get_nowait()
            except Exception:  # noqa: BLE001
                break
            self._analysis_panel.update_result(result)

            if result.is_voiced and result.f0 is not None:
                self._f0_history.append(result.f0)
            if result.is_voiced and len(result.formants) >= 2:
                self._f2_history.append(result.formants[1])

            # Decimate storage
            self._frame_counter += 1
            if self._frame_counter % _FRAME_DECIMATE_RATE == 0:
                f1 = result.formants[0] if len(result.formants) >= 1 else None
                f2 = result.formants[1] if len(result.formants) >= 2 else None
                elapsed_ms = int((time.monotonic() - self._session_start) * 1000)
                add_frame(_DB_PATH, self._session_id, elapsed_ms,
                          result.f0, f1, f2, result.cpp)

        # Vocal health check
        elapsed = time.monotonic() - self._session_start
        level = should_warn(elapsed)
        if level == WarningLevel.RED:
            self._status_label.setText("⚠️  Please rest your voice — you've been training for over 60 minutes.")
        elif level == WarningLevel.YELLOW:
            self._status_label.setText("💛 Consider taking a break — 45 minutes of training completed.")
        else:
            self._status_label.setText("")

    def _on_device_changed(self, device_index: int) -> None:
        self._capture.stop()
        self._settings.device_index = device_index
        save_settings(_SETTINGS_PATH, self._settings)
        self._capture = AudioCapture(device_index=device_index)
        self._capture.start()

    def closeEvent(self, event: object) -> None:  # noqa: ANN001
        self._timer.stop()
        self._capture.stop()

        duration = time.monotonic() - self._session_start
        avg_f0 = float(np.mean(self._f0_history)) if self._f0_history else 0.0
        f0_std = float(np.std(self._f0_history)) if self._f0_history else 0.0
        avg_f2 = float(np.mean(self._f2_history)) if self._f2_history else 0.0

        # IMPORTANT: call close_session() FIRST — this persists the current session
        # to the DB. Only AFTER that do we query get_history_stats() so the current
        # session's contribution is included in milestone evaluation.
        # The session is initially closed with empty flags; we update them below.
        close_session(_DB_PATH, self._session_id, duration, avg_f0, f0_std, avg_f2,
                      milestone_flags={})

        # Now query history — current session is included
        session_stats = SessionStats(avg_f0=avg_f0, f0_std_dev=f0_std,
                                     avg_f2=avg_f2, duration_secs=duration)
        streak = get_streak(_DB_PATH)
        baseline_f2 = self._settings.baseline_f2 or 1400.0
        agg = get_history_stats(_DB_PATH, baseline_f2=baseline_f2)
        all_sessions = get_all_sessions(_DB_PATH)
        history = HistoryStats(
            total_sessions=len(all_sessions),
            streak=streak,
            total_practice_secs=agg.total_practice_secs,
            f2_above_baseline_streak=agg.f2_above_baseline_streak,
            f0_above_165_sessions=agg.f0_above_165_sessions,
            f0_above_185_sessions=agg.f0_above_185_sessions,
            baseline_f2=baseline_f2,
        )
        earned = evaluate_milestones(session_stats, history)
        # Always call update_session_milestones — back-fills flags even if none were earned
        # (empty dict is correct; it replaces the placeholder '{}' set by close_session above)
        flags = {m.value: True for m in earned}
        update_session_milestones(_DB_PATH, self._session_id, flags)

        self._progress_panel.refresh()
        super().closeEvent(event)  # type: ignore[arg-type]
```

- [ ] **Step 2: Manual smoke test**

```bash
python run.py
```

Expected: application window opens, tabs visible, no crash on close.

- [ ] **Step 3: Run full test suite**

```bash
pytest -v
```

Expected: all tests pass (or known UI-only tests skip if no display is available).

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "feat: complete Phase 1 — SwitchedOnVoice MVP

Full pipeline: audio capture → F0/formants/CPP → Qt display.
Vowel space, pitch meter, spectrum, exercise panel, progress
panel, milestones, onboarding wizard, vocal health warnings.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push
```

---

## Open Questions

These are NOT open — they are resolved by the spikes in Chunk 1. They are listed here for reference only.

| # | Question | Resolution |
|---|----------|------------|
| 1 | LPC order (12, 14, or 16) | Resolved by **Spike 2** (Chunk 1). Run the validation script, record results in `spikes/SPIKE_NOTES.md`, update the `_LPC_ORDER` constant in `formants.py` before starting Chunk 2. |
| 2 | pyworld buffer size and latency | Resolved by **Spike 1** (Chunk 1). Benchmark 200 ms buffer on your hardware, record in `SPIKE_NOTES.md`, update `_BUFFER_SECS` in `capture.py` if needed before starting Chunk 2. |

Do not treat these as blockers during implementation — they are spike-gated decisions, not unknowns.

---

## Phase 2 Reminder (out of scope for this plan)

Phase 2 restructures the single-process architecture so a Tauri frontend spawns Python as a subprocess with stdio IPC. This is a **real architecture change** — not a drop-in addition. DSP code in `src/switchedonvoice/audio/` is written to be subprocess-portable (no Qt imports), but the `AudioCapture` process model does not transfer.
