---
phase: 08-daily-goals
plan: 01
type: execute
wave: multi
depends_on:
  - 01-foundation
  - 06-curriculum-schema
files_modified:
  - src/switchedonvoice/storage/db.py
  - src/switchedonvoice/storage/daily_goals.py
  - src/switchedonvoice/gamification/daily_goals.py
  - src/switchedonvoice/storage/settings.py
  - src/switchedonvoice/storage/sessions.py
  - src/switchedonvoice/ui/todays_goal_widget.py
  - src/switchedonvoice/ui/analysis_panel.py
  - src/switchedonvoice/ui/settings_panel.py
  - src/switchedonvoice/ui/main_window.py
  - tests/storage/test_daily_goals.py
  - tests/gamification/test_daily_goals.py
  - tests/ui/test_todays_goal_widget.py
  - tests/storage/test_settings.py
  - tests/storage/test_sessions.py
  - tests/ui/test_main_window.py
autonomous: true
requirements:
  - REQ-C02
  - REQ-C05
must_haves:
  truths:
    - "Database schema version advances by exactly one from the schema version present when Phase 8 starts (expected baseline: 5 if upstream phases remain unchanged)"
    - "The effective daily target stays at the saved base goal until seven completed days of history exist"
    - "When there are seven days of history, effective target = round(avg * 1.1) if at least 4 of 7 goals were met, else round(avg * 0.9), then clamp to 5–60 minutes or 1–10 exercises"
    - "A streak day counts only when daily_goals.met is true"
    - "The first false->true transition for a day awards exactly one daily-goal XP event worth 50 XP"
  artifacts:
    - path: "src/switchedonvoice/storage/db.py"
      provides: "Schema migration with daily_goals"
      contains: "_CURRENT_SCHEMA_VERSION"
    - path: "src/switchedonvoice/gamification/daily_goals.py"
      provides: "Pure adaptive target and goal-completion logic"
    - path: "src/switchedonvoice/ui/todays_goal_widget.py"
      provides: "Analysis-tab TodayGoalWidget"
  key_links:
    - from: "src/switchedonvoice/ui/main_window.py"
      to: "src/switchedonvoice/storage/daily_goals.py"
      via: "session-close progress + refresh"
      pattern: "daily_goals"
    - from: "src/switchedonvoice/storage/sessions.py"
      to: "daily_goals.met"
      via: "goal-based streak computation"
      pattern: "met = 1"
    - from: "daily goal completion"
      to: "src/switchedonvoice/curriculum/service.py"
      via: "award_xp(profile_id, 'daily-goal-met', source_id, 50)"
      pattern: "daily-goal-met"
---

<objective>
## Objective

Add a goal-aware daily habit system: persisted goal preferences, adaptive daily
targets, a home-screen widget, streak logic that only counts goal-met days, and
XP credit when a daily goal is first completed.
</objective>

<execution_context>
@~/.copilot/get-shit-done/workflows/execute-plan.md
@~/.copilot/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/06-curriculum-schema/06-PLAN.md
@.planning/phases/08-daily-goals/08-CONTEXT.md
@src/switchedonvoice/storage/db.py
@src/switchedonvoice/storage/settings.py
@src/switchedonvoice/storage/sessions.py
@src/switchedonvoice/ui/analysis_panel.py
@src/switchedonvoice/ui/settings_panel.py
</context>

<interfaces>
## Interfaces and conventions

- Storage remains local SQLite/JSON only; use per-call connections and atomic
  settings writes.
- Pure helpers in `gamification/daily_goals.py` should expose typed functions such as:
  - `calculate_effective_target(base_target, history, goal_type) -> GoalTarget`
  - `is_goal_met(target, achieved) -> bool`
- `daily_goals` rows should include `profile_id`, `date`, `goal_type`, `target`,
  `achieved`, and `met`; `source_id` for XP can be `YYYY-MM-DD:<goal_type>`.
- Exercise-count progress increments only for canonical completions emitted with a
  Phase 6 exercise ID; v1.2 counts reading-passage and evaluation completion as
  one exercise each.
