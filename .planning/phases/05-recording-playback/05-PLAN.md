---
phase: 05-recording-playback
plan: 01
type: execute
waves: 3
depends_on:
  - Phase 4 complete
files_modified:
  - pyproject.toml
  - src/switchedonvoice/storage/settings.py
  - src/switchedonvoice/ui/settings_panel.py
  - src/switchedonvoice/audio/capture.py
  - src/switchedonvoice/recordings/session_recorder.py
  - src/switchedonvoice/recordings/library.py
  - src/switchedonvoice/recordings/playback_controller.py
  - src/switchedonvoice/ui/recording_history_widget.py
  - src/switchedonvoice/ui/recording_waveform_thumbnail.py
  - src/switchedonvoice/ui/reading_panel.py
  - tests/storage/test_settings.py
  - tests/audio/test_capture.py
  - tests/recordings/test_session_recorder.py
  - tests/recordings/test_recording_library.py
  - tests/recordings/test_playback_controller.py
  - tests/ui/test_recording_history_widget.py
  - tests/ui/test_reading_panel.py
  - tests/ui/test_settings_panel.py
autonomous: true
requirements:
  - REQ-R04
  - REQ-NF02
must_haves:
  truths:
    - "record_by_default persists in Settings and seeds the per-session record prompt"
    - "Completed reading attempts save WAV files under recordings/<book_slug>/<passage_slug>/<timestamp>.wav"
    - "Recording history lists all recordings for the current passage in ascending date order"
    - "Playback controller allows only one active recording at a time"
    - "Waveform thumbnails load off-thread and do not block widget construction"
    - "Storage management shows accurate totals and deletes only the targeted files"
  artifacts:
    - path: "src/switchedonvoice/recordings/session_recorder.py"
      provides: "WAV recording writer around non-overlapping audio chunks"
    - path: "src/switchedonvoice/ui/recording_history_widget.py"
      provides: "Per-passage recording timeline"
    - path: "tests/recordings/test_recording_library.py"
      provides: "Storage estimation and deletion coverage"
  key_links:
    - from: "ReadingPanel"
      to: "SessionRecorder"
      via: "start/stop recording around a reading attempt"
    - from: "RecordingHistoryWidget"
      to: "PlaybackController"
      via: "play/stop UI state"
---

<objective>
Add opt-in reading-session recording, playback history per passage, static
waveform thumbnails, and storage-management controls without breaking the
existing low-latency capture pipeline.
</objective>

<wave_plan>
## Wave Breakdown

### Wave 1 — infrastructure (parallel)
1. Add the missing audio file dependency and settings/prompt state.
2. Add a safe recording audio tap + session recorder.
3. Build the recording library for listing, sizing, and deleting files.

### Wave 2 — playback/history UI (parallel)
4. Build the playback controller/state machine.
5. Build the history timeline widget and asynchronous waveform thumbnails.

### Wave 3 — Reading/Settings integration + verification
6. Integrate opt-in prompts and recorder lifecycle into Reading Mode.
7. Add Settings storage-management controls and finish end-to-end tests.
</wave_plan>

<tasks>
## Tasks

### Task 1 (Wave 1): Dependency and settings groundwork

**Description:** Add the missing runtime dependency for WAV I/O and persist
the global recording default in the settings model + settings UI.

**Files to create/modify**
- Modify: `pyproject.toml`
- Modify: `src/switchedonvoice/storage/settings.py`
- Modify: `src/switchedonvoice/ui/settings_panel.py`
- Test: `tests/storage/test_settings.py`
- Test: `tests/ui/test_settings_panel.py`

**Acceptance criteria (runnable assertions)**
- `pyproject.toml` includes `soundfile` as a runtime dependency.
- `Settings(record_by_default=True)` round-trips through JSON unchanged.
- `SettingsPanel` exposes the toggle and saves it.
- The per-session prompt default reflects the saved global setting.

