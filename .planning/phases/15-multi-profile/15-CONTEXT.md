# Phase 15: Multi-Profile Support - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 15 retrofits profile-awareness across the existing local-only app. The core
work is not the switcher UI; it is the migration from a single-user SQLite model
to a profile-scoped model without losing any pre-existing history.

This phase must isolate all persisted training/progress data per profile while
keeping machine-level settings shared. That is an intentional product
clarification: `settings.json` remains per-machine, but sessions, curriculum
state, homework, evaluations, arcade history, and reading progress all become
profile-scoped.

Coach profiles are a capability flag for later instructor features. They are not
an authentication or permission boundary. The machine remains trusted-local-use
only.
</domain>

<decisions>
## Key Decisions

### D-15-01: Canonical profile-scoped tables
The migration must add a `profiles` table and a `profile_id` foreign key to
exactly these user-scoped tables:

- `sessions`
- `reading_progress`
- `arcade_scores`
- `xp_events`
- `user_skill_progress`
- `daily_goals`
- `evaluations`

Tables that are **not** profile-scoped in this phase:

- `frames` — inherits ownership through `sessions.session_id`
- content tables such as `books`, `chapters`, `passages`
- machine-level `settings.json`

### D-15-02: Migration must rebuild final schemas, not just append columns
SQLite `ALTER TABLE ... ADD COLUMN` is not sufficient for the final schema here,
because the target state needs non-null `profile_id`, foreign keys, updated
uniqueness constraints, and predictable cascade behavior. The safest pattern is:

```sql
BEGIN;

CREATE TABLE profiles (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    profile_type TEXT NOT NULL CHECK (profile_type IN ('student', 'coach')),
    created_at TEXT NOT NULL,
    avatar_colour TEXT NOT NULL
);

INSERT INTO profiles (id, name, profile_type, created_at, avatar_colour)
VALUES (1, 'Me', 'student', '2026-05-30T00:00:00Z', '#7C4DFF');

CREATE TABLE sessions_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    duration_secs REAL,
    avg_f0 REAL,
    f0_std_dev REAL,
    avg_f2 REAL,
    milestone_flags_json TEXT DEFAULT '{}'
);
INSERT INTO sessions_new (id, profile_id, date, duration_secs, avg_f0, f0_std_dev, avg_f2, milestone_flags_json)
SELECT id, 1, date, duration_secs, avg_f0, f0_std_dev, avg_f2, milestone_flags_json
FROM sessions;
DROP TABLE sessions;
ALTER TABLE sessions_new RENAME TO sessions;

-- Repeat the same create-copy-drop-rename pattern for:
-- reading_progress, arcade_scores, xp_events, user_skill_progress,
-- daily_goals, evaluations.

CREATE INDEX idx_sessions_profile_date ON sessions(profile_id, date DESC);
-- Recreate every affected uniqueness/index using profile_id as part of the key.

PRAGMA user_version = <next version>;
COMMIT;
```

Rules for the migration:

1. Preserve primary keys where downstream tables reference them.
2. Backfill every legacy row to `profile_id = 1`.
3. Recreate indexes/unique constraints so they are profile-aware.
4. Keep the migration in `storage/db.py` as a new `if version < N:` block.
5. Do not reorder old migrations.

### D-15-03: Zero-data-loss verification is part of the deliverable
The migration is not done until these checks pass on a copy of a populated
pre-phase-15 database:

```sql
SELECT COUNT(*) = 1 FROM profiles WHERE id = 1 AND name = 'Me' AND profile_type = 'student';
SELECT COUNT(*) FROM sessions WHERE profile_id IS NULL;
SELECT COUNT(*) FROM reading_progress WHERE profile_id IS NULL;
SELECT COUNT(*) FROM arcade_scores WHERE profile_id IS NULL;
SELECT COUNT(*) FROM xp_events WHERE profile_id IS NULL;
SELECT COUNT(*) FROM user_skill_progress WHERE profile_id IS NULL;
SELECT COUNT(*) FROM daily_goals WHERE profile_id IS NULL;
SELECT COUNT(*) FROM evaluations WHERE profile_id IS NULL;
```

