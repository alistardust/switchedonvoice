---
phase: 15-multi-profile
plan_type: phase-plan
requirements:
  - REQ-I01
depends_on:
  - Phase 14
status: ready
waves:
  - 1
  - 2
  - 3
---

# Phase 15 Plan — Multi-Profile Support

## Goal
Add multi-profile support with zero legacy data loss, profile-isolated history,
and a profile switcher/CRUD flow that becomes the foundation for coach-mode
features in Phases 16–19.

## Execution Principles

- Treat the migration as the highest-risk task in the phase.
- Keep `settings.json` machine-scoped; keep training data profile-scoped.
- Require `profile_id` explicitly in every profile-aware repository/service API.
- Preserve the existing live-session lifecycle when switching profiles.
- TDD the migration and isolation rules before building UI.

## Wave 1 — Schema migration and repository contracts

### Task 1.1 — Add the profile schema migration
**Files**
- Modify: `src/switchedonvoice/storage/db.py`
- Test: `tests/storage/test_db.py`
- Create: `tests/storage/test_profile_migration.py`

**Work**
- Add the `profiles` table.
- Rebuild `sessions`, `reading_progress`, `arcade_scores`, `xp_events`,
  `user_skill_progress`, `daily_goals`, and `evaluations` with `profile_id`
  foreign keys.
- Preserve existing primary keys while backfilling all legacy rows to profile 1.
- Bump `PRAGMA user_version` in a new `if version < N:` migration block.

**Acceptance criteria**
- A migrated legacy DB opens without error.
- Exactly one default profile exists: `id=1`, `name='Me'`, `profile_type='student'`.
- All migrated rows have `profile_id = 1`.
- Pre/post row counts match for every migrated table.
- `frames` rows still join correctly to sessions after migration.

### Task 1.2 — Create the profiles repository
**Files**
- Create: `src/switchedonvoice/storage/profiles.py`
- Test: `tests/storage/test_profiles.py`

**Work**
- Add a `Profile` dataclass and CRUD functions/repository methods for:
  `list_profiles()`, `get_profile()`, `create_profile()`, `update_profile()`,
  `delete_profile()`, `profile_exists()`.
- Enforce profile type validation (`student` / `coach`).
- Refuse to delete the active profile at the repository/service boundary.

**Acceptance criteria**
- Profile CRUD is covered by storage tests.
- Invalid types raise `ValueError`.
- Deleting a non-active profile cascades dependent rows.
- Deleting the active profile raises a clear error.

### Task 1.3 — Make repositories profile-explicit
**Files**
- Modify: `src/switchedonvoice/storage/sessions.py`
- Modify: `src/switchedonvoice/storage/books.py`
- Modify: `src/switchedonvoice/storage/evaluations.py`
- Modify: `src/switchedonvoice/storage/daily_goals.py`
- Modify: `src/switchedonvoice/storage/arcade.py`
- Modify: `src/switchedonvoice/storage/xp.py`
- Modify: `src/switchedonvoice/storage/skill_progress.py`
- Modify: `src/switchedonvoice/curriculum/service.py`
- Test: `tests/storage/test_profile_isolation.py`

**Work**
- Thread `profile_id` through all profile-scoped query and write functions,
  including the modules that own `xp_events` and `user_skill_progress`.
- In `BookRepository`, accept `profile_id` at the API boundary only where the
  repository joins or derives user-owned progress/state; keep canonical book /
  passage content tables global and unfiltered.
- Update unique lookups and list queries to filter by `profile_id` only for
  user-owned data.
- Remove temporary optional-profile code paths before the wave closes.

**Acceptance criteria**
- The compiler/type checker has no callsites using stale signatures.
- Profile A cannot read or update Profile B data through any repository.
- Existing content/global tables remain shared where intended.

## Wave 2 — Application state and profile UI

### Task 2.1 — Persist active profile selection in settings
**Files**
- Modify: `src/switchedonvoice/storage/settings.py`
- Modify: `tests/storage/test_settings.py`