**Test strategy**
- `tests/storage/test_settings.py`
  - new boolean default + round-trip
- `tests/ui/test_settings_panel.py`
  - checkbox initial state from saved settings
  - save writes updated value

**Security / edge-case notes**
- Invalid/corrupt JSON should still fall back to `record_by_default=False`.
- Update dependency lock/install flow as part of implementation; tests should
  run against the real installed dependency.

### Task 2 (Wave 1): Non-overlapping audio tap and session recorder

**Description:** Extend the capture pipeline just enough to supply valid raw
audio chunks to a recorder, then write those chunks to timestamped WAV files.

**Files to create/modify**
- Modify: `src/switchedonvoice/audio/capture.py`
- Create: `src/switchedonvoice/recordings/session_recorder.py`
- Test: `tests/audio/test_capture.py`
- Test: `tests/recordings/test_session_recorder.py`

**Acceptance criteria (runnable assertions)**
- The recorder receives non-overlapping chunks; appending two consecutive
  chunks yields exactly their combined duration, not duplicated audio.
- Starting/stopping a recorder writes a valid mono 44.1 kHz 16-bit WAV file.
- The saved path matches:
  `recordings/<book_slug>/<passage_slug>/<YYYY-MM-DD_HH-MM>.wav`.
- Stopping without any captured audio does not leave a corrupt file behind.

**Test strategy**
- `tests/audio/test_capture.py`
  - capture exposes the new recording tap without breaking existing results
- `tests/recordings/test_session_recorder.py`
  - file naming/path assertions
  - WAV metadata assertions via `soundfile`
  - incomplete-session cleanup

**Security / edge-case notes**
- Keep the callback limited to copying into a queue/deque.
- Never allow slugs to escape the recordings root; normalise/validate path
  components before writing.

### Task 3 (Wave 1): Recording library and storage management backend

**Description:** Create the service layer that knows how to enumerate
recordings for a passage, total storage, per-book totals, and deletion
operations.

**Files to create/modify**
- Create: `src/switchedonvoice/recordings/library.py`
- Test: `tests/recordings/test_recording_library.py`

**Acceptance criteria (runnable assertions)**
- Listing a passage with three WAV files returns three entries sorted by date
  ascending.
- `get_storage_usage()` returns total bytes/MB and a per-book breakdown that
  matches the actual files on disk.
- `delete_book("alice-wonderland")` removes only files under that book.
- `delete_before(date)` removes only recordings strictly older than the
  cutoff.

**Test strategy**
- `tests/recordings/test_recording_library.py`
  - list ordering
  - size calculation
  - per-book deletion
  - cutoff-date deletion

**Security / edge-case notes**
- All delete APIs must resolve and verify paths under the recordings root
  before unlinking.
- Treat missing files during deletion as handled operational errors, not hard
  crashes.

### Task 4 (Wave 2): Playback controller/state machine

**Description:** Centralise play/stop behaviour so the UI cannot start two
recordings at once.

**Files to create/modify**
- Create: `src/switchedonvoice/recordings/playback_controller.py`
- Test: `tests/recordings/test_playback_controller.py`

**Acceptance criteria (runnable assertions)**
- Calling `play(path_a)` then `play(path_b)` stops A before B starts.
- Calling `stop()` from idle is safe.
- Controller state transitions are deterministic: idle -> playing -> idle,
  with an error state surfaced if file load fails.

**Test strategy**
- `tests/recordings/test_playback_controller.py`
  - play/stop sequence using mocked `sounddevice.play/stop`
  - one-active-recording guarantee
  - load failure handling

**Security / edge-case notes**
- Validate file existence before handing bytes to playback.
- Keep playback control out of row widgets; rows should delegate.

### Task 5 (Wave 2): Recording history widget and waveform thumbnails

**Description:** Build the scrollable per-passage history UI and load static
waveform previews in a worker/thread-safe way.