And the test harness must compare pre/post row counts for each migrated table.
For `sessions`, verify frame linkage still works by confirming every `frames`
row joins to a session row after migration.

### D-15-04: Active profile is machine state, not DB state
The current active profile should live in `settings.json` as
`active_profile_id`. That choice matches the existing machine-scoped settings
model and avoids a global singleton table in SQLite.

If the saved active profile no longer exists, startup must fall back to profile
`1` and rewrite settings.

### D-15-05: Profile context must be explicit in repositories and UI
No storage or service layer should infer a "current profile" implicitly. Every
profile-scoped repository/service API must accept `profile_id` explicitly.
`MainWindow` owns the selected profile and passes it downward.

This is the key leak-prevention rule for the phase.

### D-15-06: Switching profile rotates the active session cleanly
The current app auto-starts a session at window open. Therefore switching
profiles mid-run cannot just swap labels; it must:

1. close the current session under the old profile,
2. clear in-memory acoustic history/state,
3. start a fresh session under the new profile,
4. refresh visible panels against the new profile.

Do not let one live session span two profiles.

### D-15-07: Deletion semantics must rely on FK cascades
A non-active profile delete should remove the profile row and all dependent DB
rows via `ON DELETE CASCADE`. If recordings/history files exist by this point in
the roadmap, the implementation must also delete the profile-owned recording
subtree after the DB delete succeeds.

The active profile cannot be deleted.

### D-15-08: UI copy must state the trust boundary clearly
The create/edit dialog and switcher help text should explicitly say profiles are
for local organisation only and are not password-protected. The coach badge is a
UI affordance for feature gating, not a security role.
</decisions>

<architecture_fit>
## Architecture Fit

- `src/switchedonvoice/storage/db.py` remains the only place where schema
  migration rules live.
- Add a dedicated `src/switchedonvoice/storage/profiles.py` repository rather
  than overloading `sessions.py`.
- `src/switchedonvoice/ui/main_window.py` owns the active profile and creates
  profile-scoped panels/repositories.
- Existing panels that query data (`ProgressPanel`, later curriculum/homework
  panels) need a `set_profile(...)` or equivalent refresh boundary.
- Settings stay per-machine; profile-specific training data stays in SQLite.
</architecture_fit>

<pitfalls>
## Pitfalls

- **Frames table:** do not add `profile_id` to `frames`; ownership comes from the
  parent session row.
- **Composite uniqueness:** any uniqueness that used to be global must be
  rebuilt as `(profile_id, ...)` uniqueness where appropriate.
- **Session close ordering:** preserve the existing `close_session()` →
  `get_history_stats()` → `evaluate_milestones()` ordering during switch and app
  close.
- **UI leak risk:** one missing `WHERE profile_id = ?` in a repository will leak
  cross-profile history.
- **Delete safety:** do not allow deleting the active profile or the default
  fallback profile if it is currently active.
</pitfalls>

<dependencies>
## Dependencies and Canonical References

- `.planning/ROADMAP.md` §Phase 15
- `.planning/REQUIREMENTS.md` §REQ-I01, §REQ-I04, §REQ-I06
- `src/switchedonvoice/storage/db.py`
- `src/switchedonvoice/storage/sessions.py`
- `src/switchedonvoice/storage/settings.py`
- `src/switchedonvoice/ui/main_window.py`
- `src/switchedonvoice/ui/progress_panel.py`

Downstream phases depend on this phase introducing explicit `profile_id`
contracts; do not leave temporary optional-profile APIs behind. This phase also
assumes the profile-scoped tables added across Phases 2–14 already exist, so the
migration can treat the post-Phase-14 schema as its starting point.
</dependencies>

<open_questions>
## Open Questions

- Non-blocking: choose a small fixed avatar colour palette now, or permit any Qt
  colour picker value and normalize to hex.
- Non-blocking: decide whether coach profiles appear in later student selectors
  by default, or only student profiles do.

No blocking product questions remain; the migration strategy and ownership model
are already determined.
</open_questions>

---

*Phase: 15-multi-profile*
*Context gathered: 2026-05-30 for plan authoring*
