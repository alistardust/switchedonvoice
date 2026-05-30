# Phase 24: Milestone Recording & Comparison - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Goal

Phase 24 lets the user record the same short, standard passage at major practice
milestones, then compare those recordings over time through playback, waveform
views, and acoustic trend summaries.

This phase is about reflective evidence of progress, not live scoring. It should
reuse the recording and session-history foundations from earlier phases and stay
fully offline.
</domain>

<dependencies>
## Dependencies on Earlier Phases

- **Phase 5 — Recording infrastructure:** provides the capture path, WAV writing,
  and playback primitives this phase should wrap instead of reinventing.
- **Phase 18 — Session reports/data:** provides stable historical aggregates and a
  pattern for assembling read-only comparison data from stored artifacts.
- **Existing storage layer:** `src/switchedonvoice/storage/db.py` already owns the
  migration pattern (`PRAGMA user_version`, independent `if version < N` blocks)
  and `src/switchedonvoice/storage/sessions.py` already owns session lifecycle,
  streak, and history queries.
- **Existing UI shell:** `src/switchedonvoice/ui/main_window.py`,
  `src/switchedonvoice/ui/progress_panel.py`, and `src/switchedonvoice/ui/waveform_widget.py`
  are the likely host points for the milestone prompt, selector, and comparison UI.

Assume the dependency phases exist before implementation starts. Do **not** block
Phase 24 on speculative future work such as community sharing or cloud storage.
</dependencies>

<decisions>
## Key Decisions

### D-24-01: Milestone passages are packaged assets with stable slugs
Use a small curated library of 3–5 standard passages stored under the package
(`src/switchedonvoice/.../assets/`), not imported books and not user-authored
content. Each passage gets a stable `slug`, title, rationale, and body text so the
same text can be rerecorded years later without DB churn.

### D-24-02: Triggering is event-based, not free-form
A milestone recording prompt should be created only when a qualifying event is
observed: e.g. tenth session, 30-day streak, first skill-tree tier completion.
Represent these as stable `milestone_key` strings and persist prompt state so the
UI can offer a dismissible prompt without nagging on every repaint.

### D-24-03: Store one recording row per completed milestone capture
Persist a row containing the WAV path plus a scalar acoustic snapshot
(`f0_median_hz`, `f1_hz`, `f2_hz`, `cpp_db`) inside SQLite. The raw waveform stays
on disk as a WAV file under the app data directory; SQLite stores metadata,
indexes, and summary values.

### D-24-04: Keep the first comparison algorithm conservative
REQ-M01 is marked as a gap and lacks a detailed comparison algorithm, so the first
implementation should avoid time-warped alignment, phoneme matching, or any claim
of objective voice quality scoring. v1 compares:

- normalized waveform envelopes for two selected recordings,
- date-ordered scalar trends across all recordings,
- simple acoustic deltas between two snapshots.

### D-24-05: Comparison data assembly belongs outside widgets
Widgets should render preassembled view models, not open WAV files or query
SQLite directly. Create a dedicated comparison/data-assembly layer that loads two
WAVs, resamples envelopes to a fixed point count, and emits immutable structures
for waveform overlay, trend charting, and playback labels.

### D-24-06: Back-to-back playback is an explicit sequence
"Hearing yourself become yourself" should be implemented as a small playback
controller that plays clip A, waits a named pause constant, then plays clip B
while showing both date labels and a plain-language delta summary. Do not mix this
control flow into the generic UI paint/update path.
</decisions>

<research>
## Research Findings

### R-24-01: The repo already has the primitives needed for a lightweight waveform UI
`src/switchedonvoice/ui/waveform_widget.py` shows that waveform rendering is
already part of the codebase. Reuse that visual language and keep any milestone
overlay rendering in Qt/PySide rather than introducing a second plotting stack.

