---
phase: 06-curriculum-schema
plan: 01
type: execute
wave: multi
depends_on:
  - 04-acoustic-overlay
  - 05-recording-playback
files_modified:
  - src/switchedonvoice/storage/db.py
  - src/switchedonvoice/storage/curriculum.py
  - src/switchedonvoice/curriculum/models.py
  - src/switchedonvoice/curriculum/logic.py
  - src/switchedonvoice/curriculum/levels.py
  - src/switchedonvoice/curriculum/service.py
  - tests/storage/test_db.py
  - tests/curriculum/test_logic.py
  - tests/curriculum/test_service.py
autonomous: true
requirements:
  - REQ-C01
  - REQ-C05
must_haves:
  truths:
    - "Database schema version advances by exactly one from the schema version present when Phase 6 starts (expected baseline: 4 if upstream phases remain unchanged)"
    - "Exactly 15 skills are seeded across 5 categories with an acyclic dependency graph"
    - "CurriculumService.award_xp() appends one xp_events row and get_user_xp() returns SUM(xp_amount) for the profile"
    - "get_level(xp) returns the highest configured threshold <= xp and clamps above-max XP to level 24"
    - "Service tests validate unlocks and XP totals without direct SQL in the test body"
  artifacts:
    - path: "src/switchedonvoice/storage/db.py"
      provides: "Schema migration with curriculum tables"
      contains: "_CURRENT_SCHEMA_VERSION"
    - path: "src/switchedonvoice/curriculum/service.py"
      provides: "CurriculumService API"
      exports:
        - "class CurriculumService"
    - path: "src/switchedonvoice/curriculum/levels.py"
      provides: "24-level ladder with names and flavour text"
    - path: "tests/curriculum/test_service.py"
      provides: "Service-level verification without direct DB access"
  key_links:
    - from: "src/switchedonvoice/curriculum/service.py"
      to: "src/switchedonvoice/storage/curriculum.py"
      via: "repository methods only; no SQL in service"
      pattern: "from switchedonvoice.storage.curriculum import"
    - from: "src/switchedonvoice/storage/curriculum.py"
      to: "src/switchedonvoice/storage/db.py"
      via: "get_connection(db_path) per-call open/close"
      pattern: "from switchedonvoice.storage.db import get_connection"
    - from: "src/switchedonvoice/curriculum/logic.py"
      to: "src/switchedonvoice/curriculum/levels.py"
      via: "pure level lookup over static definitions"
      pattern: "LEVEL_DEFINITIONS"
---

<objective>
## Objective

Create the curriculum domain layer: schema, seed data, XP event accounting,
level lookup, and a `CurriculumService` API that future phases can call
without writing SQL.

Output: migrated storage schema, seeded curriculum definitions, and tested
service APIs ready for Skill Tree UI, Daily Goals, Evaluation Mode, and
Recommendations.
</objective>

<execution_context>
@~/.copilot/get-shit-done/workflows/execute-plan.md
@~/.copilot/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/06-curriculum-schema/06-CONTEXT.md
@src/switchedonvoice/storage/db.py
@src/switchedonvoice/storage/sessions.py
@src/switchedonvoice/storage/settings.py
@tests/storage/test_db.py
</context>

<interfaces>
## Interfaces and conventions

- Storage modules use `structlog` and the existing per-call `get_connection(db_path)`
  pattern; they do not keep long-lived SQLite connections.
- `CurriculumService` owns orchestration only. SQL stays in
  `storage/curriculum.py`; DAG traversal and level lookup stay pure in
  `curriculum/logic.py`.
- Stable public methods required by downstream phases:
  - `get_unlocked_skills(profile_id: int | None) -> list[SkillState]`
  - `evaluate_skill_unlock(profile_id: int | None, skill_id: str) -> SkillUnlockResult`
  - `get_user_xp(profile_id: int | None) -> int`
  - `award_xp(profile_id: int | None, source_type: str, source_id: str, amount: int) -> None`
  - `get_level(xp: int) -> LevelDefinition`
