# Phase 22: Melody Following Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the user browse a library of public-domain melodies, sing against a scrolling target display, and receive persisted pitch/timing/vibrato results that award XP.

**Architecture:** Introduce a singing-content layer that loads validated melody assets and converts them into prepared note bars for a Qt practice widget, then store detailed attempt data through a generic singing repository while mirroring summary scores into `ArcadeRepository` and `CurriculumService`. `MainWindow` continues to own live `AnalysisResult` delivery; melody widgets only consume already-processed frames on the Qt thread.

**Tech Stack:** Python 3.11, PySide6/QPainter, JSON content assets, SQLite, existing `ArcadeRepository`, existing `CurriculumService`, pytest, pytest-qt

---

## File map

**Create:**
- `src/switchedonvoice/content/melodies/library.json`
- `src/switchedonvoice/singing/melody_library.py`
- `src/switchedonvoice/singing/scoring.py`
- `src/switchedonvoice/storage/singing.py`
- `src/switchedonvoice/ui/melody_browser_widget.py`
- `src/switchedonvoice/ui/melody_timeline_widget.py`
- `src/switchedonvoice/ui/melody_practice_panel.py`
- `src/switchedonvoice/ui/melody_results_dialog.py`
- `src/switchedonvoice/ui/singing_panel.py`
- `tests/singing/test_melody_library.py`
- `tests/singing/test_scoring.py`
- `tests/storage/test_singing_repository.py`
- `tests/ui/test_melody_browser_widget.py`
- `tests/ui/test_melody_timeline_widget.py`
- `tests/ui/test_singing_panel.py`

**Modify:**
- `src/switchedonvoice/storage/db.py`
- `src/switchedonvoice/ui/main_window.py`
- `src/switchedonvoice/ui/progress_panel.py`
- `tests/storage/test_db.py`

**Why this split:**
- Asset loading, scoring math, persistence, and rendering all stay separate.
- `singing_panel.py` (top-level singing tab) avoids bloating the existing
  `exercise_panel.py` with unrelated melody-browser logic.
- The generic `storage/singing.py` repository is reusable by Phase 23 exercises.

## Chunk 1: Content assets and pure scoring logic

### Task 1: Create the public-domain melody library and schema loader

**Files:**
- Create: `src/switchedonvoice/content/melodies/library.json`
- Create: `src/switchedonvoice/singing/melody_library.py`
- Test: `tests/singing/test_melody_library.py`

- [ ] **Step 1: Write failing asset/schema tests first**

Create `tests/singing/test_melody_library.py`:

```python
def test_load_melody_library_returns_at_least_ten_public_domain_songs() -> None:
    songs = load_melody_library()
    assert len(songs) >= 10
    assert all(song.source for song in songs)


def test_each_song_note_schema_has_required_fields() -> None:
    songs = load_melody_library()
    first_note = songs[0].notes[0]
    assert first_note.note_name
    assert first_note.start_time_ms >= 0
    assert first_note.duration_ms > 0
    assert first_note.frequency_hz > 0
```

- [ ] **Step 2: Run the loader tests to prove they fail**

Run: `pytest tests/singing/test_melody_library.py -q`

Expected: FAIL with `ModuleNotFoundError` and/or missing asset file errors.

- [ ] **Step 3: Implement the asset file and loader**

Populate `src/switchedonvoice/content/melodies/library.json` with at least 12
traditional/public-domain tunes. Every melody entry must include:
- `slug`
- `title`
- `source`
- `difficulty`
- `range_min_hz`
- `range_max_hz`
- `notes[]`

Create `src/switchedonvoice/singing/melody_library.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
import json

@dataclass(frozen=True)
class MelodyNote:
    note_name: str
    start_time_ms: int
    duration_ms: int
    frequency_hz: float

@dataclass(frozen=True)
class MelodySong:
    slug: str
    title: str
    source: str
    difficulty: str
    range_min_hz: float
    range_max_hz: float
    notes: tuple[MelodyNote, ...]
```

Loader rules:
- raise `ValueError` on malformed songs
- sort notes by `start_time_ms`
- keep one `_LIBRARY_RESOURCE = "library.json"` constant
- include a helper `validate_song_schema(raw_song: dict[str, object]) -> None`

- [ ] **Step 4: Re-run the library tests**

Run: `pytest tests/singing/test_melody_library.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/content/melodies/library.json src/switchedonvoice/singing/melody_library.py tests/singing/test_melody_library.py
git commit -m "feat: add public domain melody library"
```

### Task 2: Build pure note-bar preparation and scoring helpers

**Files:**
- Create: `src/switchedonvoice/singing/scoring.py`
- Test: `tests/singing/test_scoring.py`

- [ ] **Step 1: Add failing math tests**

Create `tests/singing/test_scoring.py`:

