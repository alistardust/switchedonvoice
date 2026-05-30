---
phase: 04-acoustic-overlay
plan: 01
type: execute
waves: 3
depends_on:
  - Phase 3 complete
files_modified:
  - src/switchedonvoice/storage/db.py
  - src/switchedonvoice/storage/books.py
  - src/switchedonvoice/health.py
  - src/switchedonvoice/reading/feedback.py
  - src/switchedonvoice/ui/reading_panel.py
  - src/switchedonvoice/ui/session_summary_dialog.py
  - src/switchedonvoice/ui/progress_panel.py
  - src/switchedonvoice/ui/main_window.py
  - tests/storage/test_db.py
  - tests/content/test_books_repository.py
  - tests/reading/test_feedback.py
  - tests/ui/test_session_summary_dialog.py
  - tests/ui/test_reading_panel.py
  - tests/ui/test_progress_panel.py
  - tests/ui/test_main_window.py
autonomous: true
requirements:
  - REQ-R03
  - REQ-R05
must_haves:
  truths:
    - "Reading tab reuses MainWindow's shared AudioCapture and goes idle when inactive"
    - "Per-word mean F0 aggregation ignores unvoiced frames and buckets completed words green/amber/red"
    - "reading_progress preserves first_* values once and updates recent_* on every completed attempt"
    - "Completing a passage shows a summary dialog with avg F0, resonance, CPP, time, and a verdict sentence"
    - "Progress UI can show first-vs-recent reading scores for a completed passage"
  artifacts:
    - path: "src/switchedonvoice/reading/feedback.py"
      provides: "Pure scoring/aggregation logic"
    - path: "src/switchedonvoice/ui/session_summary_dialog.py"
      provides: "End-of-passage summary dialog"
    - path: "tests/reading/test_feedback.py"
      provides: "Per-word aggregation and threshold coverage"
  key_links:
    - from: "MainWindow._tick()"
      to: "ReadingPanel.update_result()"
      via: "shared AnalysisResult delivery while reading tab is active"
    - from: "ReadingPanel.complete_attempt()"
      to: "BookRepository.save_reading_scores()"
      via: "single transaction for first/recent fields"
---

<objective>
Add live acoustic feedback to Reading Mode, colour completed words based on
reading-session performance, persist first-vs-recent scores per passage, and
show a meaningful session summary at the end of each attempt.
</objective>

<wave_plan>
## Wave Breakdown

### Wave 1 — pure logic and persistence (parallel)
1. Add the `reading_progress` score columns and repository APIs.
2. Build/test the pure feedback aggregation and summary logic.
3. Build the summary dialog UI around the pure summary output.

### Wave 2 — Reading tab integration
4. Reuse shared audio widgets inside Reading Mode, feed `AnalysisResult`
   frames into the panel, recolour completed words, and surface health
   warnings.
5. Extend `ProgressPanel` with a reading-score comparison section.

### Wave 3 — end-to-end verification
6. Finalise `MainWindow` routing, idle-state behaviour, and integration
   tests for repeated passage attempts.
</wave_plan>

<tasks>
## Tasks

### Task 1 (Wave 1): Schema migration and repository support for reading scores

**Description:** Extend `reading_progress` so each passage can hold first and
recent acoustic outcomes, and expose repository methods that enforce the
one-time vs always-update semantics.

**Files to create/modify**
- Modify: `src/switchedonvoice/storage/db.py`
- Modify: `src/switchedonvoice/storage/books.py`
- Modify: `tests/storage/test_db.py`
- Modify: `tests/content/test_books_repository.py`

**Acceptance criteria (runnable assertions)**
- After migration, `PRAGMA table_info(reading_progress)` contains:
  `first_avg_f0`, `first_resonance_score`, `first_cpp_score`,
  `first_recorded_at`, `recent_avg_f0`, `recent_resonance_score`,
  `recent_cpp_score`, `recent_recorded_at`.
- Saving scores for a passage with null first_* fields writes both first_*
  and recent_* values.
- Saving a second attempt for the same passage leaves all first_* values
  unchanged and updates all recent_* values.
- Bookmark and completion fields still round-trip after the migration.

**Test strategy**
- `tests/storage/test_db.py`
  - schema version bump / new columns present
- `tests/content/test_books_repository.py`
  - first/recent semantics
  - transaction updates all related columns atomically

**Security / edge-case notes**
- Use an independent `if version < N` migration block; never reorder older
  migration blocks.
- Handle passages with no previous progress row by creating the row before or
  during score persistence in one transaction.

### Task 2 (Wave 1): Pure feedback aggregation and scoring module

**Description:** Keep word scoring, resonance summary, CPP bucket logic, and
verdict generation outside the Qt layer.

**Files to create/modify**
- Create: `src/switchedonvoice/reading/feedback.py`
- Test: `tests/reading/test_feedback.py`
- Modify: `src/switchedonvoice/health.py` (if CPP helpers are centralised here)
- Test: `tests/test_health.py`

**Acceptance criteria (runnable assertions)**
- Feeding voiced frames for word index 3 produces a mean F0 for word 3 only.
- Unvoiced frames do not create a false 0 Hz score.
- Threshold logic maps representative values to green / amber / red exactly
  as designed.
- Summary computation returns avg F0, resonance centroid, CPP bucket, total
  reading time, and a non-empty verdict sentence.

**Test strategy**
- `tests/reading/test_feedback.py`
  - per-word aggregation over multiple frames
  - threshold bucket boundaries
  - no-data/unvoiced handling
  - verdict string generation