- Streak queries treat a date as completed when **any** `daily_goals` row for
  that date has `met = true`.
- UI modules use stdlib `logging`; storage modules use `structlog`.
</interfaces>

<threat_model>
## Threat model

- **Duplicate XP awards:** award 50 XP only on the first `met: false -> true`
  transition for a day.
- **Silent preference mutation:** keep base goal in settings and effective target in
  `daily_goals`; never overwrite the saved preference automatically.
- **Streak corruption:** update `get_streak()`/related queries atomically against
  persisted `daily_goals.met`, not in-memory widget state.
</threat_model>

<file_map>
## File Map

### Create
- `src/switchedonvoice/storage/daily_goals.py`
- `src/switchedonvoice/gamification/daily_goals.py`
- `src/switchedonvoice/ui/todays_goal_widget.py`
- `tests/storage/test_daily_goals.py`
- `tests/gamification/test_daily_goals.py`
- `tests/ui/test_todays_goal_widget.py`

### Modify
- `src/switchedonvoice/storage/db.py`
- `src/switchedonvoice/storage/settings.py`
- `src/switchedonvoice/storage/sessions.py`
- `src/switchedonvoice/ui/analysis_panel.py`
- `src/switchedonvoice/ui/settings_panel.py`
- `src/switchedonvoice/ui/main_window.py`
- `tests/storage/test_settings.py`
- `tests/storage/test_sessions.py`
- `tests/ui/test_main_window.py`
</file_map>

<waves>
## Wave Plan

### Wave 1 (parallel) — Persistence and pure logic

#### Task 1: Add `daily_goals` table and repository
**Files:** `src/switchedonvoice/storage/db.py`, `src/switchedonvoice/storage/daily_goals.py`, `tests/storage/test_daily_goals.py`

**Description:**
Create the next schema version after the version present when Phase 8 starts
(expected `5` if upstream plans stay unchanged) with the new `daily_goals`
table and repository helpers
for upserting today's row, loading recent history, and recomputing `met` after
progress updates.

**Acceptance criteria:**
- one logical row per profile/day/goal type
- rows persist enough data to reconstruct today's widget on app reopen
- repository supports seven-day history queries

**Automated verify:**
- `pytest tests/storage/test_daily_goals.py tests/storage/test_settings.py -q`
- include assertions for `PRAGMA user_version == previous_version + 1`

#### Task 2: Extend settings with base daily goal preferences
**Files:** `src/switchedonvoice/storage/settings.py`, `tests/storage/test_settings.py`

**Description:**
Add typed settings fields for goal type and target amount, with defaults of 10
minutes / 3 exercises and forward-compatible single-profile handling.

**Acceptance criteria:**
- settings load/save round-trips with new fields present or absent
- corrupt or missing goal fields fall back safely to defaults

**Automated verify:**
- `pytest tests/storage/test_settings.py -q`

#### Task 3: Implement pure adjustment + completion logic
**Files:** `src/switchedonvoice/gamification/daily_goals.py`, `tests/gamification/test_daily_goals.py`

**Description:**
Implement the canonical algorithm: before seven completed days, return the base
target unchanged. After that, compute the seven-day average achieved amount;
when at least 4 of the last 7 days were met, effective target is
`round(avg * 1.1)`, otherwise `round(avg * 0.9)`. Clamp to 5–60 minutes or
1–10 exercises.

**Acceptance criteria:**
- no-history path returns the base target unchanged
- 7-day plateau and all-missed scenarios are covered
- min/max clamps are enforced

**Automated verify:**
- `pytest tests/gamification/test_daily_goals.py -q`

### Wave 2 (depends on Wave 1) — UI and session integration

#### Task 4: Add goal controls to Settings
**Files:** `src/switchedonvoice/ui/settings_panel.py`

**Description:**
Extend the settings UI with goal type and target controls.

**Acceptance criteria:**
- users can change goal type and target amount
- saving persists values to `settings.json`
- invalid combinations are rejected clearly

