---
phase: 09-evaluation-mode
plan: 01
type: execute
wave: multi
depends_on:
  - 04-acoustic-overlay
  - 05-recording-playback
  - 06-curriculum-schema
files_modified:
  - src/switchedonvoice/storage/db.py
  - src/switchedonvoice/storage/evaluations.py
  - src/switchedonvoice/evaluation/scoring.py
  - src/switchedonvoice/evaluation/service.py
  - src/switchedonvoice/ui/report_card_dialog.py
  - src/switchedonvoice/ui/evaluation_trend_widget.py
  - src/switchedonvoice/ui/progress_panel.py
  - src/switchedonvoice/ui/main_window.py
  - src/switchedonvoice/ui/reading_panel.py
  - pyproject.toml
  - tests/evaluation/test_scoring.py
  - tests/storage/test_evaluations.py
  - tests/ui/test_report_card_dialog.py
  - tests/ui/test_evaluation_trend_widget.py
  - tests/ui/test_main_window.py
autonomous: true
requirements:
  - REQ-C03
  - REQ-C05
must_haves:
  truths:
    - "Database schema version advances by exactly one from the schema version present when Phase 9 starts (expected baseline: 6 if upstream phases remain unchanged)"
    - "Evaluation mode hides live hints for the full run while background analysis and recording continue"
    - "Resonance score uses the fixed reference ellipse centered at (450, 1650) with radii (180, 420)"
    - "Average of the five normalized scores multiplied by 100 is awarded as XP through CurriculumService"
    - "Per-passage trend graphs plot one line per dimension ordered by evaluation timestamp"
  artifacts:
    - path: "src/switchedonvoice/storage/db.py"
      provides: "Schema migration with evaluations"
      contains: "_CURRENT_SCHEMA_VERSION"
    - path: "src/switchedonvoice/evaluation/scoring.py"
      provides: "Pure score calculators and summary text builders"
    - path: "src/switchedonvoice/ui/report_card_dialog.py"
      provides: "Post-evaluation results dialog"
    - path: "src/switchedonvoice/ui/evaluation_trend_widget.py"
      provides: "pyqtgraph trend graph widget"
  key_links:
    - from: "src/switchedonvoice/evaluation/service.py"
      to: "src/switchedonvoice/curriculum/service.py"
      via: "award_xp(profile_id, 'evaluation', source_id, xp)"
      pattern: "average_score * 100"
    - from: "src/switchedonvoice/ui/reading_panel.py"
      to: "recording subsystem"
      via: "evaluation forces silent capture regardless of settings"
      pattern: "evaluation mode"
    - from: "src/switchedonvoice/ui/progress_panel.py"
      to: "src/switchedonvoice/storage/evaluations.py"
      via: "per-passage history adapter"
      pattern: "passage_slug"
---

<objective>
## Objective

Add a formal evaluation workflow to Reading Mode with silent capture, five
scored dimensions, persisted history, a report card dialog, per-passage trend
graphs, and XP credit tied to the final score.
</objective>

<execution_context>
@~/.copilot/get-shit-done/workflows/execute-plan.md
@~/.copilot/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/04-acoustic-overlay/04-PLAN.md
@.planning/phases/05-recording-playback/05-PLAN.md
@.planning/phases/06-curriculum-schema/06-PLAN.md
@.planning/phases/09-evaluation-mode/09-CONTEXT.md
@src/switchedonvoice/ui/progress_panel.py
</context>

<interfaces>
## Interfaces and conventions

- Storage uses `passage_slug TEXT` as the grouping key; do not switch to numeric IDs.
- Recommended pure scoring API:
  - `compute_pitch_accuracy(samples, target_range) -> float`
  - `compute_resonance_score(formant_track) -> float`
  - `compute_cpp_score(cpp_values) -> float`
  - `estimate_syllables(text: str) -> int`
  - `compute_pacing_score(syllables_per_minute) -> float`
  - `compute_consistency_score(f0_values) -> float`
