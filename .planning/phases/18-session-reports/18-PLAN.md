---
phase: 18-session-reports
plan_type: phase-plan
requirements:
  - REQ-I04
depends_on:
  - Phase 15
  - Phase 17
  - Phase 9
  - Phase 5
status: ready
waves:
  - 1
  - 2
  - 3
---

# Phase 18 Plan — Session Reports & File Export

## Goal
Export any saved session as HTML, PDF, and `.sov-session`, then view those
portable packages on another machine without any database dependency.

## Execution Principles

- Keep export/view logic separate from widgets.
- Treat WebEngine as optional.
- Keep report rendering deterministic for tests.
- Make `.sov-session` fully self-contained.

## Wave 1 — Reporting core and package format

### Task 1.1 — Build report data assembly and HTML rendering
**Files**
- Create: `src/switchedonvoice/reports/html_renderer.py`
- Create: `src/switchedonvoice/reports/report_models.py`
- Test: `tests/reports/test_html_renderer.py`

**Work**
- Define report data models for session metadata, scores, assets, and notes.
- Implement a deterministic HTML renderer using a stdlib template or another
  lightweight templating approach.
- Ensure inline references point to portable relative asset paths.

**Acceptance criteria**
- HTML rendering is snapshot-testable.
- Output contains metadata, score table, charts, waveform, and notes sections.
- Rendering does not require Qt.

### Task 1.2 — Implement chart asset generation and `.sov-session` packaging
**Files**
- Create: `src/switchedonvoice/reports/exporter.py`
- Create: `src/switchedonvoice/reports/package_io.py`
- Modify: `src/switchedonvoice/storage/sessions.py`
- Modify: `src/switchedonvoice/storage/evaluations.py`
- Test: `tests/reports/test_package_io.py`

**Work**
- Generate SVG assets for F0-over-time, vowel trajectory, and waveform.
- Serialize `session.json`, `report.html`, chart assets, and optional `audio.wav`
  into `.sov-session` ZIP files.
- Implement package validation and read-only loading helpers.

**Acceptance criteria**
- `.sov-session` exports are valid ZIP files with the documented structure.
- Export/import helpers round-trip metadata and assets.
- Missing optional audio is handled gracefully.

## Wave 2 — PDF export and viewer UI

### Task 2.1 — Add PDF export backend with documented fallback hook
**Files**
- Modify: `src/switchedonvoice/reports/exporter.py`
- Modify: `pyproject.toml`
- Test: `tests/reports/test_pdf_export.py`

**Work**
- Implement PDF export via Qt `QPrinter`.
- Add a backend abstraction so an optional WeasyPrint fallback can be enabled if
  manual QA shows Qt output is insufficient.
- Document any optional dependency/runtime requirement cleanly.

**Acceptance criteria**
- PDF smoke tests confirm non-empty output with a valid `%PDF` header.
- At least one chart appears in exported PDF output.
- The implementation does not hard-require WeasyPrint on systems where Qt output
  is acceptable.

### Task 2.2 — Build the read-only session viewer
**Files**
- Create: `src/switchedonvoice/ui/session_report_viewer.py`
- Modify: `src/switchedonvoice/ui/main_window.py`
- Test: `tests/ui/test_session_report_viewer.py`

**Work**
- Add drag-in/file-open support for `.sov-session` files.
- Prefer `QWebEngineView` when available; otherwise fall back to `QTextBrowser`.
- Read package contents directly from the ZIP where possible; if any asset must
  be materialized, write it only under `~/.switchedonvoice/`, not a system temp
  directory.
- Surface corrupt package errors without crashing.

**Acceptance criteria**
- Viewer loads a valid `.sov-session` on a machine with no source DB state.
- Fallback rendering works when WebEngine is unavailable.
- No viewer path writes extracted files to a system temp directory.
- Corrupt `session.json` shows a clear error.

## Wave 3 — Progress-tab export flow and regression coverage

### Task 3.1 — Add export actions to session history
**Files**
- Modify: `src/switchedonvoice/ui/progress_panel.py`
- Modify: `src/switchedonvoice/ui/main_window.py`
- Test: `tests/ui/test_progress_panel.py`

**Work**
- Add `Export session` affordance in the Progress/session history UI.
- Support `.sov-session` and PDF save flows.
- Thread export notes input into the report payload.

**Acceptance criteria**
- Users can export any session from history.
- The selected format determines the generated artifact correctly.
- Export UI handles cancellation without side effects.

### Task 3.2 — Final validation across export, viewer, and fallback modes
**Files**
- Modify: `tests/reports/test_html_renderer.py`
- Modify: `tests/reports/test_package_io.py`
- Modify: `tests/reports/test_pdf_export.py`
- Modify: `tests/ui/test_session_report_viewer.py`

**Work**
- Add corrupt-package, missing-JSON, and fallback-renderer tests.
- Run manual QA on Linux for PDF readability and pagination.

**Acceptance criteria**
- HTML snapshot, ZIP round-trip, PDF smoke, and viewer-load tests all pass.
- Missing/corrupt `session.json` never crashes the app.
- Manual QA records whether Qt PDF output is sufficient or the fallback path
  should be enabled.

## Test Strategy

- Pure report rendering tests first.
- Packaging tests for ZIP structure and round-trip safety.
- UI tests for viewer loading and export actions.
- Manual QA for Linux PDF fidelity because automated smoke tests cannot fully
  judge readability.

**Suggested commands**
```bash
pytest tests/reports/test_html_renderer.py tests/reports/test_package_io.py -q
QT_QPA_PLATFORM=offscreen pytest tests/reports/test_pdf_export.py tests/ui/test_session_report_viewer.py -q
QT_QPA_PLATFORM=offscreen pytest tests/ui/test_progress_panel.py -q
pytest -q
```

## Completion Criteria

- `Export session` produces valid `.sov-session` packages.
- PDF export succeeds with readable multi-section output.
- Viewer opens exported packages without DB access.
- WebEngine absence is handled gracefully with a fallback renderer.
- Corrupt/missing `session.json` produces a clear, non-crashing error path.
