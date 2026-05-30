# Phase 6: Curriculum Data Model & Skill Tree Schema - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase adds the durable curriculum backbone for Milestone v1.2. By the
end of the phase the app can answer four questions reliably: which skills
exist, which prerequisite edges connect them, which skills are unlocked for
the current profile, and how much XP the profile has earned.

This is deliberately a data-and-service phase. It should not introduce any
visual skill tree rendering, level-up celebration UI, daily goal widgets, or
evaluation reports. Those all depend on this phase producing a stable schema
and service contract first.
</domain>

<decisions>
## Key Decisions

### Curriculum graph shape
- **D-06-01:** Start with a *forest-shaped DAG*: five category chains
  (Pitch, Resonance, Vocal Quality, Clarity, Intonation), each with three
  tiers linked entry → intermediate → advanced.
- **Reasoning:** This satisfies REQ-C01, keeps unlock logic obvious, and
  gives Phase 7 a deterministic layout without needing an auto-layout graph
  engine. Cross-category prerequisite edges are deferred until there is real
  evidence they improve pedagogy.

### Stable skill identifiers
- **D-06-02:** Store skill IDs as stable string keys (for example
  `pitch-entry`, `resonance-intermediate`) rather than numeric IDs.
- **Reasoning:** Phase 7 tooltips, Phase 10 recommendation rules, and later
  curriculum authoring/export all need human-readable identifiers that can be
  referenced safely outside a single database file.

### Unlock criteria storage
- **D-06-03:** Keep unlock rules in `unlock_criteria_json` on `skills`, with
  a small typed rule vocabulary implemented in pure Python.
- **Reasoning:** Thresholds will evolve as acoustic scoring matures. JSON
  keeps the schema forward-compatible while the evaluator stays typed and
  testable in code.

### Profile columns now, single profile behaviour now
- **D-06-04:** Every new curriculum table includes `profile_id` from day one,
  but Phase 6 treats `None` or `1` as the only active profile.
- **Reasoning:** The user explicitly wants Phase 15 multi-profile support to
  be migration-light. This phase should avoid painting the DB into a
  single-profile corner.

### XP accounting model
- **D-06-05:** `xp_events` is append-only and authoritative; user XP is
  always computed on read via `SUM(xp_amount)`.
- **Reasoning:** A write-optimised append log is simpler to audit, easier to
  test, and avoids divergence bugs between `xp_events` and a cached total.
  If performance ever becomes a real issue, Phase 15+ can add a cache layer
  without changing the API.

### Level definitions live in code, not SQLite
- **D-06-06:** The 24 level thresholds, names, and flavour text live in a
  versioned Python module (`curriculum/levels.py` or equivalent), not a DB
  table.
- **Reasoning:** Levels are product design constants, not user-authored data.
  Keeping them in code avoids migration churn and makes boundary tests
  straightforward.

### Service boundary
- **D-06-07:** Introduce a dedicated curriculum domain package with pure
  logic separated from storage access. `CurriculumService` orchestrates the
  repository and exposes the API used by future UI phases.
- **Reasoning:** The project constraints explicitly prefer business logic out
  of DB queries. Phase 7, 8, 9, 10, and 11 all need the same curriculum
  answers; centralising them now prevents duplicated SQL in UI code.

### XP duplication policy
- **D-06-08:** `xp_events` allows repeated source IDs; no DB-level unique
  constraint is added on (`profile_id`, `source_type`, `source_id`). The event
  log is append-only, and callers are responsible for awarding XP once per real
  completion.
- **Reasoning:** Exercises, passages, and future arcade content can be repeated
  intentionally. A uniqueness constraint would block legitimate repeatable XP.

### Initial unlock rule contract
- **D-06-09:** Phase 6 seeds concrete unlock criteria now using Phase 4 target
  bands plus a minimum qualifying-session gate of 3 / 5 / 8 sessions for
  entry / intermediate / advanced tiers respectively. These thresholds are
  explicitly provisional and may be tuned after real-user calibration, but they
  are not left undefined for implementation.
- **Reasoning:** Downstream UI and tests need deterministic unlock behaviour. A
  versioned provisional table is safer than an undefined one.
</decisions>

<canonical_refs>
## Canonical References

**Downstream planning and implementation work should read these first.**

### Requirements
- `.planning/REQUIREMENTS.md` — REQ-C01 and REQ-C05 are mandatory for this
  phase; REQ-C02–REQ-C04 matter only as downstream consumers

### Roadmap
- `.planning/ROADMAP.md` §Phase 6 — task list and success criteria

### Existing storage patterns
- `src/switchedonvoice/storage/db.py` — versioned migration pattern with
  `PRAGMA user_version` and independent `if version < N` blocks
- `src/switchedonvoice/storage/sessions.py` — per-call connection lifecycle
  and error handling conventions
- `src/switchedonvoice/storage/settings.py` — JSON persistence pattern for
  forward-compatible profile-scoped settings

### Prior-phase artifacts this phase depends on
- `src/switchedonvoice/storage/books.py` (Phase 2) — canonical passage slug
  source used by later evaluation and recommendation flows
- `reading_progress` schema from Phase 4 — includes `first_*` and `recent_*`
  acoustic summary fields used by unlock criteria evaluation
- Reading and recording flows from Phases 3–5 — the curriculum phase assumes
  passages and completed sessions already exist as XP sources
</canonical_refs>

<code_context>
## Architecture Fit

### Where this phase should sit
- **Storage:** new curriculum tables belong in `storage/db.py` migrations and
  low-level queries belong in a dedicated storage module