- `EvaluationService` should return a typed payload containing five normalized
  scores, five plain-language summaries, mean score, and awarded XP.
- Evaluation recordings carry `recording_kind = "evaluation"` (or equivalent
  Phase 5 metadata) so practice-history UI can filter them by default.
- If `pyqtgraph` is still absent, add it to `pyproject.toml` in this phase.
</interfaces>

<threat_model>
## Threat model

- **False evaluation integrity:** never show live hints or stale overlay widgets
  during an active evaluation.
- **Formula drift:** keep all five dimension calculations in pure functions with
  fixed constants and targeted tests.
- **Silent recording mismatch:** evaluation mode must override ordinary recording
  preferences explicitly so reports always match captured data.
</threat_model>

<file_map>
## File Map

### Create
- `src/switchedonvoice/storage/evaluations.py`
- `src/switchedonvoice/evaluation/__init__.py`
- `src/switchedonvoice/evaluation/scoring.py`
- `src/switchedonvoice/evaluation/service.py`
- `src/switchedonvoice/ui/report_card_dialog.py`
- `src/switchedonvoice/ui/evaluation_trend_widget.py`
- `tests/evaluation/__init__.py`
- `tests/evaluation/test_scoring.py`
- `tests/storage/test_evaluations.py`
- `tests/ui/test_report_card_dialog.py`
- `tests/ui/test_evaluation_trend_widget.py`

### Modify
- `src/switchedonvoice/storage/db.py`
- `src/switchedonvoice/ui/progress_panel.py`
- `src/switchedonvoice/ui/main_window.py`
- `src/switchedonvoice/ui/reading_panel.py` *(or the Phase 3–5 reading module that owns the passage header)*
- `pyproject.toml` *(if `pyqtgraph` is still absent)*
- `tests/ui/test_main_window.py`
</file_map>

<waves>
## Wave Plan

### Wave 1 (parallel) — Persistence and scoring engine

#### Task 1: Add evaluation schema and repository
**Files:** `src/switchedonvoice/storage/db.py`, `src/switchedonvoice/storage/evaluations.py`, `tests/storage/test_evaluations.py`

**Description:**
Add the next schema version after the version present when Phase 9 starts
(expected `6` if upstream plans stay unchanged) with the `evaluations` table and
repository helpers for
insert and per-passage history queries ordered by timestamp.

**Acceptance criteria:**
- FK/reference strategy matches the `passage_slug` requirement
- inserts and history reads are deterministic
- repository returns the exact data shape needed by the trend widget

**Automated verify:**
- `pytest tests/storage/test_evaluations.py -q`
- include assertions for `PRAGMA user_version == previous_version + 1`

#### Task 2: Implement pure scoring functions
**Files:** `src/switchedonvoice/evaluation/scoring.py`, `tests/evaluation/test_scoring.py`

**Description:**
Build pure calculators for pitch accuracy, resonance score, CPP health, pacing,
and consistency, plus helpers that turn scores into plain-language summaries.
Use the fixed resonance ellipse from the context: center `(450, 1650)`, radii
`(180, 420)`, score `clamp(1 - normalized_distance, 0, 1)`. For pacing, derive
syllables per minute from a local `estimate_syllables(text)` heuristic over the
selected passage text and the recorded run duration.

**Acceptance criteria:**
- each dimension is testable from synthetic inputs
- scores are normalized to a clear 0–1 internal convention
- summary text is deterministic and user-facing

**Automated verify:**
- `pytest tests/evaluation/test_scoring.py -q`

### Wave 2 (depends on Wave 1) — Evaluation orchestration

#### Task 3: Implement evaluation service and XP hook
**Files:** `src/switchedonvoice/evaluation/service.py`

**Description:**
Orchestrate scoring, persistence, XP award, and history retrieval. The service
accepts final captured run data and returns a report-card payload plus awarded
XP, where `xp = round(mean_score * 100)`.

