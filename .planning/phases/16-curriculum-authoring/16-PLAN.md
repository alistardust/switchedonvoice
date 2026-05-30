---
phase: 16-curriculum-authoring
plan_type: phase-plan
requirements:
  - REQ-I02
  - REQ-I04
depends_on:
  - Phase 15
  - Phase 6
status: ready
waves:
  - 1
  - 2
  - 3
---

# Phase 16 Plan — Curriculum Authoring

## Goal
Let a coach build a structured curriculum with drag-and-drop ordering, custom
passages, measurable targets, and a portable `.sov-curriculum` export/import
format.

## Execution Principles

- Keep serialization logic out of Qt widgets.
- Use slug-based references for built-in passages/exercises.
- Make import transactional and deterministic.
- Prefer plain text and minimal dependencies for v1.

## Wave 1 — Storage, manifest schema, and pure target logic

### Task 1.1 — Add curriculum-authoring storage schema
**Files**
- Modify: `src/switchedonvoice/storage/db.py`
- Create: `src/switchedonvoice/storage/custom_passages.py`
- Create: `src/switchedonvoice/storage/curricula.py`
- Modify: `src/switchedonvoice/curriculum/service.py`
- Test: `tests/storage/test_custom_passages.py`
- Test: `tests/storage/test_curricula.py`

**Work**
- Add `custom_passages`, `curricula`, and `curriculum_items` tables.
- Keep all rows profile-owned and persist item order via explicit `position`.
- Expose repository functions for curriculum CRUD, item CRUD, and ordered
  retrieval.

**Acceptance criteria**
- Custom passages persist per profile.
- Authored curricula persist with deterministic item ordering.
- Deleting a profile removes its curricula and custom passages.

### Task 1.2 — Define the `.sov-curriculum` package I/O layer
**Files**
- Create: `src/switchedonvoice/curriculum/package_io.py`
- Test: `tests/curriculum/test_package_io.py`

**Work**
- Implement manifest validation, ZIP export, and ZIP import.
- Serialize built-in passage references by `passage_slug`.
- Serialize custom passage text as separate `custom_passages/*.txt` files.
- Reject malformed manifests before any DB write begins.

**Acceptance criteria**
- Export produces a valid ZIP with parseable `manifest.json`.
- Import recreates the same item order, titles, targets, and custom text.
- Invalid packages perform zero DB writes.

### Task 1.3 — Implement pure target evaluation helpers
**Files**
- Create: `src/switchedonvoice/curriculum/targets.py`
- Test: `tests/curriculum/test_targets.py`

**Work**
- Add pure functions that evaluate metrics like `avg_f0`, `cpp`, and
  `consecutive_sessions` against saved session/evaluation data.
- Normalize operator handling (`>=`, `<=`, `==`).

**Acceptance criteria**
- `avg_f0 >= 180 Hz` reports met/unmet correctly.
- Consecutive-session targets are deterministic and unit tested.
- Widgets do not perform target comparison logic inline.

## Wave 2 — Coach authoring UI

### Task 2.1 — Build the curriculum builder window
**Files**
- Create: `src/switchedonvoice/ui/curriculum_builder_window.py`
- Create: `src/switchedonvoice/ui/curriculum_palette.py`
- Modify: `src/switchedonvoice/ui/settings_panel.py`
- Test: `tests/ui/test_curriculum_builder_window.py`

**Work**
- Add a coach-only `Build Curriculum` entry point in Settings.
- Build the palette/sidebar for built-in passages, exercises, and instruction
  blocks.
- Implement an ordered drag-and-drop list for curriculum items.

**Acceptance criteria**
- A coach can assemble a five-item curriculum entirely in the builder window.
- Dragging items changes persisted order.
- Student profiles do not see the builder entry point.

### Task 2.2 — Add custom passage and target editors
**Files**
- Modify: `src/switchedonvoice/ui/curriculum_builder_window.py`
- Modify: `src/switchedonvoice/storage/custom_passages.py`
- Test: `tests/ui/test_curriculum_builder_window.py`

**Work**
- Add a plain-text editor pane for coach-authored passages.
- Add target editing controls for metric/operator/value/consecutive sessions.
- Bind editor state to repository/package models rather than widget-local JSON.

**Acceptance criteria**
- Custom passages can be created and assigned as curriculum items.
- Targets can be attached or removed per item.
- Edited content survives reopen/reload.

## Wave 3 — Import/export flow, validation, and regression coverage

### Task 3.1 — Wire export to the builder and add student-facing import
**Files**
- Modify: `src/switchedonvoice/ui/curriculum_builder_window.py`
- Modify: `src/switchedonvoice/ui/settings_panel.py`
- Modify: `src/switchedonvoice/curriculum/package_io.py`
- Test: `tests/curriculum/test_package_io.py`
- Test: `tests/ui/test_curriculum_builder_window.py`
- Test: `tests/ui/test_settings_panel.py`

**Work**
- Add `Save as .sov-curriculum` to the coach builder window.
- Add an `Import Curriculum` entry point available to all profile types from
  Settings or the nearest equivalent shared file-action surface.
- Surface validation failures as clear UI errors.
- Ensure imported curricula are stored under the importing profile.

**Acceptance criteria**
- Export/import round-trip recreates the authored curriculum exactly.
- Students can import a coach-authored package without access to coach-only
  builder controls.
- Corrupt packages show a clear error and change nothing in the DB.
- Import works on a fresh profile with no hidden dependencies on source IDs.

### Task 3.2 — Final verification and UX timing pass
**Files**
- Modify: `tests/ui/test_curriculum_builder_window.py`
- Modify: `tests/curriculum/test_package_io.py`
- Modify: `tests/curriculum/test_targets.py`

**Work**
- Cover ordering persistence, malformed manifest rejection, and target
  evaluation against sample session data.
- Do a manual smoke pass for the “build 5 items in under 2 minutes” success
  criterion.

**Acceptance criteria**
- Automated tests cover serialization, validation, targets, and ordering.
- Manual smoke flow confirms the authoring UX is not overly cumbersome.

## Test Strategy

- Pure-module tests first: package I/O + target evaluation.
- Storage tests for custom passage/profile scoping.
- `pytest-qt` UI tests for drag/drop ordering, coach gating, and import/export
  actions.

**Suggested commands**
```bash
pytest tests/storage/test_custom_passages.py -q
pytest tests/curriculum/test_package_io.py tests/curriculum/test_targets.py -q
QT_QPA_PLATFORM=offscreen pytest tests/ui/test_curriculum_builder_window.py -q
pytest -q
```

## Completion Criteria

- Coach-only builder UI exists and persists ordered curricula.
- Student-facing curriculum import exists outside the coach-only builder flow.
- Custom passages are profile-owned and export/import correctly.
- `.sov-curriculum` ZIPs validate and round-trip without DB-ID coupling.
- Target evaluation works against saved session data.
- Corrupt imports fail safely with no partial writes.
