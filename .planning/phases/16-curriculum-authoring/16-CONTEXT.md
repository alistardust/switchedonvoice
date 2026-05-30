# Phase 16: Curriculum Authoring - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 16 introduces coach-authored structured curricula that can be built,
exported, and imported entirely offline. The core deliverables are:

- a coach-only curriculum builder UI,
- persisted custom passages,
- measurable target definitions,
- a portable `.sov-curriculum` package format,
- safe import/export semantics.

This phase should not redesign the curriculum engine from Phase 6. It extends
that schema with authoring, serialization, and coach workflow tooling.
</domain>

<decisions>
## Key Decisions

### D-16-01: `.sov-curriculum` is a ZIP package with a strict manifest
The package should be analogous to `.sov-book`: human-inspectable, explicit,
and stable across machines. Use a ZIP container with this layout:

```text
lesson.sov-curriculum
├── manifest.json
└── custom_passages/
    ├── custom-001.txt
    └── custom-002.txt
```

`manifest.json` schema v1:

```json
{
  "schema_version": 1,
  "title": "Week 1 Resonance Reset",
  "author_name": "Coach Mira",
  "created_at": "2026-05-30T12:00:00Z",
  "items": [
    {
      "item_id": "instruction-001",
      "position": 1,
      "item_type": "instruction_block",
      "title": "Warm-up",
      "instruction_text": "Read slowly and stay relaxed.",
      "target_id": null
    },
    {
      "item_id": "passage-001",
      "position": 2,
      "item_type": "built_in_passage",
      "title": "Alice Chapter 1 Passage 3",
      "passage_slug": "alice-wonderland/ch01/p03",
      "target_id": "target-avg-f0"
    },
    {
      "item_id": "custom-001",
      "position": 3,
      "item_type": "custom_passage",
      "title": "Phone Script",
      "custom_passage_ref": "custom_passages/custom-001.txt",
      "target_id": null
    },
    {
      "item_id": "exercise-001",
      "position": 4,
      "item_type": "exercise",
      "title": "Pitch Ladder",
      "exercise_slug": "pitch-ladder",
      "target_id": "target-cpp"
    }
  ],
  "targets": {
    "target-avg-f0": {
      "metric": "avg_f0",
      "operator": ">=",
      "value": 180.0,
      "unit": "Hz",
      "consecutive_sessions": 1
    },
    "target-cpp": {
      "metric": "cpp",
      "operator": ">=",
      "value": 0.8,
      "unit": "CPP",
      "consecutive_sessions": 3
    }
  }
}
```

Manifest rules:

- `schema_version` is mandatory and versioned from day one.
- `item_id` and `target_id` are package-local stable identifiers, not DB IDs.
- Built-in content references use `passage_slug` or `exercise_slug`, never local
  integer IDs.
- Custom passage bodies live in separate `.txt` files referenced by
  `custom_passage_ref`.

### D-16-02: Keep custom passage storage simple and profile-owned
Persist custom passages in a dedicated table:

```sql
custom_passages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL
)
```

Imported custom passages should be recreated under the importing profile with new
local IDs. The package format must not expose or depend on source-machine DB IDs.

### D-16-03: Authored curricula need explicit DB tables
Persist coach-built curricula in normalized profile-owned tables so ordering,
editing, and export are deterministic even before packaging:

```sql
curricula(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('coach_authored', 'imported'))
);

curriculum_items(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    curriculum_id INTEGER NOT NULL REFERENCES curricula(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    item_type TEXT NOT NULL CHECK (item_type IN ('instruction_block', 'built_in_passage', 'custom_passage', 'exercise')),
    title TEXT NOT NULL,
    passage_slug TEXT,
    exercise_slug TEXT,
    custom_passage_id INTEGER REFERENCES custom_passages(id) ON DELETE SET NULL,
    instruction_text TEXT,
    target_json TEXT
);
```

If Phase 6 already created equivalent tables under different names, extend those
existing tables to this normalized shape rather than creating duplicates.

### D-16-04: Import must be transactional and validate before DB writes
Package import should follow this sequence:

1. open ZIP,
2. parse and validate `manifest.json`,
3. load required custom passage files,
4. validate built-in passage/exercise references,
5. only then open a DB transaction and persist `curricula`, `curriculum_items`,
   and imported `custom_passages` rows.

If validation fails at any point, rollback everything and surface a clear error.

### D-16-05: Authoring is coach-only, but import must be available to students
The `Build Curriculum` entry point should live in Settings for coach profiles
only and open `CurriculumBuilderWindow`. Student profiles must not see coach
authoring controls.

`Import Curriculum`, however, must be available to any profile type because the
package handoff workflow is coach exports → student imports on another machine or
profile.

### D-16-06: Ordering must be persisted explicitly
Drag-and-drop ordering should never depend on widget row order alone. Persist an
explicit `position` field for curriculum items so export/import round-trips are
deterministic.

### D-16-07: Target evaluation should be pure logic
Comparison logic (`avg_f0 >= 180`, `CPP >= 0.8 for 3 sessions`) should live in a
pure evaluator module, not inside widgets or DB code. This keeps testing cheap
and makes homework/analytics reuse straightforward.
</decisions>

<architecture_fit>
## Architecture Fit

- Storage additions stay in `src/switchedonvoice/storage/`.
- Serialization/import/export logic should live outside Qt widgets, e.g.
  `src/switchedonvoice/curriculum/package_io.py`.
- Target evaluation should be a pure module under `src/switchedonvoice/curriculum/`
  or `src/switchedonvoice/gamification/` so later phases can reuse it.
- UI code belongs in `src/switchedonvoice/ui/` and should only orchestrate user
  interaction, not own manifest logic.
</architecture_fit>

<pitfalls>
## Pitfalls

- **Local IDs:** never serialize DB primary keys into `.sov-curriculum`.
- **Partial import:** a malformed ZIP must not leave half-created curriculum rows.
- **Ordering drift:** drag-drop order must match saved/exported order exactly.
- **Reference validation:** missing `passage_slug` or `exercise_slug` references
  must fail import cleanly.
- **Coach gating:** authoring UI must stay hidden for student profiles.
</pitfalls>

<dependencies>
## Dependencies and Canonical References

- `.planning/ROADMAP.md` §Phase 16
- `.planning/REQUIREMENTS.md` §REQ-C01, §REQ-I02, §REQ-I04
- `.planning/phases/15-multi-profile/15-CONTEXT.md`
- `src/switchedonvoice/storage/db.py`
- `src/switchedonvoice/curriculum/service.py`
- `src/switchedonvoice/storage/books.py`
- `src/switchedonvoice/ui/settings_panel.py`

This phase assumes stable `passage_slug` usage from the earlier reading/curriculum
work. Do not replace slug-based identity with local integer IDs.
</dependencies>

<open_questions>
## Open Questions

- Non-blocking: whether import should deduplicate by `(title, created_at)` or
  always create a fresh curriculum row. Recommendation: always import as new,
  avoid silent overwrite.
- Non-blocking: whether instruction blocks support rich text or plain text only.
  Recommendation: plain text in v1 for portability.

No blocking questions remain for planning.
</open_questions>

---

*Phase: 16-curriculum-authoring*
*Context gathered: 2026-05-30 for plan authoring*
