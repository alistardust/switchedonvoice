# Phase 24: Milestone Recording & Comparison Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the user record the same standard passage at major milestones and compare milestone recordings over time through waveform overlays, trend summaries, and back-to-back playback.

**Architecture:** Add a dedicated `milestone_voice` domain package for passage assets, trigger logic, comparison assembly, and recording orchestration. Keep SQLite persistence in `storage/`, use an explicit recording adapter at the audio boundary, and keep waveform/trend/playback preparation outside widgets so the UI consumes immutable view models only.

**Tech Stack:** Python 3.11+, PySide6, sqlite3, pathlib, numpy, wave/soundfile-compatible WAV handling, pytest, pytest-qt, uv

---

## File Map

### New modules
- `src/switchedonvoice/milestone_voice/__init__.py` — package exports
- `src/switchedonvoice/milestone_voice/models.py` — dataclasses/protocols for passages, prompts, recordings, comparison view models
- `src/switchedonvoice/milestone_voice/passages.py` — packaged milestone passage loader
- `src/switchedonvoice/milestone_voice/logic.py` — pure trigger selection, prompt dedupe, delta/trend helpers
- `src/switchedonvoice/milestone_voice/comparison.py` — waveform envelope normalization and trend assembly
- `src/switchedonvoice/milestone_voice/service.py` — orchestration service wrapping storage + recording backend
- `src/switchedonvoice/milestone_voice/assets/__init__.py` — package marker for `importlib.resources`
- `src/switchedonvoice/milestone_voice/assets/milestone_passages.json` — curated 3–5 standard passages
- `src/switchedonvoice/audio/recording.py` — Phase-5-compatible WAV recording adapter that satisfies the milestone service protocol if no reusable recorder already exists
- `src/switchedonvoice/storage/milestone_recordings.py` — repository for prompts and completed recordings
- `src/switchedonvoice/ui/milestone_prompt_banner.py` — non-intrusive prompt widget
- `src/switchedonvoice/ui/milestone_comparison_panel.py` — recording selectors, waveform overlay, trend chart, playback controls

### Modified modules
- `src/switchedonvoice/storage/db.py` — add DDL + next schema migration for milestone tables
- `src/switchedonvoice/ui/progress_panel.py` — host prompt banner and comparison entry point
- `src/switchedonvoice/ui/main_window.py` — register qualifying milestone events after milestone evaluation and refresh comparison data
- `src/switchedonvoice/ui/waveform_widget.py` — only if dual-series overlay support cannot stay local to the comparison panel
- `tests/storage/test_db.py` — bump schema-version assertion

### Tests
- `tests/milestone_voice/__init__.py`
- `tests/milestone_voice/conftest.py`
- `tests/milestone_voice/test_passages_and_logic.py`
- `tests/milestone_voice/test_service.py`
- `tests/milestone_voice/test_comparison.py`
- `tests/storage/conftest.py`
- `tests/storage/test_milestone_recordings.py`
- `tests/ui/test_milestone_prompt_banner.py`
- `tests/ui/test_milestone_comparison_panel.py`
- `tests/audio/test_recording.py`

## Chunk 1: Domain and persistence foundation

### Task 1: Create the packaged milestone passage catalog and pure trigger logic

