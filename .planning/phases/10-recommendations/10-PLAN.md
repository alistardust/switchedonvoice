---
phase: 10-recommendations
plan: 01
type: execute
wave: multi
depends_on:
  - 07-skill-tree-ui
  - 08-daily-goals
  - 09-evaluation-mode
files_modified:
  - src/switchedonvoice/recommendations/weakness.py
  - src/switchedonvoice/recommendations/service.py
  - src/switchedonvoice/recommendations/rules.json
  - src/switchedonvoice/ui/recommendations_panel.py
  - src/switchedonvoice/storage/settings.py
  - src/switchedonvoice/ui/analysis_panel.py
  - src/switchedonvoice/ui/main_window.py
  - tests/recommendations/test_weakness.py
  - tests/recommendations/test_service.py
  - tests/ui/test_recommendations_panel.py
  - tests/storage/test_settings.py
  - tests/ui/test_main_window.py
autonomous: true
requirements:
  - REQ-C04
must_haves:
  truths:
    - "WeaknessDetector compares the last 3 scored sessions against the user's own historical 50th percentile by dimension"
    - "Recommendation rules are loaded from JSON and every emitted dimension key has at least one rule"
    - "The service never repeats an identical suggestion batch on consecutive app opens when the source fingerprint is unchanged"
    - "Dismiss hides the panel only for the current session"
  artifacts:
    - path: "src/switchedonvoice/recommendations/weakness.py"
      provides: "Weakness detection helpers"
    - path: "src/switchedonvoice/recommendations/service.py"
      provides: "Recommendation orchestration and deduplication"
    - path: "src/switchedonvoice/recommendations/rules.json"
      provides: "Declarative dimension-to-target rule table"
      contains: "dimension"
    - path: "src/switchedonvoice/ui/recommendations_panel.py"
      provides: "Home-screen suggestion card panel"
  key_links:
    - from: "src/switchedonvoice/recommendations/service.py"
      to: "src/switchedonvoice/storage/settings.py"
      via: "profile-scoped last-batch fingerprint cache"
      pattern: "last_recommendation_batch"
    - from: "src/switchedonvoice/ui/main_window.py"
      to: "src/switchedonvoice/ui/recommendations_panel.py"
      via: "Analysis-tab insertion and deep-link callback wiring"
      pattern: "Suggested Next"
---

<objective>
## Objective

Build the adaptive recommendation layer that ranks weak dimensions, maps them
to concrete next steps, and displays one to three actionable suggestion cards
on the home screen without repeating itself unnecessarily.
</objective>

<execution_context>
@~/.copilot/get-shit-done/workflows/execute-plan.md
@~/.copilot/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/07-skill-tree-ui/07-PLAN.md
@.planning/phases/08-daily-goals/08-PLAN.md
@.planning/phases/09-evaluation-mode/09-PLAN.md
@.planning/phases/10-recommendations/10-CONTEXT.md
@src/switchedonvoice/storage/settings.py
@src/switchedonvoice/ui/analysis_panel.py
@src/switchedonvoice/ui/main_window.py
</context>

<interfaces>
## Interfaces and conventions

- Recommended rule schema for `rules.json`:
  - `dimension: str`
  - `title: str`
  - `why_template: str`
  - `targets: list[{"kind": "skill" | "reading" | "exercise" | "arcade", "id": str, "title": str, "icon": str, "is_live": bool}]`
- `WeaknessDetector` returns ranked items like
  `WeakDimension(name: str, recent_score: float, baseline_p50: float, gap: float)`.
- `RecommendationService` returns `RecommendationCard` payloads ready for UI
  rendering; UI does not parse JSON rules directly.
- Deep-link contract: `RecommendationTarget(tab_id: str, action_id: str, payload_id: str)`
  and `MainWindow.navigate_to_recommendation(target: RecommendationTarget) -> None`.
- Canonical live routes for v1.2 are `progress/open_skill`,
  `reading/open_passage`, and `analysis/open_exercise`; `arcade/open_game` stays
  non-live until Phase 11.
- Settings cache should be profile-scoped even in single-profile mode.
</interfaces>

<threat_model>
## Threat model

- **Dead-link recommendations:** filter out rule targets where `is_live` is false.
- **Recommendation spam:** use a stable fingerprint of the scored input + last batch
  cache to avoid repeated cards on unchanged data.
- **Bias from empty history:** return no recommendations rather than inventing
  weakness rankings when data is too sparse.
</threat_model>

<file_map>
## File Map

### Create
- `src/switchedonvoice/recommendations/__init__.py`
- `src/switchedonvoice/recommendations/weakness.py`
- `src/switchedonvoice/recommendations/service.py`
- `src/switchedonvoice/recommendations/rules.json`
- `src/switchedonvoice/ui/recommendations_panel.py`
- `tests/recommendations/__init__.py`
- `tests/recommendations/test_weakness.py`
- `tests/recommendations/test_service.py`
- `tests/ui/test_recommendations_panel.py`

### Modify
- `src/switchedonvoice/storage/settings.py`
- `src/switchedonvoice/ui/analysis_panel.py`
- `src/switchedonvoice/ui/main_window.py`
- `tests/storage/test_settings.py`
- `tests/ui/test_main_window.py`
</file_map>