### R-24-02: The storage migration pattern is fixed and must cascade cleanly
`src/switchedonvoice/storage/db.py` reads `PRAGMA user_version` once and then
applies all pending migrations. New tables for milestone prompts/recordings must
therefore be added with a new independent `if version < N:` block, never `elif`,
and the schema version must be bumped exactly once.

### R-24-03: Passage identity in this repo is slug-based
The planning corpus already established `passage_slug TEXT` as the canonical text
reference, not integer IDs. Milestone recordings should therefore point at a
milestone-passage `slug` rather than inventing another numeric foreign-key scheme.

### R-24-04: Acoustic summaries should use the same analysis vocabulary already present
The current DSP pipeline already surfaces pitch, formants, and CPP through
`AnalysisResult` in `audio/capture.py`. Reuse those same measures for milestone
snapshots so the comparison screen speaks the same language as the rest of the
product and does not create parallel metrics.

### R-24-05: Prompt state must be persisted, not inferred from live UI state
A dismissible, non-intrusive prompt cannot live only in widget memory because the
user may close the app or navigate away before acting. Persist prompt state in the
DB with explicit statuses such as `pending`, `dismissed`, and `completed`.
</research>

<data_model>
## Data Model

### SQLite

Recommended new tables:

```sql
CREATE TABLE milestone_recording_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER,
    milestone_key TEXT NOT NULL,
    milestone_label TEXT NOT NULL,
    qualifying_session_id INTEGER,
    suggested_passage_slug TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'dismissed', 'completed')),
    created_at TEXT NOT NULL,
    acted_at TEXT,
    UNIQUE(profile_id, milestone_key)
);

CREATE TABLE milestone_recordings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER,
    prompt_id INTEGER REFERENCES milestone_recording_prompts(id) ON DELETE SET NULL,
    milestone_key TEXT NOT NULL,
    passage_slug TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    wav_path TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    f0_median_hz REAL,
    f1_hz REAL,
    f2_hz REAL,
    cpp_db REAL,
    notes TEXT,
    UNIQUE(profile_id, milestone_key, recorded_at)
);
```

### Dataclasses / View Models

- `MilestonePassage(slug, title, text, rationale)`
- `MilestonePrompt(id, milestone_key, milestone_label, suggested_passage_slug, status)`
- `AcousticSnapshot(f0_median_hz, f1_hz, f2_hz, cpp_db)`
- `MilestoneRecording(id, milestone_key, passage_slug, recorded_at, wav_path, duration_seconds, snapshot)`
- `WaveformOverlay(points_a, points_b, label_a, label_b)`
- `MilestoneTrendSeries(dates, f0_values, f1_values, f2_values, cpp_values)`
- `PlaybackComparison(first_recording_id, second_recording_id, pause_seconds, delta_summary)`

### Key Interfaces

- `MilestoneRecordingRepository`: persistence for prompts and completed recordings
- `MilestoneRecordingService`: orchestration layer that turns qualifying events
  into prompts and completed recordings
- `MilestoneComparisonBuilder`: pure/service layer that assembles waveform,
  trend, and delta view models for the UI
</data_model>

<open_questions>
## Open Questions Deferred to Later Phases

1. Which exact public-domain/standard passage set should ship in v1: Rainbow,
   Grandfather, North Wind and the Sun, Comma Gets a Cure, or a more
   trans-specific curated set? The implementation can proceed with stable slugs and
   placeholder copy, but content sign-off is still needed.
2. Should milestone recordings eventually support optional text notes or
   self-reflection prompts? Useful, but not required for REQ-M01.
3. Should waveform comparison later add loudness normalization or phoneme-level
   alignment? Deferred until the gap issue behind REQ-M01 is specified.
4. Should users be allowed to create ad-hoc milestone recordings outside a major
   milestone event? Deferred; Phase 24 is milestone-triggered only.
</open_questions>

---

*Phase: 24-milestone-comparison*
*Context gathered: 2026-05-30 for plan authoring*