**Files:**
- Create: `src/switchedonvoice/milestone_voice/__init__.py`
- Create: `src/switchedonvoice/milestone_voice/models.py`
- Create: `src/switchedonvoice/milestone_voice/passages.py`
- Create: `src/switchedonvoice/milestone_voice/logic.py`
- Create: `src/switchedonvoice/milestone_voice/assets/__init__.py`
- Create: `src/switchedonvoice/milestone_voice/assets/milestone_passages.json`
- Create: `tests/milestone_voice/__init__.py`
- Test: `tests/milestone_voice/test_passages_and_logic.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

from switchedonvoice.milestone_voice.logic import build_prompt_candidates
from switchedonvoice.milestone_voice.passages import load_milestone_passages


def test_load_milestone_passages_returns_provisional_stable_slugs() -> None:
    passages = load_milestone_passages()

    # Provisional list until Context Open Question 1 is signed off.
    assert [passage.slug for passage in passages] == [
        "rainbow-standard",
        "grandfather-standard",
        "north-wind-standard",
        "comma-gets-a-cure-standard",
    ]
    assert all(passage.text for passage in passages)


def test_build_prompt_candidates_only_returns_new_major_milestones() -> None:
    pending_keys = {"session-count-10"}

    prompt_candidates = build_prompt_candidates(
        milestone_events=["session-count-10", "streak-30", "skill-tier-1"],
        existing_prompt_keys=pending_keys,
        default_passage_slug="rainbow-standard",
    )

    assert [candidate.milestone_key for candidate in prompt_candidates] == [
        "streak-30",
        "skill-tier-1",
    ]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/milestone_voice/test_passages_and_logic.py -q`

Expected: `ModuleNotFoundError: No module named 'switchedonvoice.milestone_voice'`

- [ ] **Step 3: Write the minimal implementation**

Create shared dataclasses in `models.py` first so both storage and service code import the same types.

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MilestonePassage:
    slug: str
    title: str
    text: str
    rationale: str


@dataclass(frozen=True)
class PromptCandidate:
    milestone_key: str
    suggested_passage_slug: str
```

```python
from __future__ import annotations

import json
from importlib.resources import files

from switchedonvoice.milestone_voice.models import MilestonePassage


def load_milestone_passages() -> list[MilestonePassage]:
    asset_path = files("switchedonvoice.milestone_voice.assets") / "milestone_passages.json"
    raw_items = json.loads(asset_path.read_text(encoding="utf-8"))
    return [MilestonePassage(**item) for item in raw_items]
```

```python
from __future__ import annotations

from switchedonvoice.milestone_voice.models import PromptCandidate


def build_prompt_candidates(
    milestone_events: list[str],
    existing_prompt_keys: set[str],
    default_passage_slug: str,
) -> list[PromptCandidate]:
    return [
        PromptCandidate(milestone_key=event_key, suggested_passage_slug=default_passage_slug)
        for event_key in milestone_events
        if event_key not in existing_prompt_keys
    ]
```

- [ ] **Step 4: Run the tests and verify packaged assets resolve**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/milestone_voice/test_passages_and_logic.py -q && uv run python -c "from importlib.resources import files; print((files('switchedonvoice.milestone_voice.assets') / 'milestone_passages.json').name)"`

Expected: `2 passed` and then `milestone_passages.json` printed successfully.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/milestone_voice/__init__.py src/switchedonvoice/milestone_voice/models.py src/switchedonvoice/milestone_voice/passages.py src/switchedonvoice/milestone_voice/logic.py src/switchedonvoice/milestone_voice/assets/__init__.py src/switchedonvoice/milestone_voice/assets/milestone_passages.json tests/milestone_voice/__init__.py tests/milestone_voice/test_passages_and_logic.py
git commit -m "feat: add milestone passage catalog" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 2: Add SQLite persistence for milestone prompts and recordings

**Files:**
- Modify: `src/switchedonvoice/storage/db.py`
- Create: `src/switchedonvoice/storage/milestone_recordings.py`
- Create: `tests/storage/conftest.py`
- Modify: `tests/storage/test_db.py`
- Test: `tests/storage/test_milestone_recordings.py`

- [ ] **Step 1: Write the failing tests and shared fixtures**

```python
from __future__ import annotations

import wave
from pathlib import Path

import pytest


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture()
def sample_wav_path(tmp_path: Path) -> Path:
    wav_path = tmp_path / "sample.wav"
    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * 1600)
    return wav_path
```