- **Pure logic:** DAG traversal, level lookup, and rule evaluation belong in a
  pure curriculum/gamification module so they can be tested without SQLite
- **UI integration:** none in this phase beyond exposing a stable service API
  for Phase 7 and later

### Existing app constraints that matter here
- Audio callback must remain append-only. Curriculum evaluation must happen on
  session boundaries or explicit service calls, never inside the callback or
  analysis thread.
- All data stays local under `~/.switchedonvoice/`; no backend assumptions or
  remote IDs should leak into the schema.
- Tests should follow the existing tmp-path SQLite style and keep Qt out of
  this phase wherever possible.

### Recommended new package split
- `src/switchedonvoice/curriculum/models.py` — dataclasses / enums / typed
  level and skill definitions
- `src/switchedonvoice/curriculum/logic.py` — pure DAG traversal, unlock
  evaluation helpers, level lookup, availability computation
- `src/switchedonvoice/curriculum/service.py` — `CurriculumService`
- `src/switchedonvoice/storage/curriculum.py` — repository functions and SQL

This keeps SQL out of the pure logic layer and prevents UI code from learning
schema details directly.
</code_context>

<seed_data>
## Canonical Seed Shape

### Skill IDs and categories
The initial fifteen skills should be seeded as five linear category tracks:

| Category | Entry | Intermediate | Advanced |
|----------|-------|--------------|----------|
| Pitch | `pitch-entry` | `pitch-intermediate` | `pitch-advanced` |
| Resonance | `resonance-entry` | `resonance-intermediate` | `resonance-advanced` |
| Vocal Quality | `quality-entry` | `quality-intermediate` | `quality-advanced` |
| Clarity | `clarity-entry` | `clarity-intermediate` | `clarity-advanced` |
| Intonation | `intonation-entry` | `intonation-intermediate` | `intonation-advanced` |

Each seeded skill needs: human name, category, tier, description, and a JSON
criteria blob referencing metrics already produced by Phase 4 (`recent_avg_f0`,
`recent_resonance_score`, `recent_cpp_score`, `completion_count`, session
consistency metrics, etc.).

### Exercise catalog direction
`exercises` should store canonical IDs for all practice sources that can award
XP or satisfy criteria. Phase 6 should seed at least:
- `analysis-free-practice`
- `reading-passage-complete`
- `evaluation-complete`
- `arcade-pitch-targeting`
- `arcade-resonance-drill`
- `arcade-vowel-shaping`
- `arcade-siren-glide`
- `arcade-rhythm-cadence`

The point is not to fully implement those producers now; it is to give XP and
recommendations stable source IDs that do not need renaming later.

### Levels
The canonical level ladder should be seeded in code with these thresholds:

| Level | XP | Name |
|------:|---:|------|
| 1 | 0 | Finding My Voice |
| 2 | 100 | Steady Breath |
| 3 | 250 | First Spark |
| 4 | 450 | Pitch Pathfinder |
| 5 | 700 | Resonance Seeker |
| 6 | 1000 | Gentle Lift |
| 7 | 1350 | Clarity Builder |
| 8 | 1750 | Tone Weaver |
| 9 | 2200 | Vowel Explorer |
| 10 | 2700 | Confidence Bloom |
| 11 | 3250 | Intonation Shaper |
| 12 | 3850 | Resonance Sculptor |
| 13 | 4500 | Flow Keeper |
| 14 | 5200 | Brightness Builder |
| 15 | 5950 | Story Carrier |
| 16 | 6750 | Voice Gardener |
| 17 | 7600 | Cadence Keeper |
| 18 | 8500 | Signal Refiner |
| 19 | 9450 | Velvet Current |
| 20 | 10450 | Harmonic Crafter |
| 21 | 11500 | Presence Maker |
| 22 | 12600 | Voice Architect |
| 23 | 13750 | Feminine Flame |
| 24 | 15000 | Vocal Alchemist |

Each level should also carry a one-line flavour string in code. Phase 7 will
surface it directly in the level-up dialog, so wording should be final enough
to ship.
</seed_data>

<pitfalls>
## Pitfalls to Avoid

- **Do not materialise `user_xp` as a mutable table** unless there is a proven
  performance problem. Double-write accounting bugs are much worse than a
  `SUM()` query over a modest event log.
- **Do not use `INSERT OR REPLACE` blindly** on tables with nullable
  `profile_id` if uniqueness matters. SQLite treats `NULL != NULL`.
- **Do not let tests query tables directly** when the requirement is to prove
  the service contract. Repository tests are fine at the storage layer, but
  Phase 6 acceptance should be service-first.
- **Do not infer unlocks from UI state.** Unlock evaluation must be driven by
  persisted passage/session metrics so the app can reopen and compute the same
  answer deterministically.
- **Do not add graph cycles in seed data.** A single bad dependency edge would
  quietly break Phase 7 rendering and Phase 10 recommendations.
</pitfalls>

<deferred>
## Deferred Ideas

- Cross-category prerequisite edges that make the graph denser than five simple
  category chains. Defer until there is real curriculum evidence they improve
  learning rather than merely adding complexity.
- Materialised XP totals or cached level snapshots. Defer until `xp_events`
  query cost is measurable and problematic.
- Author-facing skill editing UI. Curriculum authoring belongs to Phase 16.
</deferred>

<open_questions>
## Open Questions

</open_questions>

---

*Phase: 06-curriculum-schema*
*Context gathered: 2026-05-30 for planning*