**Automated verify:**
- `pytest tests/storage/test_settings.py tests/ui/test_main_window.py -q`

#### Task 5: Add `TodayGoalWidget` to the Analysis tab
**Files:** `src/switchedonvoice/ui/todays_goal_widget.py`, `src/switchedonvoice/ui/analysis_panel.py`, `tests/ui/test_todays_goal_widget.py`

**Description:**
Build the compact home widget showing today's effective target, progress,
progress bar, and adjusted badge when applicable.

**Acceptance criteria:**
- widget renders both minutes and exercises modes
- adjusted badge appears only when the effective target differs from the base
- empty-day state is readable and not misleading

**Automated verify:**
- `pytest tests/ui/test_todays_goal_widget.py -q`

#### Task 6: Integrate progress, streak, and XP updates in `MainWindow`
**Files:** `src/switchedonvoice/ui/main_window.py`, `src/switchedonvoice/storage/sessions.py`, `tests/ui/test_main_window.py`, `tests/storage/test_sessions.py`

**Description:**
Update the session-close flow so completed sessions contribute to today's goal,
`daily_goals.met` is recalculated, the widget refreshes, the streak uses goal
completion rather than raw session presence, exercise-count mode increments only
for canonical completion producers, and the first successful day-complete
transition awards `daily-goal-met` XP exactly once.

**Acceptance criteria:**
- meeting the goal increments the streak
- missing the goal breaks the streak correctly
- hitting the goal awards a single 50 XP event
- existing milestone/streak displays remain consistent with the new source

**Automated verify:**
- `pytest tests/storage/test_sessions.py tests/ui/test_main_window.py -q`

### Wave 3 (depends on Wave 2) — End-to-end verification

#### Task 7: Add integration tests for adaptive behaviour and persistence
**Files:** `tests/gamification/test_daily_goals.py`, `tests/storage/test_daily_goals.py`, `tests/ui/test_main_window.py`

**Description:**
Add cross-layer tests covering first-use defaults, seven-day history
adaptation, mid-stream goal completion, XP award idempotency, and widget
refresh after session close.

**Acceptance criteria:**
- after seven days, effective target reflects history using the canonical formula
- app reopen preserves today's progress and met/not-met state
- UI refresh requires no manual restart

**Automated verify:**
- `pytest tests/storage/test_daily_goals.py tests/gamification/test_daily_goals.py tests/ui/test_todays_goal_widget.py tests/storage/test_sessions.py tests/ui/test_main_window.py -q`
- `pytest -q`
</waves>

<test_strategy>
## Test Strategy

### Target commands
- `pytest tests/storage/test_daily_goals.py tests/gamification/test_daily_goals.py tests/ui/test_todays_goal_widget.py tests/storage/test_sessions.py tests/ui/test_main_window.py -q`
- `pytest -q`

### Key test cases
- no history / single session / seven-day plateau / all-missed history
- exercise goals vs minute goals
- mid-day progress updates moving `met` from false to true exactly once
- goal-type switch mid-day where one row is met and the later row is not met
- streak recalculation across a missed day boundary
- settings round-trip with new goal fields
</test_strategy>

<edge_cases>
## Edge Case Notes

- if the user changes from minutes to exercises mid-day, preserve achieved data
  only when the units are compatible; otherwise reset today's row explicitly
- rounding must not push effective targets outside the documented min/max
- zero-duration sessions should not accidentally grant minute-based progress
- if history is sparse or malformed, fall back to the saved base target
</edge_cases>

<completion_criteria>
## Completion Criteria

Phase 8 is complete when:
- the Analysis tab shows a persisted daily goal widget that refreshes after sessions
- settings persist the user's base goal preferences
- adaptive effective targets follow the canonical seven-day algorithm
- streak logic counts only goal-met days and goal completion awards XP once
- focused tests and full `pytest -q` pass
</completion_criteria>

<output>
## Output

When implementation completes, create `.planning/phases/08-daily-goals/08-SUMMARY.md`
using the standard summary template and update ROADMAP status accordingly.
</output>