- Missing skill IDs should raise `ValueError(f"Unknown skill_id: {skill_id}")`.
- XP is repeatable by design. Do not add a unique constraint on
  (`profile_id`, `source_type`, `source_id`). Callers control when awards happen.
</interfaces>

<threat_model>
## Threat model

- **Tampered criteria JSON:** parse only a small trusted rule vocabulary from seeded
  code definitions; reject unknown operators loudly.
- **SQLite NULL uniqueness traps:** avoid `INSERT OR REPLACE` for nullable
  `profile_id`; prefer explicit `UPDATE`/`INSERT` logic where necessary.
- **Double-award bugs:** keep XP as append-only events and write tests proving one
  service call equals one row, while repeated real completions remain allowed.
</threat_model>

<file_map>
## File Map

### Create
- `src/switchedonvoice/curriculum/__init__.py`
- `src/switchedonvoice/curriculum/models.py`
- `src/switchedonvoice/curriculum/logic.py`
- `src/switchedonvoice/curriculum/levels.py`
- `src/switchedonvoice/curriculum/service.py`
- `src/switchedonvoice/storage/curriculum.py`
- `tests/curriculum/__init__.py`
- `tests/curriculum/test_logic.py`
- `tests/curriculum/test_service.py`

### Modify
- `src/switchedonvoice/storage/db.py`
- `tests/storage/test_db.py`
</file_map>

<waves>
## Wave Plan

### Wave 1 (parallel) — Schema and pure domain definitions

#### Task 1: Add curriculum tables and migration path
**Files:** `src/switchedonvoice/storage/db.py`, `tests/storage/test_db.py`

**Description:**
Add the next schema version after the version present when Phase 6 starts
(expected `4` if earlier plans stay unchanged) with `skills`,
`skill_dependencies`, `user_skill_progress`, `exercises`, and `xp_events`. Use
a new independent `if version < NEXT_VERSION:` block and never reorder older
migrations.

**Acceptance criteria:**
- fresh DBs create all five tables
- migrated DBs remain idempotent
- new tables include `profile_id` where appropriate
- `skills.id` and `exercises.id` are stable text primary keys
- criteria JSON uses the provisional Phase 4 target bands with 3 / 5 / 8
  qualifying-session gates for entry / intermediate / advanced tiers

**Automated verify:**
- `pytest tests/storage/test_db.py -q`
- add assertions for `PRAGMA user_version == previous_version + 1`, expected
  tables, and nullable single-profile `profile_id` behaviour

#### Task 2: Define seed data and level ladder in pure Python
**Files:** `src/switchedonvoice/curriculum/models.py`, `src/switchedonvoice/curriculum/levels.py`

**Description:**
Encode the fifteen skills, dependency edges, exercise catalog, and the 24 level
thresholds with names and flavour text. Include the fixed IDs chosen in the
context doc so later phases can deep-link safely.

**Acceptance criteria:**
- exactly 15 seeded skills across 5 categories × 3 tiers
- dependency list is acyclic and matches the chosen forest DAG
- exercise seed IDs include `analysis-free-practice`, `reading-passage-complete`,
  `evaluation-complete`, and the planned arcade IDs from the context doc
- exactly 24 levels exist and thresholds are strictly increasing
- flavour text is present for every level

**Automated verify:**
- `pytest tests/curriculum/test_logic.py -q`
- pure tests assert skill count, edge count, acyclicity, and level threshold order

### Wave 2 (depends on Wave 1) — Repository and service contracts

#### Task 3: Implement curriculum repository operations
**Files:** `src/switchedonvoice/storage/curriculum.py`

**Description:**
Add storage helpers for seeding definitions, reading skill graphs, loading and
updating user progress, inserting XP events, and summing XP by profile.
Repository code owns SQL only.

**Acceptance criteria:**
- repository seeds tables idempotently
- repository returns dependency edges and skill metadata for the service
- repository inserts append-only XP rows and sums totals by profile
- repository supports nullable/single-profile usage without duplicate state