- `tests/test_health.py`
  - CPP warning helper behaviour if added there

**Security / edge-case notes**
- Validate negative or NaN metrics defensively; summary output should fail
  fast in tests rather than silently producing misleading text.
- Keep thresholds as named constants at module scope; no magic numbers in UI.

### Task 3 (Wave 1): Session summary dialog

**Description:** Build the end-of-attempt dialog as a thin presenter over the
pure summary result from Task 2.

**Files to create/modify**
- Create: `src/switchedonvoice/ui/session_summary_dialog.py`
- Test: `tests/ui/test_session_summary_dialog.py`

**Acceptance criteria (runnable assertions)**
- Given a summary object, the dialog renders:
  - average F0 in Hz
  - a human-readable label (for example “feminine range”)
  - resonance centroid text
  - CPP indicator state
  - total reading time
  - verdict sentence
- The dialog is constructible offscreen in pytest-qt.

**Test strategy**
- `tests/ui/test_session_summary_dialog.py`
  - field rendering
  - CPP state colour/icon mapping
  - verdict label population

**Security / edge-case notes**
- The dialog should accept already-computed values; do not repeat scoring
  logic in widget code.

### Task 4 (Wave 2): ReadingPanel live overlay integration

**Description:** Reuse the shared analysis widgets inside Reading Mode,
accumulate per-word metrics while active, and finalise colouring + summary on
completion.

**Files to create/modify**
- Modify: `src/switchedonvoice/ui/reading_panel.py`
- Modify: `src/switchedonvoice/ui/passage_display_widget.py`
- Modify: `tests/ui/test_reading_panel.py`

**Acceptance criteria (runnable assertions)**
- When the Reading tab is active, calling `update_result(result)` updates the
  embedded pitch meter, vowel space, and spectrum widgets.
- When the tab is inactive, `update_result(result)` does not mutate reading
  feedback state.
- Completing word N finalises a colour bucket for word N and does not alter
  future words.
- Reaching the end of the passage computes a summary and shows the dialog.
- CPP warnings, once implemented, surface in the Reading tab without
  disturbing word-tracking state.

**Test strategy**
- `tests/ui/test_reading_panel.py`
  - active vs inactive update behaviour
  - per-word recolour after advance
  - end-of-passage summary trigger
  - CPP warning label state

**Security / edge-case notes**
- Ignore frames when no passage is loaded.
- Ensure paused/hidden tabs stop accumulation so old frames do not bleed into
  a later reading attempt.

### Task 5 (Wave 2): Progress tab comparison UI

**Description:** Surface the newly persisted first-vs-recent reading scores
somewhere in `ProgressPanel` so Phase 4's persistence is visible to the user.

**Files to create/modify**
- Modify: `src/switchedonvoice/ui/progress_panel.py`
- Test: `tests/ui/test_progress_panel.py`

**Acceptance criteria (runnable assertions)**
- Given a passage with both first_* and recent_* values, `ProgressPanel`
  renders both sets distinctly.
- With no reading scores yet, the panel renders an explicit empty state.
- A refreshed panel shows newly saved recent scores without app restart.

**Test strategy**
- `tests/ui/test_progress_panel.py`
  - empty state
  - first-vs-recent values present
  - refresh after repository update

**Security / edge-case notes**
- Keep passage-level score queries inside repository/storage code; the panel
  should not compose raw SQL.

### Task 6 (Wave 3): MainWindow routing and integration verification

**Description:** Finalise shared capture routing and prove repeated attempts
behave correctly end-to-end.

**Files to create/modify**
- Modify: `src/switchedonvoice/ui/main_window.py`
- Modify: `tests/ui/test_main_window.py`
- Modify: `tests/ui/test_reading_panel.py`

**Acceptance criteria (runnable assertions)**
- `MainWindow` still owns exactly one `AudioCapture` instance.
- Switching to Reading sends subsequent analysis frames to Reading widgets;
  switching away leaves Reading feedback idle.
- Completing the same passage twice preserves the original first_* values and
  updates recent_* values visible in Progress.

**Test strategy**
- `tests/ui/test_main_window.py`
  - no second capture instance
  - active-tab routing
- `tests/ui/test_reading_panel.py`
  - two-attempt persistence semantics through UI flow

**Security / edge-case notes**
- Preserve the existing queue-drain loop and session frame persistence for
  Phase 1 behaviour; Phase 4 should extend, not replace, the `_tick()` flow.
</tasks>

<verification>
## Verification

```bash
cd /home/alice/git/switchedonvoice
pytest tests/storage/test_db.py tests/content/test_books_repository.py tests/reading/test_feedback.py tests/test_health.py -q
pytest tests/ui/test_session_summary_dialog.py tests/ui/test_reading_panel.py tests/ui/test_progress_panel.py tests/ui/test_main_window.py -q
pytest -q
```
</verification>

<completion_criteria>
## Completion Criteria

Phase 4 is done only when all of the following are true:

- Reading Mode shows live pitch/vowel/spectrum feedback while active and goes
  idle when hidden.
- Completed words receive stable green/amber/red colouring based on the pure
  scoring logic.
- Every completed reading attempt produces a summary dialog with meaningful
  metrics and verdict text.
- The DB preserves first-attempt scores and latest-attempt scores separately.
- Progress UI exposes the persisted comparison so the user can see “first vs
  now” for a passage.
- The full test suite still passes.
</completion_criteria>
