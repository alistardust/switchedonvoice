---
phase: 17-homework-assignment
plan_type: phase-plan
requirements:
  - REQ-I03
depends_on:
  - Phase 15
  - Phase 16
status: ready
waves:
  - 1
  - 2
  - 3
---

# Phase 17 Plan — Homework Assignment

## Goal
Allow coach profiles to assign passages/exercises to student profiles, surface
those assignments on the student home screen, and track/report completion
without mixing homework into free-practice flows.

## Execution Principles

- Reuse the existing session pipeline; do not create a parallel homework-only
  session model.
- Keep homework completion explicit and attribution-based.
- Put aggregation in services/storage, not widgets.
- Preserve profile isolation at every query boundary.

## Wave 1 — Homework schema and service layer

### Task 1.1 — Add homework persistence and session attribution fields
**Files**
- Modify: `src/switchedonvoice/storage/db.py`
- Create: `src/switchedonvoice/storage/homework.py`
- Modify: `src/switchedonvoice/storage/sessions.py`
- Test: `tests/storage/test_homework.py`

**Work**
- Add the `homework` table.
- Extend `sessions` with homework attribution fields.
- Add storage helpers for assignment CRUD, item completion updates, and student /
  coach list queries.

**Acceptance criteria**
- Homework rows persist with stable `items_json` schema.
- Sessions can be tagged as `Homework` or `Free practice`.
- Assignment status transitions correctly between `pending`, `partial`, and
  `complete`.

### Task 1.2 — Build homework orchestration logic
**Files**
- Create: `src/switchedonvoice/services/homework_service.py`
- Modify: `src/switchedonvoice/storage/homework.py`
- Test: `tests/services/test_homework_service.py`

**Work**
- Implement assignment creation, item expansion, completion recording, and coach
  report aggregation.
- Keep completion idempotent if the same homework item is re-opened.

**Acceptance criteria**
- Coach report output includes completion percentage, item dates, and score
  snapshots.
- Replaying the same completion event does not duplicate progress.
- Student and coach views filter correctly by profile IDs.

## Wave 2 — Coach and student UI flows

### Task 2.1 — Add coach assignment and report UI
**Files**
- Create: `src/switchedonvoice/ui/student_management_panel.py`
- Modify: `src/switchedonvoice/ui/settings_panel.py`
- Modify: `src/switchedonvoice/ui/main_window.py`
- Test: `tests/ui/test_student_management_panel.py`

**Work**
- Add coach-only student selection, assignment creation, due-date entry, and
  completion report views.
- Show per-assignment progress and per-item results.

**Acceptance criteria**
- A coach can assign three items to a student in one flow.
- The report view shows `1/3`, dates, and score details after one item is done.
- Non-coach profiles do not see student-management controls.

### Task 2.2 — Add student homework surfacing and deep-link starts
**Files**
- Create: `src/switchedonvoice/ui/homework_panel.py`
- Modify: `src/switchedonvoice/ui/analysis_panel.py`
- Modify: `src/switchedonvoice/ui/main_window.py`
- Test: `tests/ui/test_homework_panel.py`
- Test: `tests/ui/test_main_window.py`

**Work**
- Add the "Assigned by your coach" section to the Analysis/home view.
- Render coach name, due-date badge, and `Start` deep-link per pending item.
- Wire `Start` into session creation so the resulting session carries homework
  attribution metadata.

**Acceptance criteria**
- Students with homework immediately see pending items.
- Students with no homework see no homework section.
- Starting from the homework panel creates homework-attributed sessions.

## Wave 3 — Completion labeling, aggregation, and regression coverage

### Task 3.1 — Label session history and finalize completion state machine
**Files**
- Modify: `src/switchedonvoice/ui/progress_panel.py`
- Modify: `src/switchedonvoice/storage/homework.py`
- Modify: `src/switchedonvoice/services/homework_service.py`
- Test: `tests/ui/test_progress_panel.py`
- Test: `tests/storage/test_homework.py`

**Work**
- Update the history UI to label rows as `Homework` vs `Free practice`.
- Ensure completing one item updates only that homework item and the assignment
  header status.

**Acceptance criteria**
- Homework sessions are labelled correctly in history.
- Free-practice sessions remain separate.
- Assignment status changes from `pending` → `partial` → `complete` correctly.

### Task 3.2 — Final visibility and aggregation verification
**Files**
- Modify: `tests/services/test_homework_service.py`
- Modify: `tests/ui/test_homework_panel.py`
- Modify: `tests/ui/test_student_management_panel.py`

**Work**
- Add end-to-end tests for coach assigns → student sees → student completes →
  coach report updates.
- Add negative tests for wrong-student visibility and no-homework state.

**Acceptance criteria**
- Only the assigned student sees the assignment.
- Coach reports aggregate correct completion and score data.
- Homework data does not leak across profiles.

## Test Strategy

- Storage and service tests first for assignment state changes and aggregation.
- `pytest-qt` tests for coach/student visibility and deep-link starts.
- Regression run to ensure existing session/progress behaviour still works.

**Suggested commands**
```bash
pytest tests/storage/test_homework.py tests/services/test_homework_service.py -q
QT_QPA_PLATFORM=offscreen pytest tests/ui/test_homework_panel.py tests/ui/test_student_management_panel.py tests/ui/test_main_window.py -q
pytest tests/ui/test_progress_panel.py -q
pytest -q
```

## Completion Criteria

- Coaches can assign homework to student profiles with optional due dates.
- Students see pending homework only when relevant.
- Homework completion is tracked separately from free practice.
- Session history labels homework correctly.
- Coach report aggregation shows completion %, dates, and achieved scores.