```python
def test_cents_error_is_zero_at_target_pitch() -> None:
    assert cents_error(target_hz=440.0, observed_hz=440.0) == pytest.approx(0.0)


def test_cents_error_matches_octave_offset() -> None:
    assert cents_error(target_hz=440.0, observed_hz=880.0) == pytest.approx(1200.0)


def test_detect_vibrato_finds_five_hz_modulation() -> None:
    sample_rate_hz = 30.0
    times = np.arange(0.0, 2.0, 1.0 / sample_rate_hz)
    waveform = 440.0 + 12.0 * np.sin(2.0 * np.pi * 5.5 * times)
    assert detect_vibrato(waveform.tolist(), sample_rate_hz=sample_rate_hz) is True


def test_prepare_note_bars_marks_current_target_green_when_hit() -> None:
    song = make_song()
    bars = prepare_note_bars(song=song, now_ms=500, viewport_ms=3000, live_f0_hz=261.63)
    assert any(bar.is_active and bar.display_color == "green" for bar in bars)
```

- [ ] **Step 2: Run the failing scoring tests**

Run: `pytest tests/singing/test_scoring.py -q`

Expected: FAIL because the helpers do not exist yet.

- [ ] **Step 3: Implement the pure scoring module**

Create `src/switchedonvoice/singing/scoring.py` with:
- `PreparedNoteBar` dataclass
- `ScoredSegment` dataclass
- `cents_error()`
- `score_pitch_hit()`
- `score_onset_delta_ms()`
- `detect_vibrato()`
- `prepare_note_bars()`

Suggested seam:

```python
_OCTAVE_CENTS = 1200.0
_ACTIVE_HIT_TOLERANCE_CENTS = 35.0
_VIBRATO_MIN_RATE_HZ = 5.0
_VIBRATO_MAX_RATE_HZ = 8.0
_VIBRATO_MIN_DEPTH_CENTS = 20.0
```

Keep colour decisions centralized in one helper:
- green = within hit tolerance
- yellow = near miss
- red = off target
- neutral/grey = not yet active

- [ ] **Step 4: Re-run the pure scoring tests**

Run: `pytest tests/singing/test_scoring.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/singing/scoring.py tests/singing/test_scoring.py
git commit -m "feat: add melody scoring helpers"
```

## Chunk 2: Persistence and Qt practice flow

### Task 3: Add singing-attempt persistence and XP handoff

**Files:**
- Modify: `src/switchedonvoice/storage/db.py`
- Create: `src/switchedonvoice/storage/singing.py`
- Modify: `tests/storage/test_db.py`
- Create: `tests/storage/test_singing_repository.py`

- [ ] **Step 1: Write failing repository tests first**

Add migration coverage in `tests/storage/test_db.py` and create repository tests:

```python
def test_init_creates_singing_attempt_tables(db_path: Path) -> None:
    init_db(db_path)
    with sqlite3.connect(db_path) as con:
        tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "singing_attempts" in tables
    assert "singing_segment_scores" in tables


def test_save_attempt_persists_segments_and_summary(db_path: Path) -> None:
    repository = SingingRepository(db_path)
    attempt_id = repository.save_attempt(make_attempt_summary(), make_segments())
    loaded = repository.get_attempt(attempt_id)
    assert loaded.summary.content_slug == "twinkle-twinkle"
    assert len(loaded.segments) == 8
```

- [ ] **Step 2: Run the storage tests to confirm failure**

Run: `pytest tests/storage/test_db.py tests/storage/test_singing_repository.py -q`

Expected: FAIL because the migration and repository do not exist yet.

- [ ] **Step 3: Implement the migration and repository**

In `src/switchedonvoice/storage/db.py`:
- bump schema version
- add `_SCHEMA_V<N>` with both singing tables and indexes
- migrate with `if version < N:` (not `elif`)

In `src/switchedonvoice/storage/singing.py`:
- follow the per-method `get_connection()` pattern
- use `structlog`
- add `save_attempt()`, `get_attempt()`, `list_recent_attempts()`
- after saving the singing attempt, call `ArcadeRepository.record_score()` (or
  the equivalent Phase 11 API) with a namespaced score key like
  `melody/twinkle-twinkle`
- then call `CurriculumService.award_xp(profile_id, source_type="melody", source_id=content_slug, amount=earned_xp)`

Keep persistence ordering explicit in the repository/service boundary:

```python
attempt_id = singing_repository.save_attempt(summary, segments)
arcade_repository.record_score(profile_id=profile_id, game_id=f"melody/{summary.content_slug}", score=summary.overall_score)
curriculum_service.award_xp(profile_id=profile_id, source_type="melody", source_id=summary.content_slug, amount=summary.earned_xp)
```

- [ ] **Step 4: Re-run the storage tests**

Run: `pytest tests/storage/test_db.py tests/storage/test_singing_repository.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/storage/db.py src/switchedonvoice/storage/singing.py tests/storage/test_db.py tests/storage/test_singing_repository.py
git commit -m "feat: persist melody attempts"
```

