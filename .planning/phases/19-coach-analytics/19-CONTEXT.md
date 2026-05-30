# Phase 19: Coach Analytics View - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 19 is the first genuinely coach-centric analytics surface. It should let a
coach inspect one student's training journey over time, annotate sessions, and
export a multi-page progress report.

The phase depends on prior profile isolation, homework attribution, and session
report infrastructure. It is primarily a read-heavy analytics/reporting phase,
with one write feature: coach session notes.
</domain>

<decisions>
## Key Decisions

### D-19-01: Analytics live on the coach Progress tab
Do not fork a separate app mode. Extend the existing Progress area so coach
profiles can switch from their own summary/history into a coach analytics
workspace with a student selector. Use `pyqtgraph` for the in-app trend charts
so the analytics view matches the rest of the Qt-native plotting stack.

### D-19-02: Weekly aggregation is an 8-week rolling window with explicit buckets
The F0 trend and resonance chart should aggregate into explicit weekly buckets
for the last 8 weeks, including empty weeks where needed. Use a pure analytics
module so date bucketing is testable without Qt.

The weekly F0 chart should also render a target-range band overlay using a
shared analytics constant, not widget-local magic numbers, so the same band can
be reused in the dashboard and exported PDF.

The same analytics layer should expose curriculum/homework completion rate from
Phase 17 assignment data so the coach sees both acoustic progress and assignment
completion in one dashboard.

### D-19-03: F0 trend uses session summaries; resonance uses evaluation/history data
- Weekly F0 trend should use saved session/evaluation summary data (`avg_f0`).
- Resonance improvement should compute weekly F1/F2 centroid distance from the
  existing feminine vowel-space centre already encoded in
  `src/switchedonvoice/ui/vowel_space.py`: `F1 = 450 Hz`, `F2 = 1800 Hz`.
  That value is already the app's canonical feminine reference ellipse centre and
  should be promoted into a shared inner-layer constants module such as
  `src/switchedonvoice/analytics/constants.py` for analytics/reporting reuse.

The reference point should be a named constant in code, not a magic number.

### D-19-04: `First vs. Now` is keyed by stable `passage_slug`
Comparisons must use the oldest and most recent evaluation/session for the same
`passage_slug`. Do not compare arbitrary sessions with mismatched content.
The panel should show Phase 18 waveform thumbnails side by side alongside the
score table and delta badges so coaches can compare both numbers and shape.

### D-19-05: Session notes belong to the coach profile
Persist notes in:

```sql
session_notes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    note_text TEXT NOT NULL,
    created_at TEXT NOT NULL
)
```

`profile_id` is the note author's profile (the coach). This allows multiple local
coaches to annotate the same student session independently.

### D-19-06: PDF export should reuse Phase 18 infrastructure
The student progress PDF should be built on the same rendering/export pipeline as
Phase 18, not via a one-off PDF generator. This keeps HTML/PDF output consistent
and reduces duplicate chart-export logic.
</decisions>

<architecture_fit>
## Architecture Fit

- Add pure analytics/date-bucketing helpers under `src/switchedonvoice/analytics/`.
  Create `src/switchedonvoice/analytics/` as a new pure-logic package (no Qt
  imports) consistent with the existing `gamification/` and `health/` inner-layer
  pattern. Put shared analytics constants there as well so inner layers do not
  import from `ui/`.
- Add storage helpers for session notes under `src/switchedonvoice/storage/`.
- Keep coach dashboard UI in `src/switchedonvoice/ui/coach_analytics_panel.py`.
- Reuse report/export modules from Phase 18 for the student progress PDF.
</architecture_fit>

<pitfalls>
## Pitfalls

- **Bucket correctness:** week boundaries and sparse weeks are easy to get wrong.
- **Passage identity:** `First vs. Now` must compare like-for-like by
  `passage_slug`.
- **Role filtering:** coach dashboards should target student data without hiding
  valid coach-owned notes.
- **Multiple coaches:** note visibility and ownership must filter by coach
  `profile_id`.
- **PDF size:** multi-page export needs page-break-aware layout, not a single
  long scrolling HTML dump.
</pitfalls>

<dependencies>
## Dependencies and Canonical References

- `.planning/ROADMAP.md` §Phase 19
- `.planning/REQUIREMENTS.md` §REQ-I06
- `.planning/phases/15-multi-profile/15-CONTEXT.md`
- `.planning/phases/17-homework-assignment/17-CONTEXT.md`
- `.planning/phases/18-session-reports/18-CONTEXT.md`
- `src/switchedonvoice/ui/progress_panel.py`
- `src/switchedonvoice/storage/sessions.py`
- `src/switchedonvoice/storage/evaluations.py`

This phase assumes `passage_slug` is already the stable identity for historical
comparisons.
</dependencies>

<open_questions>
## Open Questions

- Non-blocking: whether the student selector includes coach profiles or defaults
  to student profiles only. Recommendation: show all profiles but visually mark
  coaches and default selection to students.
- Non-blocking: whether coaches can edit existing notes or append-only in v1.
  Recommendation: allow edit/delete for the authoring coach only if the storage
  API remains simple; otherwise start append-only.

No blocking questions remain for planning.
</open_questions>

---

*Phase: 19-coach-analytics*
*Context gathered: 2026-05-30 for plan authoring*
