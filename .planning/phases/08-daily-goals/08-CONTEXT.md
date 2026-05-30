# Phase 8: Daily Goals, Streaks & Home Widget - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase turns practice streaks from a raw "did you open the app today?"
count into a goal-aware habit system. The user should see today's target on
the Analysis tab, be able to change the underlying goal in Settings, and have
streaks depend on meeting the target rather than merely logging any session.

The adaptive part of this phase should shape the *effective daily target*, not
silently rewrite the user's saved preference every time history changes.
</domain>

<decisions>
## Key Decisions

- **D-08-01:** Store the user's configured baseline goal in `settings.json`,
  but store the day-specific effective target and achieved progress in the
  `daily_goals` table.
- **Reasoning:** This preserves the user's intent while allowing adaptive
  nudges to vary by day and history.

- **D-08-02:** Goal adaptation should be transparent. The UI shows an
  "adjusted" badge when the day's target differs from the user's saved base
  target.
- **Reasoning:** REQ-C02 explicitly says the system should not adjust without
  user awareness.

- **D-08-03:** `daily_goals.met` becomes the canonical streak source.
- **Reasoning:** Once streaks are goal-based, counting distinct `sessions.date`
  is no longer semantically correct.

- **D-08-04:** A day with no history in the last seven days uses the saved base
  target and no adjustment.
- **Reasoning:** Adaptive difficulty should start from confidence, not from a
  fabricated estimate.

- **D-08-05:** When there are at least seven completed days of history, compute
  the effective target from the seven-day average and completion rate:
  `round(avg * 1.1)` when the user met goals on at least 4 of 7 days, otherwise
  `round(avg * 0.9)`. Clamp to 5–60 minutes or 1–10 exercises.
- **Reasoning:** This makes the "±10% toward achievable" rule concrete and
  testable while still nudging successful users slightly upward.

- **D-08-06:** When a day first transitions from `met = false` to `met = true`,
  award a single `daily-goal-met` XP event worth 50 XP through
  `CurriculumService`.
- **Reasoning:** REQ-C05 explicitly includes XP for hitting daily goals, and the
  award must be tied to the moment a day is completed to avoid duplicates.

- **D-08-07:** Editing the goal mid-day recalculates today's effective target
  immediately. Preserve `achieved` only when the goal type stays the same; if
  the user switches between minutes and exercises, start a fresh day row for the
  new goal type.
- **Reasoning:** This is the least surprising UX and keeps unit semantics clean.

- **D-08-08:** Exercise-count goals increment only from producers that write a
  canonical exercise completion ID from the Phase 6 exercise catalog. For v1.2,
  count reading-passage completion and evaluation completion as one exercise
  each; free practice minutes alone do not increment the exercise counter.
- **Reasoning:** The "exercise" unit must have a deterministic producer list or
  the second goal mode is untestable.

- **D-08-09:** If a user changes goal type mid-day and more than one
  `daily_goals` row exists for the same date, a streak day counts as met when
  **any** row for that date has `met = true`.
- **Reasoning:** Switching goal type should not retroactively erase a day that was
  already successfully completed.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/REQUIREMENTS.md` — REQ-C02 and REQ-C05 (daily goals must affect
  both streaks and XP)
- `.planning/ROADMAP.md` §Phase 8 — canonical scope and success criteria
- `.planning/phases/06-curriculum-schema/06-CONTEXT.md` and `06-PLAN.md` — XP
  event shape and profile-id policy
- `src/switchedonvoice/storage/settings.py` — current JSON persistence pattern
- `src/switchedonvoice/storage/sessions.py` — current streak/history queries
- `src/switchedonvoice/ui/analysis_panel.py` and `src/switchedonvoice/ui/settings_panel.py`

</canonical_refs>

<architecture>
## Architecture Fit

### New subsystem boundaries
- `storage/daily_goals.py` should own table reads/writes for per-day progress
- `gamification/daily_goals.py` (or equivalent pure module) should own the
  adjustment algorithm and `met` evaluation helpers
- `ui/todays_goal_widget.py` should display status but not decide targets
- `ui/settings_panel.py` remains the place where base goal preferences are set

### Existing code that will be impacted
- `storage/settings.py` — new persisted goal preference fields
- `storage/sessions.py` — streak queries must be updated or supplemented to
  use `daily_goals.met`
- `ui/analysis_panel.py` / `ui/main_window.py` — widget placement and refresh
  hooks after each session

### Forward-compatibility note
`daily_goals` should include `profile_id` immediately, even if the app still
behaves as single-profile. Phase 15 will depend on that.
</architecture>

<pitfalls>
## Pitfalls to Avoid

- Do not overwrite the user's configured goal value with the adaptive value.
  Store both concepts separately.
- Do not break Phase 1 milestone logic accidentally. `get_streak()` changes
  here will ripple into milestone badges like Week Warrior and Month Strong.
- Do not calculate today's progress only in memory. The app should reopen and
  still know whether today's goal was already met.
- Do not let "minutes" goals depend on frame counts alone; use persisted
  session durations, not UI timer ticks.
- Do not adjust goals before a meaningful sample exists; the requirement says
  defer for the first seven days with no history.
</pitfalls>

<dependencies>
## Specific Dependencies on Earlier Phases

- **Phase 1:** existing streak UI and milestone system must be updated without
  regressing the 104-test baseline
- **Phase 6:** XP/session data may later award goal-completion XP, so goal
  completion records should be designed to integrate with `CurriculumService`
- **Phases 3–5:** reading sessions and passage completions are likely sources
  of exercise-count progress for the daily goal widget
</dependencies>

<deferred>
## Deferred Ideas

- User-configurable adaptive aggressiveness (easy / balanced / stretch). Defer
  until the default algorithm has real usage data.
- Calendar heatmap/history UI for goal completion. REQ-C02 only needs today's widget and streak continuity.
- Partial-credit streaks. The requirement is binary met/not-met, so keep it so.
</deferred>

<open_questions>
## Open Questions

1. When arcade games arrive in Phase 11, should they count as exactly one
   exercise each or vary by game/difficulty? Phase 8 only needs reading and
   evaluation completions, but the future rule should be written down before
   arcade implementation starts.
</open_questions>

---

*Phase: 08-daily-goals*
*Context gathered: 2026-05-30 for planning*