**Acceptance criteria:**
- average score × 100 XP formula is applied through `CurriculumService`
- service returns both numeric values and plain-language strings
- no UI code needs to know how scores are computed

**Automated verify:**
- `pytest tests/evaluation/test_scoring.py tests/storage/test_evaluations.py -q`

#### Task 4: Add evaluation mode entry/exit to Reading UI
**Files:** `src/switchedonvoice/ui/reading_panel.py` *(or equivalent)*, recording service module, `tests/ui/test_main_window.py`

**Description:**
Add the Evaluate button to the passage header, suppress live overlays during an
active evaluation, and force silent recording regardless of ordinary settings.

**Acceptance criteria:**
- visible hints disappear for the entire evaluation run
- recording starts/stops automatically for evaluation sessions
- evaluation recordings are tagged/segregated from ordinary practice history
- ordinary practice mode remains unchanged

**Automated verify:**
- `pytest tests/ui/test_main_window.py -q`

### Wave 3 (depends on Wave 2) — Reporting UI

#### Task 5: Build `ReportCardDialog`
**Files:** `src/switchedonvoice/ui/report_card_dialog.py`, `tests/ui/test_report_card_dialog.py`

**Description:**
Show the five dimension scores, plain-language explanations, total/average
score, and XP earned.

**Acceptance criteria:**
- dialog renders all five dimensions consistently
- copy is readable and affirming
- XP earned is shown from the service response, not recomputed locally

**Automated verify:**
- `pytest tests/ui/test_report_card_dialog.py -q`

#### Task 6: Add per-passage trend graph to Progress tab
**Files:** `src/switchedonvoice/ui/evaluation_trend_widget.py`, `src/switchedonvoice/ui/progress_panel.py`, `tests/ui/test_evaluation_trend_widget.py`

**Description:**
Embed a pyqtgraph multi-line chart showing one line per dimension and one point
per evaluation for the selected passage.

**Acceptance criteria:**
- with three evaluations of one passage, each line shows three ordered points
- empty state is handled without errors
- Progress tab can refresh the chart when a new evaluation is added

**Automated verify:**
- `pytest tests/ui/test_evaluation_trend_widget.py tests/ui/test_main_window.py -q`
- `pytest -q`
</waves>

<test_strategy>
## Test Strategy

### Target commands
- `pytest tests/evaluation/test_scoring.py tests/storage/test_evaluations.py tests/ui/test_report_card_dialog.py tests/ui/test_evaluation_trend_widget.py tests/ui/test_main_window.py -q`
- `pytest -q`

### Key test cases
- exact pitch-accuracy computation for samples inside vs outside target range
- resonance ellipse distance normalization
- CPP threshold pass/fail boundary
- pacing in-range vs too-slow vs too-fast samples
- consistency score from low-variance vs high-variance F0 runs
- evaluation storage round-trip with one passage and multiple timestamps
- XP award formula correctness for known averages
</test_strategy>

<edge_cases>
## Edge Case Notes

- unvoiced or mostly silent runs should produce a valid low-score report, not a crash
- if recording fails, the evaluation should fail loudly and not present a fake report card
- timestamps must sort correctly across time zones and app restarts
- if `pyqtgraph` is added here, tests should pin its import path explicitly
</edge_cases>

<completion_criteria>
## Completion Criteria

Phase 9 is complete when:
- Reading Mode supports a distinct no-hints evaluation run
- finishing an evaluation shows a five-dimension report card
- evaluations persist by `passage_slug` and render in a trend graph
- evaluation XP is credited through `CurriculumService` and visible in XP history
- focused tests and full `pytest -q` pass
</completion_criteria>

<output>
## Output

When implementation completes, create `.planning/phases/09-evaluation-mode/09-SUMMARY.md`
using the standard summary template and update ROADMAP status accordingly.
</output>
