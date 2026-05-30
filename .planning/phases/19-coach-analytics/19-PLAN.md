---
phase: 19-coach-analytics
plan_type: phase-plan
requirements:
  - REQ-I06
depends_on:
  - Phase 15
  - Phase 17
  - Phase 18
status: ready
waves:
  - 1
  - 2
  - 3
---

# Phase 19 Plan — Coach Analytics View

## Goal
Give coach profiles a per-student analytics dashboard with weekly trends,
`First vs. Now` comparisons, session notes, and a multi-page progress PDF.

## Execution Principles

- Keep analytics/date bucketing pure and testable.
- Reuse Phase 18 report infrastructure for PDF generation.
- Preserve profile and coach ownership boundaries for notes.
- Compare passages by stable `passage_slug`, never by row order.

## Wave 1 — Analytics and notes foundations

### Task 1.1 — Add session notes persistence
**Files**
- Modify: `src/switchedonvoice/storage/db.py`
- Create: `src/switchedonvoice/storage/session_notes.py`
- Test: `tests/storage/test_session_notes.py`

**Work**
- Add the `session_notes` table.
- Implement CRUD helpers scoped by coach `profile_id` and `session_id`.

**Acceptance criteria**
- Coaches can create/read/update/delete their own notes.
- Notes cascade on coach/session deletion.
- One coach's notes do not leak into another coach's view.

### Task 1.2 — Build pure analytics aggregation helpers
**Files**
- Create: `src/switchedonvoice/analytics/constants.py`
- Create: `src/switchedonvoice/analytics/aggregates.py`
- Modify: `src/switchedonvoice/storage/sessions.py`
- Modify: `src/switchedonvoice/storage/evaluations.py`
- Test: `tests/analytics/test_aggregates.py`

**Work**
- Promote the feminine vowel reference point and F0 target-range band into
  shared inner-layer analytics constants.
- Implement rolling 8-week bucketing for F0 and resonance data.
- Aggregate curriculum/homework completion rate from Phase 17 assignment data.
- Implement `first_vs_now` selection by `passage_slug`.
- Expose data structures ready for UI and PDF rendering.

**Acceptance criteria**
- Weekly averages bucket correctly across month/year boundaries.
- Empty weeks are represented consistently.
- F0 trend data includes a reusable target-range band overlay.
- Curriculum/homework completion rate aggregates correctly from assignment data.
- `First vs. Now` returns the oldest and newest matching passage records only.

## Wave 2 — Coach dashboard UI

### Task 2.1 — Add the coach analytics panel
**Files**
- Create: `src/switchedonvoice/ui/coach_analytics_panel.py`
- Create: `src/switchedonvoice/ui/first_vs_now_panel.py`
- Modify: `src/switchedonvoice/ui/progress_panel.py`
- Modify: `src/switchedonvoice/ui/main_window.py`
- Test: `tests/ui/test_coach_analytics_panel.py`

**Work**
- Add a coach-only dashboard entry in the Progress area.
- Add student selector, `pyqtgraph` F0 trend chart with target-range band,
  resonance chart, curriculum completion summary, and `First` vs. `Now`
  comparison panel.
- Render Phase 18 waveform thumbnails side by side in the `First vs. Now` view.
- Add session note display and edit controls in the coach view.

**Acceptance criteria**
- Selecting student `Alex` loads Alex's weekly trend data with the target-range
  band overlay plus curriculum completion summary.
- `First vs. Now` shows waveform thumbnails plus score deltas with correct arrow
  badges.
- Notes appear under the correct session entries.

### Task 2.2 — Integrate notes into session history views
**Files**
- Modify: `src/switchedonvoice/ui/progress_panel.py`
- Modify: `src/switchedonvoice/storage/session_notes.py`
- Test: `tests/ui/test_progress_panel.py`
- Test: `tests/ui/test_coach_analytics_panel.py`

**Work**
- Show note snippets in history rows or detail affordances.
- Keep note editing scoped to the active coach profile.

**Acceptance criteria**
- Notes appear with the correct session.
- Student history is not polluted by notes from other coaches.
- Editing a note updates the right record only.

## Wave 3 — PDF export and final verification

### Task 3.1 — Build full student progress PDF on top of Phase 18 reporting
**Files**
- Create: `src/switchedonvoice/reports/student_progress_pdf.py`
- Modify: `src/switchedonvoice/reports/exporter.py`
- Test: `tests/reports/test_student_progress_pdf.py`

**Work**
- Assemble cover summary, weekly F0 chart, resonance chart, top-3 `First vs. Now`
  comparisons with waveform thumbnails, and session list into a multi-page
  export.
- Reuse existing HTML/PDF infrastructure instead of a parallel pipeline.

**Acceptance criteria**
- Exported PDFs contain all required sections.
- Students with 4+ weeks of data produce PDFs longer than 2 pages.
- Chart rendering is consistent with the on-screen dashboard.

### Task 3.2 — Final regression and aggregation verification
**Files**
- Modify: `tests/analytics/test_aggregates.py`
- Modify: `tests/storage/test_session_notes.py`
- Modify: `tests/ui/test_coach_analytics_panel.py`
- Modify: `tests/reports/test_student_progress_pdf.py`

**Work**
- Cover date bucketing edge cases, multi-coach note ownership, and PDF smoke.
- Run manual QA on a seeded 4+ week student profile.

**Acceptance criteria**
- Weekly aggregation tests prove correct bucketing.
- Session notes CRUD is fully covered.
- PDF smoke tests and manual QA both pass.

## Test Strategy

- Pure analytics tests first for bucketing and `First vs. Now` logic.
- Storage tests for note ownership and CRUD.
- `pytest-qt` tests for coach dashboard behaviour.
- PDF smoke tests plus manual seeded-data verification for page count/readability.

**Suggested commands**
```bash
pytest tests/analytics/test_aggregates.py tests/storage/test_session_notes.py -q
QT_QPA_PLATFORM=offscreen pytest tests/ui/test_coach_analytics_panel.py tests/ui/test_progress_panel.py -q
QT_QPA_PLATFORM=offscreen pytest tests/reports/test_student_progress_pdf.py -q
pytest -q
```

## Completion Criteria

- Coaches can inspect per-student weekly F0 and resonance trends.
- `First vs. Now` comparisons work by `passage_slug` and show correct deltas.
- Session notes persist under the authoring coach profile.
- Full student progress PDFs reuse the Phase 18 export stack and include all
  required sections.
