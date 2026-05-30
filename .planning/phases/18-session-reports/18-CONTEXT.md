# Phase 18: Session Reports & File Export - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 18 turns a saved session into a portable offline artifact: HTML, PDF, and
`.sov-session` package export, plus a read-only viewer that can open that
package on another machine without touching the DB.

The phase spans reporting, asset generation, packaging, and viewer UX. It should
not depend on network access or on the source machine's live SQLite database.
</domain>

<decisions>
## Key Decisions

### D-18-01: `.sov-session` is a self-contained ZIP package
Recommended package layout:

```text
session-2026-05-30.sov-session
├── session.json
├── report.html
├── charts/
│   ├── f0_timeline.svg
│   ├── vowel_space.svg
│   └── waveform.svg
└── audio.wav          # optional
```

Recommended `session.json` v1 shape:

```json
{
  "schema_version": 1,
  "exported_at": "2026-05-30T12:00:00Z",
  "profile": {"name": "Me", "profile_type": "student"},
  "session": {
    "session_id": 42,
    "date": "2026-05-30",
    "duration_secs": 610.0,
    "passage_slug": "alice-wonderland/ch01/p03",
    "practice_context": "free_practice"
  },
  "scores": {
    "avg_f0": 188.4,
    "avg_f2": 1710.2,
    "cpp": 0.86
  },
  "assets": {
    "report_html": "report.html",
    "f0_chart": "charts/f0_timeline.svg",
    "vowel_chart": "charts/vowel_space.svg",
    "waveform_chart": "charts/waveform.svg",
    "audio": "audio.wav"
  },
  "notes": "Optional export note"
}
```

### D-18-02: Report generation should be deterministic and layered
Use a pipeline with separate responsibilities:

1. collect session/report data,
2. generate chart assets (SVG),
3. render HTML,
4. package HTML + assets into ZIP,
5. optionally print HTML to PDF.

Keep the HTML renderer pure so snapshot tests stay stable.

### D-18-03: Treat WebEngine as optional runtime capability
`QWebEngineView` is not guaranteed to be present just because `PySide6` is
installed. In split-package environments it often requires the Qt WebEngine
module (`PySide6-Addons`, distro `qt6-webengine`, or equivalent runtime libs).

Plan for capability detection:

- try `from PySide6.QtWebEngineWidgets import QWebEngineView`,
- perform a one-time guarded smoke instantiation after Qt startup,
- if both import and runtime initialization succeed, use WebEngine for rich
  report viewing,
- otherwise fall back to `QTextBrowser` rendering static HTML.

This check must catch both `ImportError` and runtime WebEngine initialization
failures common on Linux package splits. Export must not depend on WebEngine.
Viewer tests should cover the fallback path.

### D-18-04: Prefer Qt PDF export first, keep WeasyPrint optional
Primary export path: render HTML into Qt and print via `QPrinter`.

Because Linux PDF quality/pagination can vary, document a fallback backend hook
for WeasyPrint if manual QA shows unacceptable results. Do **not** make
WeasyPrint mandatory in the first implementation unless the Qt path proves
unusable.

### D-18-05: Viewer is read-only and DB-independent
Opening a `.sov-session` must never write to SQLite, settings, or the source
profile. The viewer should read `session.json`, HTML, and SVG assets directly
from the ZIP via `ZipFile.read()` wherever possible instead of `extractall()`.
If a file must be materialized for playback/viewing, write it under a dedicated
app cache path inside `~/.switchedonvoice/`, never to a system temp directory.

### D-18-06: Export notes should belong to the package payload
The report notes field in this phase is best treated as export metadata supplied
at export time. Later Phase 19 session notes can be merged into the same report
pipeline, but Phase 18 should not block on that feature.
</decisions>

<architecture_fit>
## Architecture Fit

- Create a dedicated reporting package (for example `src/switchedonvoice/reports/`).
- Keep chart generation and HTML rendering out of widgets.
- Reuse the Progress tab as the export launch point, but keep heavy export logic
  in non-UI modules.
- Viewer UI belongs in `src/switchedonvoice/ui/`, layered over the pure package
  reader and HTML renderer.
</architecture_fit>

<pitfalls>
## Pitfalls

- **QtWebEngine availability:** many test/CI systems will not have it.
- **Absolute paths:** never embed machine-local paths in exported HTML/JSON.
- **Partial package writes:** export should write the final ZIP atomically.
- **Corrupt JSON:** missing or invalid `session.json` must show a clear error and
  never crash the viewer.
- **SVG/PDF fidelity:** chart output must stay readable after PDF conversion.
</pitfalls>

<dependencies>
## Dependencies and Canonical References

- `.planning/ROADMAP.md` §Phase 18
- `.planning/REQUIREMENTS.md` §REQ-R04, §REQ-C03, §REQ-I04
- `.planning/phases/15-multi-profile/15-CONTEXT.md`
- `src/switchedonvoice/ui/progress_panel.py`
- `src/switchedonvoice/storage/sessions.py`
- `src/switchedonvoice/storage/evaluations.py`
- `pyproject.toml`

If the project later adds an optional dependency for WebEngine/PDF fallback,
document it in `pyproject.toml` and keep the viewer functional without it.
</dependencies>

<open_questions>
## Open Questions

- Non-blocking: whether the viewer opens in a dedicated top-level window or a
  modal dialog. Recommendation: dedicated window for drag-in and file-open reuse.
- Non-blocking: whether waveform rendering should use matplotlib, pyqtgraph
  export, or QPainter SVG. Recommendation: prefer the charting stack already
  present after earlier phases to avoid duplicate plotting dependencies.

No blocking questions remain for the plan.
</open_questions>

---

*Phase: 18-session-reports*
*Context gathered: 2026-05-30 for plan authoring*