### Task 4: Build the browser, timeline, results screen, and top-level singing tab

**Files:**
- Create: `src/switchedonvoice/ui/melody_browser_widget.py`
- Create: `src/switchedonvoice/ui/melody_timeline_widget.py`
- Create: `src/switchedonvoice/ui/melody_practice_panel.py`
- Create: `src/switchedonvoice/ui/melody_results_dialog.py`
- Create: `src/switchedonvoice/ui/singing_panel.py`
- Modify: `src/switchedonvoice/ui/main_window.py`
- Modify: `src/switchedonvoice/ui/progress_panel.py`
- Test: `tests/ui/test_melody_browser_widget.py`
- Test: `tests/ui/test_melody_timeline_widget.py`
- Test: `tests/ui/test_singing_panel.py`

- [ ] **Step 1: Add failing pytest-qt coverage**

Create focused UI tests:

```python
def test_browser_lists_at_least_ten_songs(qtbot) -> None:
    widget = MelodyBrowserWidget(load_melody_library())
    qtbot.addWidget(widget)
    assert widget.song_count() >= 10


def test_selecting_song_launches_practice_panel(qtbot) -> None:
    panel = SingingPanel()
    qtbot.addWidget(panel)
    panel.select_song("twinkle-twinkle")
    assert panel.active_song_slug() == "twinkle-twinkle"


def test_timeline_marks_off_pitch_note_red(qtbot) -> None:
    widget = MelodyTimelineWidget()
    qtbot.addWidget(widget)
    widget.load_song(make_song())
    widget.update_live_pitch(now_ms=500, live_f0_hz=220.0)
    assert widget.active_bar_color_name() == "red"
```

- [ ] **Step 2: Run the failing UI tests**

Run: `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_melody_browser_widget.py tests/ui/test_melody_timeline_widget.py tests/ui/test_singing_panel.py -q`

Expected: FAIL with missing widgets/APIs.

- [ ] **Step 3: Implement the minimal Qt flow**

Build the widgets with these responsibilities:
- `MelodyBrowserWidget` — list of songs with title/range/difficulty
- `MelodyTimelineWidget` — `load_song()` + `update_live_pitch()` + `paintEvent()`
- `MelodyPracticePanel` — owns countdown/start/finish state and per-note scoring
- `MelodyResultsDialog` — shows pitch bar chart, timing score, vibrato count, XP earned
- `SingingPanel` — stacked browse/practice shell used by `MainWindow`

`MainWindow` changes:
- add `self._singing_panel = SingingPanel(...)`
- add a `Singing` tab beside `Exercises`
- during `_tick()`, forward frames with `self._singing_panel.on_audio_frame(result)`
  when a melody practice session is active

`ProgressPanel` change:
- refresh XP Breakdown after melody completion so `melody/<slug>` entries appear
  immediately without an app restart

- [ ] **Step 4: Re-run the focused UI tests, then the end-to-end slice**

Run:
- `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_melody_browser_widget.py tests/ui/test_melody_timeline_widget.py tests/ui/test_singing_panel.py -q`
- `QT_QPA_PLATFORM=offscreen pytest tests/singing/test_melody_library.py tests/singing/test_scoring.py tests/storage/test_singing_repository.py tests/ui/test_singing_panel.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/ui/melody_browser_widget.py src/switchedonvoice/ui/melody_timeline_widget.py src/switchedonvoice/ui/melody_practice_panel.py src/switchedonvoice/ui/melody_results_dialog.py src/switchedonvoice/ui/singing_panel.py src/switchedonvoice/ui/main_window.py src/switchedonvoice/ui/progress_panel.py tests/ui/test_melody_browser_widget.py tests/ui/test_melody_timeline_widget.py tests/ui/test_singing_panel.py
git commit -m "feat: add melody following ui"
```

## Final verification

- [ ] Run: `pytest tests/singing/test_melody_library.py tests/singing/test_scoring.py tests/storage/test_singing_repository.py -q`
- [ ] Run: `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_melody_browser_widget.py tests/ui/test_melody_timeline_widget.py tests/ui/test_singing_panel.py -q`
- [ ] Run: `ruff check src tests`
- [ ] Run: `mypy src`
- [ ] Manual smoke test: start `python run.py`, open the Singing tab, confirm at least 10 melodies render in the browser, start one song, sing near and far from the target band to verify green/red feedback, finish the melody, and confirm XP Breakdown refreshes.

Expected final state:
- Melody browser lists at least 10 public-domain songs.
- Live note bars respond smoothly to pitch accuracy.
- Results screen shows note-level pitch accuracy, timing score, vibrato count, and XP.
- Melody completion persists history and appears in XP Breakdown.

Plan complete and saved to `.planning/phases/22-melody-following/22-PLAN.md`. Ready to execute?