**Automated verify:**
- `pytest tests/curriculum/test_service.py -q`
- include first-use seeding and repeated service initialisation cases

#### Task 4: Implement pure DAG + level logic
**Files:** `src/switchedonvoice/curriculum/logic.py`

**Description:**
Add pure functions for prerequisite lookup, transitive availability, unlock
eligibility evaluation from criteria dictionaries, and XP-to-level mapping.

**Acceptance criteria:**
- graph traversal rejects or safely handles cycles in tests
- unlocking a prerequisite makes the dependent skill available
- `get_level(xp)` returns the highest level whose threshold is `<= xp`
- boundary behaviour is explicit for 0 XP, exact thresholds, and overflow XP

**Automated verify:**
- `pytest tests/curriculum/test_logic.py -q`

#### Task 5: Implement `CurriculumService`
**Files:** `src/switchedonvoice/curriculum/service.py`, `src/switchedonvoice/curriculum/__init__.py`

**Description:**
Build the public API required by downstream phases. The service seeds
definitions on first use, hides repository details, and returns typed results.

**Acceptance criteria:**
- service methods hide repository details from callers
- XP awards create one event row per call
- service returns deterministic unlock state from persisted data
- invalid skill IDs raise a clear `ValueError`

**Automated verify:**
- `pytest tests/curriculum/test_service.py -q`

### Wave 3 (depends on Wave 2) — Automated verification

#### Task 6: Add logic tests
**Files:** `tests/curriculum/test_logic.py`

**Description:**
Cover DAG traversal, acyclicity guards, unlock availability, and level
boundaries with pure-function tests.

**Acceptance criteria:**
- no SQLite or filesystem needed
- exact threshold assertions for at least level 1, 2, 12, 24, and above-max XP
- a cycle fixture proves the logic fails loudly rather than looping forever

**Automated verify:**
- `pytest tests/curriculum/test_logic.py -q`

#### Task 7: Add service tests with temp SQLite DBs
**Files:** `tests/curriculum/test_service.py`

**Description:**
Cover first-use seeding, XP accumulation, skill unlock evaluation, and service
read APIs. Tests use tmp-path DBs and call only the service surface.

**Acceptance criteria:**
- `award_xp()` increases `get_user_xp()` totals correctly
- unlocking a prerequisite skill changes dependent availability
- seeded skill count and exercise count are visible through service helpers
- tests do not query tables directly except storage-layer tests in
  `tests/storage/test_db.py`

**Automated verify:**
- `pytest tests/curriculum/test_service.py -q`
- `pytest -q`
</waves>

<test_strategy>
## Test Strategy

### Target commands
- `pytest tests/storage/test_db.py tests/curriculum/test_logic.py tests/curriculum/test_service.py -q`
- `pytest -q`

### Key test cases
- level lookup at exact boundaries and one-XP-below boundaries
- transitive unlock availability after satisfying entry-tier prerequisites
- repeatable XP accumulation from repeated real exercise completions
- seed idempotency on repeated service initialisation
- invalid skill lookup and malformed criteria JSON fail loudly
</test_strategy>

<edge_cases>
## Edge Case Notes

- `profile_id=None` must behave as a single logical profile until multi-profile
  ships; tests should pin that behaviour.
- Empty histories should still return seeded locked/available skills and level 1.
- XP above the level-24 threshold clamps to level 24.
- Unlock criteria tolerate missing Phase 4 metrics and return "not yet unlocked"
  rather than crashing.
</edge_cases>

<completion_criteria>
## Completion Criteria

Phase 6 is complete when:
- curriculum tables migrate cleanly and seed idempotently
- the service can return unlocked skills and XP totals for the active profile
- the 24-level ladder is implemented with names + flavour text
- tests prove DAG traversal, unlock logic, XP accumulation, and level
  boundaries without direct DB access from the service test layer
- full `pytest -q` still passes
</completion_criteria>

<output>
## Output

When implementation completes, create `.planning/phases/06-curriculum-schema/06-SUMMARY.md`
using the standard summary template and update ROADMAP status accordingly.
</output>
