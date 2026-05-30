# Phase 25: Virtual Coach Engine - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Goal

Phase 25 turns the app's existing progress data into brief, affirming, offline
coaching messages that help the user decide what to do next without introducing
any LLM, network, or opaque model dependency.

The core deliverable is a deterministic rules engine plus a small UI surface. The
engine should explain progress gently, not judge the user or replace the rest of
the training experience.
</domain>

<dependencies>
## Dependencies on Earlier Phases

- **Phase 10 — Recommendations infrastructure:** provides the precedent for a
  declarative, rule-driven guidance system and likely route/action targets.
- **Phase 18 — Session reports/data:** provides historical metrics and reporting
  views that Phase 25 can reuse when building coach context from stored data.
- **Existing storage/session APIs:** `src/switchedonvoice/storage/sessions.py`
  already exposes history/stat aggregates, which should be reused instead of
  recomputing session summaries inside widgets.
- **Existing settings/UI shell:** `src/switchedonvoice/storage/settings.py` and
  `src/switchedonvoice/ui/main_window.py` are the likely persistence and display
  hooks.

Treat milestone-recording context as optional input. If Phase 24 lands first, the
coach can react to it; if not, the engine must still behave deterministically with
that signal absent.
</dependencies>

<decisions>
## Key Decisions

### D-25-01: The rule catalog is packaged JSON with stable IDs
Store the default coaching script as package data, not as inline Python literals.
Each rule needs a stable `rule_id`, `priority`, `category`, a declarative
condition tree, message text/template, and optional `action_hint` so the copy is
reviewable and easy to extend without editing ranking code.

### D-25-02: Separate pure evaluation from state assembly
`CoachingEngine` should be a pure function that accepts a fully assembled
`CoachingContext` and a list of rules, then returns ranked `CoachingMessage`
objects. Any DB reads, session aggregation, or milestone lookups belong in a
separate context-builder/service layer.

### D-25-03: Rule evaluation must be whitelisted and declarative
Do not use `eval`, ad-hoc Python expressions, or embedded code in JSON. Support a
small approved operator set (`eq`, `gte`, `lte`, `in`, `changed_recently`,
`all`, `any`, `not`) and compile that into pure Python comparisons.

### D-25-04: Suppression state is persistent and rule-scoped for the single local profile
Track presentation state per `rule_id` in SQLite, not only in settings memory, so
messages survive restarts cleanly. v1 is single-profile, so no `profile_id` column
is needed yet.
- dismiss = suppress that `rule_id` until explicitly cleared or replaced by a new rule ID
- snooze = suppress until `snoozed_until`
- repeat guard = do not show the same rule again within seven days unless it has never been shown

### D-25-05: Ranking is deterministic and stable
Sort eligible messages by a deterministic tuple such as `(priority, category_rank,
rule_id)` so identical input state always yields identical output ordering.
Randomized rotation is explicitly out of scope for the first version.

### D-25-06: The UI should show at most three messages
The panel should surface the top 1–3 messages only, each brief and affirming, with
clear actions for `Dismiss` and `Snooze 7 days`. The engine may rank more than
three messages, but the first implementation should not flood the user.
</decisions>

<research>
## Research Findings

### R-25-01: Phase 10 already established the value of declarative guidance rules
The Phase 10 context intentionally put recommendation mapping in packaged JSON.
Phase 25 should follow the same pattern so copywriting, policy, and ranking do not
become entangled in one giant Python file.

### R-25-02: The repo's architecture strongly favors pure core logic
`gamification/milestones.py` is already a pure decision function and is the best
local precedent for `CoachingEngine`. Keeping the engine pure makes it easy to
exercise every branch with straightforward pytest cases.

### R-25-03: Persistence belongs in SQLite, not ad-hoc widget state
The app already centralizes durable state in SQLite and settings JSON. Because
message suppression is temporal (`shown_at`, `dismissed_at`, `snoozed_until`), a
small repository table is a cleaner fit than stuffing nested suppression maps into
settings JSON.

### R-25-04: The current Settings dataclass is intentionally small and atomic
`storage/settings.py` persists a single JSON document atomically. That is a good
home for user preferences, but not for event history that may grow over time. Use
settings for display toggles, not for the coach message ledger.

### R-25-05: REQ-C01 has a known content-spec gap, so copy should stay conservative
Because the coaching-script spec is not finalized, the first rule set should stay
short, supportive, and non-clinical. Avoid pseudo-therapeutic claims, promises of
outcomes, or any language that would imply diagnosis.
</research>

<data_model>
## Data Model

### SQLite

Recommended table:

```sql
CREATE TABLE coaching_message_state (
    rule_id TEXT PRIMARY KEY,
    last_shown_at TEXT,
    dismissed_at TEXT,
    snoozed_until TEXT,
    last_context_fingerprint TEXT,
    presentation_count INTEGER NOT NULL DEFAULT 0
);
```

### Dataclasses

- `CoachingContext(...)` — immutable snapshot of user state (streak, recent
  scores, unlocked skills, plateau flags, milestone flags, fatigue indicators)
- `CoachingRule(rule_id, priority, category, condition, text, action_hint)`
- `CoachingMessage(rule_id, priority, category, text, action_hint)`
- `CoachingMessageState(rule_id, last_shown_at, dismissed_at, snoozed_until, presentation_count)`
- `CoachingDecision(messages, suppressed_rule_ids, generated_at)`

### Key Interfaces

- `load_coaching_rules() -> list[CoachingRule]`
- `evaluate_coaching_rules(context, rules) -> list[CoachingMessage]` (pure)
- `CoachingStateRepository` for show/dismiss/snooze persistence
- `build_coaching_context(...) -> CoachingContext` to translate storage/session
  data into the pure-engine input contract
</data_model>

<open_questions>
## Open Questions Deferred to Later Phases

1. Should dismiss be permanent forever for a rule ID, or should there be a
   product-level reset affordance in settings? The first implementation can treat
   dismiss as indefinite and add reset UX later.
2. Which event signals count as `vocal fatigue` in a rules-only system: explicit
   self-report, session duration, unstable CPP trend, or repeated early stops?
   The engine can ship with a conservative placeholder flag if the signal is not
   yet fully specified.
3. Should the coach eventually surface richer action buttons (open a passage,
   open a skill, start an exercise)? Phase 25 only needs `action_hint` text; deep
   navigation can be expanded later.
4. Does the default ruleset need localization in v1? Deferred; ship English first
   with stable rule IDs so translated catalogs can follow later.
</open_questions>

---

*Phase: 25-virtual-coach-engine*
*Context gathered: 2026-05-30 for plan authoring*