```python
from __future__ import annotations

from switchedonvoice.storage.db import init_db
from switchedonvoice.storage.milestone_recordings import MilestoneRecordingRepository


def test_init_db_creates_milestone_tables(db_path) -> None:
    init_db(db_path)
    repository = MilestoneRecordingRepository(db_path)

    prompt = repository.create_prompt(
        milestone_key="session-count-10",
        milestone_label="10 sessions completed",
        suggested_passage_slug="rainbow-standard",
        qualifying_session_id=10,
    )

    assert prompt.id > 0


def test_save_recording_persists_snapshot_and_wav_path(db_path, sample_wav_path) -> None:
    init_db(db_path)
    repository = MilestoneRecordingRepository(db_path)
    prompt = repository.create_prompt(
        milestone_key="streak-30",
        milestone_label="30-day streak",
        suggested_passage_slug="rainbow-standard",
        qualifying_session_id=30,
    )

    recording = repository.save_recording(
        prompt_id=prompt.id,
        milestone_key="streak-30",
        passage_slug="rainbow-standard",
        wav_path=sample_wav_path,
        duration_seconds=4.2,
        f0_median_hz=198.5,
        f1_hz=650.0,
        f2_hz=1710.0,
        cpp_db=13.2,
    )

    assert recording.snapshot.f0_median_hz == 198.5
    assert recording.wav_path == sample_wav_path
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/storage/test_milestone_recordings.py tests/storage/test_db.py::test_schema_version_is_set -q`

Expected: FAIL because the repository module and milestone tables do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

1. Add `CREATE TABLE IF NOT EXISTS milestone_recording_prompts ...` and `CREATE TABLE IF NOT EXISTS milestone_recordings ...` to `_SCHEMA` in `src/switchedonvoice/storage/db.py`.
2. Read the current `_CURRENT_SCHEMA_VERSION` value and assign `NEXT_SCHEMA_VERSION` as the next literal integer. If the repository still matches today’s state, that literal is `2`.
3. Bump `_CURRENT_SCHEMA_VERSION` to `NEXT_SCHEMA_VERSION`.
4. In `_migrate()`, keep every existing migration block as a hard-coded literal; update any older `PRAGMA user_version = _CURRENT_SCHEMA_VERSION` line to a literal for its own version, then append a new independent `if version < NEXT_SCHEMA_VERSION:` block for the milestone schema.
5. Update `tests/storage/test_db.py::test_schema_version_is_set` to assert `NEXT_SCHEMA_VERSION`.

```python
if version < 1:
    con.execute("PRAGMA user_version = 1")
if version < NEXT_SCHEMA_VERSION:
    con.execute(f"PRAGMA user_version = {NEXT_SCHEMA_VERSION}")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/storage/test_milestone_recordings.py tests/storage/test_db.py -q`

Expected: PASS, with milestone prompt creation, recording round-trip, and schema-version coverage updated.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/storage/db.py src/switchedonvoice/storage/milestone_recordings.py tests/storage/conftest.py tests/storage/test_milestone_recordings.py tests/storage/test_db.py
git commit -m "feat: add milestone recording storage" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 3: Add the recording adapter seam and orchestration service

**Files:**
- Create: `src/switchedonvoice/audio/recording.py`
- Create: `src/switchedonvoice/milestone_voice/service.py`
- Create: `tests/milestone_voice/conftest.py`
- Test: `tests/audio/test_recording.py`
- Test: `tests/milestone_voice/test_service.py`

- [ ] **Step 1: Write the failing tests and fixtures**

```python
from __future__ import annotations

from pathlib import Path

import pytest

from switchedonvoice.milestone_voice.passages import load_milestone_passages
from switchedonvoice.storage.milestone_recordings import MilestoneRecordingRepository


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "milestone.db"


@pytest.fixture()
def passage_catalog():
    return load_milestone_passages()


@pytest.fixture()
def repository(db_path):
    return MilestoneRecordingRepository(db_path)


@pytest.fixture()
def recordings_dir(tmp_path: Path) -> Path:
    path = tmp_path / "recordings"
    path.mkdir()
    return path
```

