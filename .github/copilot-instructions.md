# SwitchedOnVoice — Copilot Instructions

Real-time voice feminization training app: microphone → DSP analysis → PySide6 UI.

## Commands

```bash
# Install (requires Python 3.11+)
uv pip install -e ".[dev]"

# Run
python run.py

# Test (full suite)
pytest

# Single test file
pytest tests/audio/test_pitch.py

# Single test by name
pytest tests/audio/test_pitch.py::test_estimate_f0_returns_none_for_silence

# Lint
ruff check src tests

# Type check
mypy src

# Coverage
pytest --cov=switchedonvoice --cov-report=term-missing
```

## Architecture

Three-thread pipeline:

```
sounddevice callback  →  deque (lock-free)
analysis thread       →  reads deque, runs DSP (~30 Hz), posts AnalysisResult to queue.Queue
Qt main thread        →  QTimer at 33 ms polls queue, updates UI widgets
```

**Key rule:** The sounddevice callback does *nothing* except `deque.append()`. All DSP runs in the analysis thread.

Layer structure (import direction inward only):

```
ui/          →  audio/, storage/, gamification/, health
storage/     →  db.py (SQLite)
gamification →  (pure logic, no I/O)
health       →  (pure logic, no I/O)
audio/       →  (DSP, no Qt)
```

### Audio pipeline (`src/switchedonvoice/audio/`)

- **capture.py** — `AudioCapture` owns the sounddevice stream, analysis thread, and `results` queue. Produces `AnalysisResult` dataclass (f0, formants, cpp, is_voiced, spectrum, raw_audio).
- **voice_detector.py** → gates all analysis; DSP runs only when voiced
- **pitch.py** → DIO + stonemask (pyworld). Returns `median` of voiced frames — **not** `voiced[-1]`. DIO has a ~20 Hz boundary error on the last 1–3 frames; median eliminates it.
- **formants.py** → LPC order **14** at 16 kHz after downsampling. Pre-emphasis (`α=0.97`) is mandatory before `librosa.lpc` — without it, /u/ roots land outside the unit circle and are discarded. LPC order is set by `LPC_ORDER` constant; do not change without re-running Spike 2.
- **cpp.py** → Cepstral Peak Prominence (breathiness proxy)
- **spectrum.py** → FFT spectrum for display

### Storage (`src/switchedonvoice/storage/`)

SQLite at `~/.switchedonvoice/data.db`. All functions open and close their own connection; no long-lived connections.

- **db.py** — `init_db()` + `get_connection()`. Migrations use `PRAGMA user_version`; add `if version < N` blocks (not `elif` — the version is read once at entry so each block must be an independent `if`), never reorder.
- **sessions.py** — CRUD + `get_streak()` + `get_history_stats()`. Each session is created at app start with `create_session()`, closed with `close_session()` on window close, then milestones are back-patched with `update_session_milestones()`.
- **settings.py** — `Settings` dataclass persisted as JSON at `~/.switchedonvoice/settings.json`. `save_settings()` writes atomically (tempfile + `os.replace`).

### Milestone evaluation (`src/switchedonvoice/gamification/milestones.py`)

Pure function `evaluate_milestones(session, history) → set[MilestoneID]`. Milestones are earned once only; `MilestoneID` string values are persisted in `milestone_flags_json` — **do not rename enum values** without a DB migration.

**Close-session ordering in `MainWindow.closeEvent()`:**
1. `close_session()` first (persists current session)
2. `get_history_stats()` after (so current session is included)
3. `evaluate_milestones()` then `update_session_milestones()`

### UI (`src/switchedonvoice/ui/`)

All widgets receive `AnalysisResult` via `update_result()` called from `MainWindow._tick()`. Widgets must not do blocking I/O. `ProgressPanel` and `SettingsPanel` have their own DB/settings paths and are self-contained.

## Key Conventions

- **`from __future__ import annotations`** at the top of every module — required for PEP 604 union syntax (`X | Y`) on Python 3.11.
- **structlog** for logging in `audio/` (structured, key-value args). `logging` (stdlib) used in `ui/` modules. Use `_log = structlog.get_logger(__name__)` or `_logger = logging.getLogger(__name__)`.
- **No magic numbers** in DSP code. Constants like `_BUFFER_DURATION_S`, `LPC_ORDER`, `_FRAME_DECIMATE_RATE` are named and live at module top-level.
- **Qt tests** use `pytest-qt`. The `conftest.py` fixture auto-calls `widget.show()` so visibility can be tested. Use `QT_QPA_PLATFORM=offscreen` for headless runs.
- **Frame decimation:** analysis runs at ~30 Hz; only every 5th frame (`_FRAME_DECIMATE_RATE = 5`) is stored to the DB (~6 Hz). Don't store every frame.
- **`queue.Full` is silently dropped** in `AudioCapture._analysis_loop` — this is intentional, not a bug. The UI being behind is recoverable; blocking the analysis thread is not.
- **Spikes** in `spikes/` are standalone scripts used for empirical validation. `SPIKE_NOTES.md` records decisions (LPC order, pre-emphasis, F0 estimator choice) that must not be silently revisited.
- User data and settings live in `~/.switchedonvoice/`. The app creates this directory on first run.