**Work**
- Extend `Settings` with `active_profile_id`.
- Keep settings machine-scoped.
- On startup, fall back to profile 1 if the stored profile is missing.

**Acceptance criteria**
- Active profile survives restart.
- Missing/stale profile IDs fall back safely to profile 1.
- Existing settings tests remain green after schema extension.

### Task 2.2 — Add the profile switcher and CRUD dialog
**Files**
- Create: `src/switchedonvoice/ui/profile_switcher.py`
- Create: `src/switchedonvoice/ui/profile_dialog.py`
- Modify: `src/switchedonvoice/ui/main_window.py`
- Modify: `src/switchedonvoice/ui/settings_panel.py`
- Test: `tests/ui/test_profile_dialog.py`
- Test: `tests/ui/test_main_window.py`

**Work**
- Add a top-bar switcher showing avatar initial, name, and `(Coach)` badge.
- Add dropdown actions for switching profiles and creating a new one.
- Add create/edit/delete dialog with name, type, and avatar colour controls.
- Show copy explaining profiles are not password-protected.

**Acceptance criteria**
- App boots into the default `Me` profile on first migration.
- Coach profiles show `(Coach)` in the dropdown.
- The active profile cannot be deleted.
- Choosing “Add new profile” opens the dialog and refreshes the switcher.

### Task 2.3 — Rotate sessions and refresh panels on profile change
**Files**
- Modify: `src/switchedonvoice/ui/main_window.py`
- Modify: `src/switchedonvoice/ui/progress_panel.py`
- Modify: `src/switchedonvoice/ui/analysis_panel.py`
- Modify: `src/switchedonvoice/ui/exercise_panel.py`
- Test: `tests/ui/test_main_window.py`

**Work**
- On profile switch, close the current session under the old profile.
- Clear in-memory histories and start a new session under the new profile.
- Refresh panels so all visible data comes from the selected profile.

**Acceptance criteria**
- Switching profiles mid-run never mixes a session across two profiles.
- Progress/history panels refresh immediately.
- The current session after a switch belongs only to the newly active profile.

## Wave 3 — Verification, deletion, and regression coverage

### Task 3.1 — Test migration correctness on populated legacy fixtures
**Files**
- Modify: `tests/storage/test_profile_migration.py`
- Create: `tests/fixtures/legacy/pre_profile_data.sql`

**Work**
- Build a representative pre-phase-15 fixture DB with rows in every migrated
  table.
- Run the migration and assert row-count parity plus `profile_id = 1` backfill.

**Acceptance criteria**
- Tests prove zero data loss on populated legacy data.
- All migrated tables preserve row counts and key relationships.

### Task 3.2 — Verify delete cascade and cross-profile isolation end to end
**Files**
- Modify: `tests/storage/test_profile_isolation.py`
- Modify: `tests/ui/test_main_window.py`

**Work**
- Create profile A and B, populate both, then delete B.
- Assert B data disappears and A data remains untouched.
- Verify switcher state after deletion falls back correctly.

**Acceptance criteria**
- Deleting a non-active profile removes all of its data.
- Deletion does not damage other profiles.
- UI state remains stable after delete + refresh.

## Test Strategy

- Storage-first TDD: migration fixtures, profile CRUD, repository isolation.
- UI tests with `pytest-qt`: switcher state, dialog validation, active-profile
  protection, session rotation.
- Regression run: ensure existing session/history tests still pass under the new
  `profile_id` contract.

**Suggested commands**
```bash
pytest tests/storage/test_db.py tests/storage/test_profile_migration.py -q
pytest tests/storage/test_profiles.py tests/storage/test_profile_isolation.py -q
QT_QPA_PLATFORM=offscreen pytest tests/ui/test_profile_dialog.py tests/ui/test_main_window.py -q
pytest -q
```

## Completion Criteria

- Legacy data migrates into default profile `Me` with zero loss.
- All profile-scoped repositories require `profile_id` explicitly.
- The app supports create/edit/delete/switch flows with active-profile guards.
- Cross-profile isolation is proven in automated tests.
- Non-active profile deletion removes all dependent data.