```python
from __future__ import annotations

from pathlib import Path

from switchedonvoice.audio.recording import AudioMilestoneRecorder
from switchedonvoice.milestone_voice.models import RecordedMilestoneClip
from switchedonvoice.milestone_voice.service import MilestoneRecordingService


class FakeCaptureBackend:
    def record_standard_passage(self, passage_text: str, output_path: Path) -> RecordedMilestoneClip:
        return RecordedMilestoneClip(
            wav_path=output_path,
            duration_seconds=3.5,
            f0_median_hz=205.0,
            f1_hz=620.0,
            f2_hz=1760.0,
            cpp_db=12.4,
        )


def test_audio_milestone_recorder_returns_clip_metadata(tmp_path: Path) -> None:
    output_path = tmp_path / "clip.wav"
    recorder = AudioMilestoneRecorder(sample_rate_hz=16000, channels=1)

    clip = recorder.record_standard_passage("hello world", output_path)

    assert clip.wav_path == output_path
    assert clip.duration_seconds > 0


def test_register_milestone_event_creates_single_prompt(repository, passage_catalog, recordings_dir) -> None:
    service = MilestoneRecordingService(
        repository=repository,
        capture_backend=FakeCaptureBackend(),
        passage_catalog=passage_catalog,
        recordings_dir=recordings_dir,
    )

    service.register_milestone_event("session-count-10", "10 sessions completed", qualifying_session_id=10)
    service.register_milestone_event("session-count-10", "10 sessions completed", qualifying_session_id=10)

    prompts = repository.list_all_prompts()
    assert len(prompts) == 1


def test_complete_prompt_records_snapshot_and_marks_prompt_complete(repository, passage_catalog, recordings_dir) -> None:
    service = MilestoneRecordingService(
        repository=repository,
        capture_backend=FakeCaptureBackend(),
        passage_catalog=passage_catalog,
        recordings_dir=recordings_dir,
    )
    prompt = repository.create_prompt("streak-30", "30-day streak", "rainbow-standard", 30)

    recording = service.complete_prompt(prompt.id, passage_slug="rainbow-standard")

    assert recording.snapshot.cpp_db == 12.4
    assert repository.get_prompt(prompt.id).status == "completed"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/audio/test_recording.py tests/milestone_voice/test_service.py -q`

Expected: FAIL because the recording adapter and `MilestoneRecordingService` do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

1. In `models.py`, add a `MilestonePrompt` dataclass plus a `MilestoneCaptureBackend` protocol with `record_standard_passage(passage_text: str, output_path: Path) -> RecordedMilestoneClip`.
2. In `src/switchedonvoice/audio/recording.py`, either wrap the Phase 5 reusable recorder if it exists or implement the thin WAV-recording adapter there so the milestone service never talks directly to widgets.
3. Inject `recordings_dir: Path` into `MilestoneRecordingService.__init__`.
4. Deduplicate against **all** existing prompts/recordings, not only `pending` ones, so the repository’s uniqueness rules are respected without `IntegrityError`.

```python
class MilestoneRecordingService:
    def __init__(self, repository, capture_backend, passage_catalog, recordings_dir: Path) -> None:
        self._repository = repository
        self._capture_backend = capture_backend
        self._passages_by_slug = {passage.slug: passage for passage in passage_catalog}
        self._recordings_dir = recordings_dir
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/audio/test_recording.py tests/milestone_voice/test_service.py -q`

Expected: PASS, proving the adapter seam exists and service dedupe/completion work.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/audio/recording.py src/switchedonvoice/milestone_voice/models.py src/switchedonvoice/milestone_voice/service.py tests/audio/test_recording.py tests/milestone_voice/conftest.py tests/milestone_voice/test_service.py
git commit -m "feat: add milestone recording service" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

## Chunk 2: Comparison UI and playback flow

### Task 4: Build comparison/trend assembly and back-to-back playback sequencing