<waves>
## Wave Plan

### Wave 1 (parallel) — Detection and rule mapping

#### Task 1: Implement weakness detection
**Files:** `src/switchedonvoice/recommendations/weakness.py`, `tests/recommendations/test_weakness.py`

**Description:**
Add functions that inspect the last three scored sessions/evaluations,
aggregate per-dimension results, compare them to the user's historical 50th
percentile, and return a ranked weakness list.

**Acceptance criteria:**
- no-history and single-session cases return an empty or clearly documented result
- equal-score histories do not fabricate weaknesses
- lower pitch than resonance across recent sessions ranks pitch ahead of resonance

**Automated verify:**
- `pytest tests/recommendations/test_weakness.py -q`

#### Task 2: Create declarative recommendation rules
**Files:** `src/switchedonvoice/recommendations/rules.json`, `tests/recommendations/test_service.py`

**Description:**
Add a JSON rule table covering every detectable weak dimension with candidate
skill IDs and current/future destination IDs using the schema defined above.

**Acceptance criteria:**
- every weak dimension has at least one mapped target
- rules distinguish currently navigable targets from Phase-11 placeholders
- schema is simple enough to edit without touching Python code

**Automated verify:**
- `pytest tests/recommendations/test_service.py -q`

### Wave 2 (depends on Wave 1) — Service and settings integration

#### Task 3: Implement recommendation service + deduplication cache
**Files:** `src/switchedonvoice/recommendations/service.py`, `src/switchedonvoice/storage/settings.py`, `tests/recommendations/test_service.py`, `tests/storage/test_settings.py`

**Description:**
Build the orchestration layer that runs weakness detection, applies the rule
table, filters to 1–3 unique suggestions, and avoids repeating an identical
batch on consecutive app opens when the underlying fingerprint is unchanged.

**Acceptance criteria:**
- service persists last batch metadata in settings in a profile-scoped shape
- unchanged data yields a rotated or empty-safe result instead of a duplicate batch
- dismiss state is not persisted beyond the current session

**Automated verify:**
- `pytest tests/recommendations/test_service.py tests/storage/test_settings.py -q`

### Wave 3 (depends on Wave 2) — Home-screen UI and deep links

#### Task 4: Build `RecommendationsPanel`
**Files:** `src/switchedonvoice/ui/recommendations_panel.py`, `tests/ui/test_recommendations_panel.py`

**Description:**
Render one to three cards with icon, title, short why-it-matters text, deep-link
button, and a "Just let me choose" dismiss action.

**Acceptance criteria:**
- panel handles 0, 1, 2, or 3 cards gracefully
- dismiss hides the panel for the active session
- buttons expose accessible names and stable identifiers for tests

**Automated verify:**
- `pytest tests/ui/test_recommendations_panel.py -q`

#### Task 5: Wire the panel into Analysis/MainWindow navigation
**Files:** `src/switchedonvoice/ui/analysis_panel.py`, `src/switchedonvoice/ui/main_window.py`, `tests/ui/test_main_window.py`

**Description:**
Insert the panel below Today's Goal, fetch recommendations after session
completion or app open, and route deep-link actions through
`MainWindow.navigate_to_recommendation(target)` so buttons do not need to know
widget internals.

**Acceptance criteria:**
- after relevant low scores, the panel appears without restart
- clicking a suggestion navigates to the intended destination via the explicit
  navigation contract
- dismiss hides the panel until the next session refresh

**Automated verify:**
- `pytest tests/ui/test_main_window.py tests/ui/test_recommendations_panel.py -q`
- `pytest -q`
</waves>

<test_strategy>
## Test Strategy

### Target commands
- `pytest tests/recommendations/test_weakness.py tests/recommendations/test_service.py tests/ui/test_recommendations_panel.py tests/storage/test_settings.py tests/ui/test_main_window.py -q`
- `pytest -q`

### Key test cases
- no history / all equal / single recent score
- pitch weaker than resonance across two recent sessions
- full rule-table coverage for every dimension key
- deduplication when the source fingerprint matches the previous app open
- dismiss hiding only for the current session
- deep-link routing to a concrete destination
</test_strategy>

<edge_cases>
## Edge Case Notes

- if no currently navigable target exists for a weakness, hide that suggestion
  rather than surfacing a dead button
- if exactly one suggestion remains after deduplication, show one card rather than pad with repeated content
- settings cache must survive unknown extra keys so Phase 15 profile expansion does not break older configs
- unchanged data plus no alternate suggestions should hide the panel rather than repeat itself
</edge_cases>

<completion_criteria>
## Completion Criteria

Phase 10 is complete when:
- low recent scores generate 1–3 ranked, non-duplicative recommendations
- the Analysis tab shows suggestion cards under Today's Goal
- deep links navigate to valid content
- dismiss hides only for the current session and suggestions can reappear later
- focused tests and full `pytest -q` pass
</completion_criteria>

<output>
## Output

When implementation completes, create `.planning/phases/10-recommendations/10-SUMMARY.md`
using the standard summary template and update ROADMAP status accordingly.
</output>
