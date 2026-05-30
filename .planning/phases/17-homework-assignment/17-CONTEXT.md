# Phase 17: Homework Assignment - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 17 turns authored curriculum content into assignable homework for specific
student profiles. The feature set is broader than one table: it includes coach
assignment UI, student-facing visibility, completion tracking, and coach report
aggregation.

The critical design rule is that homework must be tracked separately from free
practice while still reusing the existing session/evaluation pipeline.
</domain>

<decisions>
## Key Decisions

### D-17-01: `homework` is the assignment header; item state lives in `items_json`
The required table is:

```sql
homework(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coach_profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    student_profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    assigned_at TEXT NOT NULL,
    due_date TEXT,
    items_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'partial', 'complete'))
)
```

`items_json` should be explicit, not ad-hoc. Recommended per-item shape:

```json
[
  {
    "item_key": "passage-001",
    "item_type": "passage",
    "title": "Alice Chapter 1 Passage 3",
    "passage_slug": "alice-wonderland/ch01/p03",
    "status": "pending",
    "completed_session_id": null,
    "completed_at": null,
    "score_snapshot": null
  }
]
```

This keeps the homework row self-contained while still supporting report output.

### D-17-02: Sessions need homework attribution fields
To label history as `Homework` vs `Free practice` cleanly, extend `sessions` with
nullable attribution fields such as:

- `practice_context` (`free_practice` / `homework`)
- `homework_id`
- `homework_item_key`

Migration shape:

```sql
ALTER TABLE sessions ADD COLUMN practice_context TEXT DEFAULT 'free_practice';
ALTER TABLE sessions ADD COLUMN homework_id INTEGER REFERENCES homework(id);
ALTER TABLE sessions ADD COLUMN homework_item_key TEXT;
PRAGMA user_version = <next version>;
```

That preserves the normal session pipeline while making session history and
coach reports straightforward.

### D-17-03: Completion is driven by explicit homework launches
A session should only mark homework progress when it was started from a homework
"Start" deep-link or equivalent explicit assignment context. Free-practice work
on the same passage should remain free practice unless the student deliberately
starts the assigned item.

### D-17-04: Coach-to-student assignment stays local-machine only
Homework rows link one local coach profile to one local student profile. This is
not multi-device sync. A machine may contain multiple coaches and students; the
row itself is the source of truth for ownership and visibility.

### D-17-05: Student home-screen surfacing belongs on the Analysis tab
The "Assigned by your coach" section should appear on the student landing view
where they already begin a live session. It should be absent when no homework is
pending.

### D-17-06: Reporting should aggregate from assignment + sessions, not UI state
Coach reports need completion percentage, completion date, and achieved acoustic
scores. That aggregation must happen in a storage/service layer, not be rebuilt
inside the widget tree.
</decisions>

<architecture_fit>
## Architecture Fit

- Add storage helpers in `src/switchedonvoice/storage/homework.py`.
- Add orchestration/business rules in `src/switchedonvoice/services/homework_service.py`.
- Keep student and coach UI separate: a student-facing homework summary panel and
  a coach-facing student-management/report panel.
- Reuse existing session close flow; inject homework context into session
  creation/closure rather than bypassing the session pipeline.
</architecture_fit>

<pitfalls>
## Pitfalls

- **Silent completion leakage:** free-practice sessions must not auto-complete
  homework unless launched from homework context.
- **JSON drift:** `items_json` needs a stable schema with tests; do not let
  widgets mutate anonymous dict blobs.
- **Student visibility:** only the assigned student should see the assignment.
- **Coach visibility:** reports must filter by both `coach_profile_id` and
  `student_profile_id`.
- **Due dates:** use ISO local-date strings consistently; do not mix timezone
  offsets into a date-only field.
</pitfalls>

<dependencies>
## Dependencies and Canonical References

- `.planning/ROADMAP.md` §Phase 17
- `.planning/REQUIREMENTS.md` §REQ-I03
- `.planning/phases/15-multi-profile/15-CONTEXT.md`
- `.planning/phases/16-curriculum-authoring/16-CONTEXT.md`
- `src/switchedonvoice/storage/sessions.py`
- `src/switchedonvoice/ui/main_window.py`
- `src/switchedonvoice/ui/analysis_panel.py`
- `src/switchedonvoice/ui/progress_panel.py`

Homework depends on profile-aware repositories and curriculum/package content
already being stable.
</dependencies>

<open_questions>
## Open Questions

- Non-blocking: whether overdue homework gets special colour treatment or only a
  date badge. Recommendation: date badge first; styling can come later.
- Non-blocking: whether coaches may assign whole curricula in one click, or only
  individual items in v1. Recommendation: support both only if the existing
  curriculum service already exposes clean item expansion; otherwise start with
  explicit item selection.

No blocking questions remain for the plan.
</open_questions>

---

*Phase: 17-homework-assignment*
*Context gathered: 2026-05-30 for plan authoring*