**Files:**
- Create: `src/switchedonvoice/milestone_voice/comparison.py`
- Modify: `src/switchedonvoice/milestone_voice/logic.py`
- Test: `tests/milestone_voice/test_comparison.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

from pathlib import Path

from switchedonvoice.milestone_voice.comparison import build_comparison_view_model
from switchedonvoice.milestone_voice.models import AcousticSnapshot, MilestoneRecording


def test_build_comparison_view_model_resamples_two_waveforms_and_sorts_trends(tmp_path: Path) -> None:
    import wave

    wav_a = tmp_path / "a.wav"
    wav_b = tmp_path / "b.wav"
    for wav_path, frame_count in ((wav_a, 1600), (wav_b, 2400)):
        with wave.open(str(wav_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            wav_file.writeframes(b"\x00\x00" * frame_count)
    recordings = [
        MilestoneRecording(
            id=1,
            milestone_key="session-count-10",
            passage_slug="rainbow-standard",
            recorded_at="2026-01-01T10:00:00+00:00",
            wav_path=wav_a,
            duration_seconds=4.0,
            snapshot=AcousticSnapshot(180.0, 640.0, 1700.0, 12.0),
        ),
        MilestoneRecording(
            id=2,
            milestone_key="streak-30",
            passage_slug="rainbow-standard",
            recorded_at="2026-02-01T10:00:00+00:00",
            wav_path=wav_b,
            duration_seconds=4.2,
            snapshot=AcousticSnapshot(210.0, 680.0, 1800.0, 14.0),
        ),
    ]

    view_model = build_comparison_view_model(
        recordings=recordings,
        first_recording_id=1,
        second_recording_id=2,
        waveform_points=256,
        playback_pause_seconds=0.75,
    )

    assert len(view_model.overlay.points_a) == 256
    assert len(view_model.overlay.points_b) == 256
    assert view_model.trends.dates == sorted(view_model.trends.dates)
    assert "F0" in view_model.delta_summary
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/milestone_voice/test_comparison.py -q`

Expected: FAIL because the comparison builder does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

1. Add named constants such as `_DEFAULT_WAVEFORM_POINTS` and `_DEFAULT_PLAYBACK_PAUSE_SECONDS` at module top.
2. Load both WAVs through the audio adapter/safe file path used elsewhere in the app.
3. Normalize each waveform into a fixed-size envelope so the overlay widget never performs file I/O.
4. Build a simple delta summary string from scalar snapshot differences.

```python
def build_delta_summary(first: MilestoneRecording, second: MilestoneRecording) -> str:
    f0_delta = _format_delta("F0", first.snapshot.f0_median_hz, second.snapshot.f0_median_hz, "Hz")
    cpp_delta = _format_delta("CPP", first.snapshot.cpp_db, second.snapshot.cpp_db, "dB")
    return f"{f0_delta} · {cpp_delta}"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/milestone_voice/test_comparison.py -q`

Expected: PASS with deterministic overlay/trend ordering.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/milestone_voice/comparison.py src/switchedonvoice/milestone_voice/logic.py tests/milestone_voice/test_comparison.py
git commit -m "feat: add milestone comparison data builder" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 5: Add the prompt banner, comparison panel, and milestone wiring in the UI

**Files:**
- Create: `src/switchedonvoice/ui/milestone_prompt_banner.py`
- Create: `src/switchedonvoice/ui/milestone_comparison_panel.py`
- Modify: `src/switchedonvoice/ui/progress_panel.py`
- Modify: `src/switchedonvoice/ui/main_window.py`
- Modify: `src/switchedonvoice/ui/waveform_widget.py` (only if overlay support cannot stay local)
- Test: `tests/ui/test_milestone_prompt_banner.py`
- Test: `tests/ui/test_milestone_comparison_panel.py`

- [ ] **Step 1: Write the failing UI tests**

```python
from __future__ import annotations


def test_prompt_banner_emits_record_and_dismiss_actions(qtbot) -> None:
    widget = MilestonePromptBanner(prompt=sample_prompt)
    qtbot.addWidget(widget)

    with qtbot.waitSignal(widget.record_requested):
        widget.record_button.click()


def test_comparison_panel_updates_overlay_and_delta_summary(qtbot) -> None:
    panel = MilestoneComparisonPanel()
    qtbot.addWidget(panel)

    panel.set_view_model(sample_view_model)

    assert panel.delta_summary_label.text() == sample_view_model.delta_summary
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /home/alice/git/switchedonvoice && QT_QPA_PLATFORM=offscreen uv run pytest tests/ui/test_milestone_prompt_banner.py tests/ui/test_milestone_comparison_panel.py -q`