**Files to create/modify**
- Create: `src/switchedonvoice/ui/recording_history_widget.py`
- Create: `src/switchedonvoice/ui/recording_waveform_thumbnail.py`
- Test: `tests/ui/test_recording_history_widget.py`

**Acceptance criteria (runnable assertions)**
- Given three recordings, the widget renders three dated rows in ascending
  order.
- Each row exposes a play/stop control and duration text.
- Thumbnail loading returns quickly enough that widget construction does not
  block waiting for disk I/O.
- Thumbnail results are ignored safely if the widget switches to a different
  passage before the worker finishes.

**Test strategy**
- `tests/ui/test_recording_history_widget.py`
  - row ordering and labels
  - play/stop button state wiring
  - async thumbnail completion / stale-result ignore

**Security / edge-case notes**
- Never decode WAV content inside `paintEvent()`.
- Show a placeholder thumbnail if the file is missing or unreadable.

### Task 6 (Wave 3): Reading Mode recording lifecycle integration

**Description:** Prompt for recording, start/stop the recorder around a
reading attempt, and refresh history for the active passage.

**Files to create/modify**
- Modify: `src/switchedonvoice/ui/reading_panel.py`
- Modify: `tests/ui/test_reading_panel.py`

**Acceptance criteria (runnable assertions)**
- Starting a reading attempt prompts with the saved default preselected.
- Declining the prompt completes the attempt without creating a WAV file.
- Accepting the prompt and finishing the attempt creates exactly one WAV file
  in the expected passage path.
- Finishing the attempt refreshes the history list for the current passage.

**Test strategy**
- `tests/ui/test_reading_panel.py`
  - prompt default state
  - opt-out creates no file
  - opt-in creates correctly named file and refreshes history

**Security / edge-case notes**
- Stop recording on passage/tab/window exit to avoid dangling file handles.
- Ensure a cancelled or failed attempt does not increment history incorrectly.

### Task 7 (Wave 3): Settings storage-management panel and final verification

**Description:** Expose recording storage totals and destructive delete
controls in Settings, then prove the whole flow works.

**Files to create/modify**
- Modify: `src/switchedonvoice/ui/settings_panel.py`
- Modify: `tests/ui/test_settings_panel.py`
- Modify: `tests/recordings/test_recording_library.py`

**Acceptance criteria (runnable assertions)**
- Settings shows total recording storage in MB and per-book totals.
- “Delete recordings for this book” removes only the targeted book after
  confirmation.
- “Delete all before date” removes only recordings older than the chosen
  date after confirmation.
- Refreshing the panel after deletion shows updated totals.

**Test strategy**
- `tests/ui/test_settings_panel.py`
  - totals rendered
  - confirmation-gated delete actions
  - UI refresh after delete
- `tests/recordings/test_recording_library.py`
  - backend delete correctness

**Security / edge-case notes**
- Deletion must always be confirmation-gated in the UI.
- Library code must remain the single authority on which files are safe to
  remove.
</tasks>

<verification>
## Verification

```bash
cd /home/alice/git/switchedonvoice
uv pip install -e ".[dev]"
pytest tests/storage/test_settings.py tests/audio/test_capture.py tests/recordings/test_session_recorder.py tests/recordings/test_recording_library.py tests/recordings/test_playback_controller.py -q
pytest tests/ui/test_recording_history_widget.py tests/ui/test_reading_panel.py tests/ui/test_settings_panel.py -q
pytest -q
```
</verification>

<completion_criteria>
## Completion Criteria

Phase 5 is done only when all of the following are true:

- Recording opt-in works both globally (saved default) and per reading
  attempt (current choice).
- Completed opted-in attempts create valid WAV files in the required
  `book_slug/passage_slug/timestamp.wav` layout.
- Recording history shows all recordings for the current passage in order,
  each with a playable row and non-blocking waveform thumbnail.
- Only one recording can play at once.
- Settings shows correct storage totals and destructive delete controls remove
  exactly the intended files.
- The full test suite still passes.
</completion_criteria>