Expected: FAIL because the widgets and wiring do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

1. Build `MilestonePromptBanner` as a slim widget with milestone copy plus `Record now` and `Dismiss` buttons.
2. Build `MilestoneComparisonPanel` with two recording selectors, a waveform overlay area, a simple trend chart widget, a delta summary label, and a `Play comparison` button.
3. In `MainWindow.closeEvent()`, immediately after `evaluate_milestones(...)` / `update_session_milestones(...)`, translate qualifying milestone results into `MilestoneRecordingService.register_milestone_event(...)` calls so prompts are persisted at the correct lifecycle point.
4. In `ProgressPanel.refresh()`, load pending prompts and completed recordings from the repository and feed the prompt banner/comparison panel.

```python
self._prompt_banner.record_requested.connect(self._start_milestone_recording)
self._prompt_banner.dismiss_requested.connect(self._dismiss_milestone_prompt)
self._comparison_panel.play_requested.connect(self._play_selected_comparison)
```

- [ ] **Step 4: Run the focused UI tests, then the full phase slice**

Run: `cd /home/alice/git/switchedonvoice && QT_QPA_PLATFORM=offscreen uv run pytest tests/ui/test_milestone_prompt_banner.py tests/ui/test_milestone_comparison_panel.py tests/milestone_voice tests/storage/test_milestone_recordings.py tests/audio/test_recording.py -q`

Expected: PASS, including prompt actions, comparison rendering, and storage/service coverage.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/ui/milestone_prompt_banner.py src/switchedonvoice/ui/milestone_comparison_panel.py src/switchedonvoice/ui/progress_panel.py src/switchedonvoice/ui/main_window.py tests/ui/test_milestone_prompt_banner.py tests/ui/test_milestone_comparison_panel.py
# Only if modified:
# git add src/switchedonvoice/ui/waveform_widget.py
git commit -m "feat: add milestone comparison ui" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 6: Final verification pass for Phase 24

**Files:**
- Verify only; no planned code changes in this task

- [ ] **Step 1: Run lint checks for touched modules**

Run: `cd /home/alice/git/switchedonvoice && uv run ruff check src/switchedonvoice/milestone_voice src/switchedonvoice/audio/recording.py src/switchedonvoice/storage/milestone_recordings.py src/switchedonvoice/ui/milestone_prompt_banner.py src/switchedonvoice/ui/milestone_comparison_panel.py tests/milestone_voice tests/audio/test_recording.py tests/ui/test_milestone_prompt_banner.py tests/ui/test_milestone_comparison_panel.py tests/storage/test_milestone_recordings.py`

Expected: `All checks passed!`

- [ ] **Step 2: Run type checking for new modules**

Run: `cd /home/alice/git/switchedonvoice && uv run mypy src/switchedonvoice/milestone_voice src/switchedonvoice/audio/recording.py src/switchedonvoice/storage/milestone_recordings.py src/switchedonvoice/ui/milestone_prompt_banner.py src/switchedonvoice/ui/milestone_comparison_panel.py`

Expected: `Success: no issues found`

- [ ] **Step 3: Run the full test suite**

Run: `cd /home/alice/git/switchedonvoice && QT_QPA_PLATFORM=offscreen uv run pytest -q`

Expected: PASS with the existing suite plus the new milestone tests.

- [ ] **Step 4: Smoke test manually**

Run: `cd /home/alice/git/switchedonvoice && uv run python run.py`

Expected: After reaching a qualifying milestone, the app shows a dismissible prompt, saves a milestone WAV plus snapshot when recorded, and the comparison panel can overlay any two saved milestone recordings.

- [ ] **Step 5: Commit any final polish**

```bash
git add -A
git commit -m "chore: final polish for milestone comparison" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

Plan complete and saved to `.planning/phases/24-milestone-comparison/24-PLAN.md`. Ready to execute?
