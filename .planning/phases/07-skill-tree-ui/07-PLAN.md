---
phase: 07-skill-tree-ui
plan: 01
type: execute
wave: multi
depends_on:
  - 06-curriculum-schema
files_modified:
  - src/switchedonvoice/ui/skill_tree_widget.py
  - src/switchedonvoice/ui/level_up_dialog.py
  - src/switchedonvoice/ui/xp_breakdown_widget.py
  - src/switchedonvoice/ui/progress_panel.py
  - src/switchedonvoice/ui/main_window.py
  - tests/ui/test_skill_tree_widget.py
  - tests/ui/test_level_up_dialog.py
  - tests/ui/test_progress_panel.py
  - tests/ui/test_main_window.py
autonomous: true
requirements:
  - REQ-C01
  - REQ-C05
must_haves:
  truths:
    - "Progress tab renders the complete Phase 6 DAG with locked, in-progress, and complete states"
    - "Status bar shows current XP total and progress toward the next level at all times"
    - "Crossing a level threshold shows exactly one level-up dialog for that threshold"
    - "XP breakdown totals match CurriculumService totals"
  artifacts:
    - path: "src/switchedonvoice/ui/skill_tree_widget.py"
      provides: "QPainter-based skill tree widget"
      exports:
        - "class SkillTreeWidget"
    - path: "src/switchedonvoice/ui/level_up_dialog.py"
      provides: "Celebratory overlay dialog"
      exports:
        - "class LevelUpDialog"
    - path: "src/switchedonvoice/ui/xp_breakdown_widget.py"
      provides: "XP event list widget"
  key_links:
    - from: "src/switchedonvoice/ui/progress_panel.py"
      to: "src/switchedonvoice/curriculum/service.py"
      via: "read-only curriculum adapter/service injection"
      pattern: "CurriculumService"
    - from: "src/switchedonvoice/ui/main_window.py"
      to: "src/switchedonvoice/ui/level_up_dialog.py"
      via: "threshold crossing detected after persisted refresh"
      pattern: "LevelUpDialog"
---

<objective>
## Objective

Build the visual curriculum experience: skill tree rendering, XP display,
level progress, level-up celebration, and an itemised XP breakdown in the
Progress tab.
</objective>

<execution_context>
@~/.copilot/get-shit-done/workflows/execute-plan.md
@~/.copilot/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/06-curriculum-schema/06-CONTEXT.md
@.planning/phases/07-skill-tree-ui/07-CONTEXT.md
@src/switchedonvoice/ui/main_window.py
@src/switchedonvoice/ui/progress_panel.py
@tests/ui/test_progress_panel.py
@tests/ui/test_main_window.py
</context>

<interfaces>
## Interfaces and conventions

- `SkillTreeWidget` consumes precomputed view-model data, not raw DB rows.
- Recommended view-model shape:
  - `SkillNodeView(id: str, name: str, category: str, tier: int, state: Literal["locked","in_progress","complete"], tooltip_text: str, is_newly_unlocked: bool)`
  - `SkillEdgeView(source_id: str, target_id: str)`
- `LevelUpDialog` input payload should be a typed level definition from Phase 6,
  not ad-hoc dicts.
- UI modules continue using stdlib `logging`; do not introduce `structlog` here.
- Status-bar refresh happens on the Qt main thread after session persistence.
</interfaces>

<threat_model>
## Threat model

- **UI freeze risk:** all painting and animation must use cached state; no service or
  disk calls inside paint events.
- **Repeat dialog spam:** compare the newly computed level against the previously
  displayed level before showing the dialog.
- **Accessibility drift:** do not rely on colour alone; tooltips and accessible names
  must expose node state and XP changes.
</threat_model>

<file_map>
## File Map

### Create
- `src/switchedonvoice/ui/skill_tree_widget.py`
- `src/switchedonvoice/ui/level_up_dialog.py`
- `src/switchedonvoice/ui/xp_breakdown_widget.py`
- `tests/ui/test_skill_tree_widget.py`
- `tests/ui/test_level_up_dialog.py`

### Modify
- `src/switchedonvoice/ui/progress_panel.py`
- `src/switchedonvoice/ui/main_window.py`
- `tests/ui/test_progress_panel.py`
- `tests/ui/test_main_window.py`
</file_map>

<waves>
## Wave Plan

### Wave 1 (parallel) — Standalone widgets

#### Task 1: Implement `SkillTreeWidget`
**Files:** `src/switchedonvoice/ui/skill_tree_widget.py`, `tests/ui/test_skill_tree_widget.py`

**Description:**
Render the seeded skill DAG with category columns, dependency lines, node
states, hover tooltips, and a pulse animation hook. Use one layout helper for
paint, hit-testing, and tests.

**Acceptance criteria:**
- locked / in-progress / complete nodes render with distinct styles
- dependency edges are painted for all prerequisite links
- hover hit-testing exposes skill detail text
- tests can validate node state and geometry without screenshot diffs

**Automated verify:**
- `pytest tests/ui/test_skill_tree_widget.py -q`

#### Task 2: Implement `LevelUpDialog`
**Files:** `src/switchedonvoice/ui/level_up_dialog.py`, `tests/ui/test_level_up_dialog.py`

**Description:**
Create a dismissible full-screen-style overlay (or frameless dialog anchored to
the main window) showing level number, name, and flavour text.

**Acceptance criteria:**
- dialog shows correct title/body for a provided level payload
- click or key press dismisses it
- dialog remains usable under `QT_QPA_PLATFORM=offscreen`

**Automated verify:**
- `pytest tests/ui/test_level_up_dialog.py -q`

#### Task 3: Implement `XPBreakdownWidget`
**Files:** `src/switchedonvoice/ui/xp_breakdown_widget.py`

**Description:**
Build a widget/table model for listing `xp_events` with source type, amount,
and earned date, plus a total footer.

**Acceptance criteria:**
- empty state is clear and non-broken
- total matches the sum of rendered rows
- formatting is deterministic for tests

**Automated verify:**
- `pytest tests/ui/test_progress_panel.py -q`

### Wave 2 (depends on Wave 1) — Progress tab integration

#### Task 4: Embed tree + XP breakdown into `ProgressPanel`
**Files:** `src/switchedonvoice/ui/progress_panel.py`, `tests/ui/test_progress_panel.py`

**Description:**
Restructure the Progress tab so existing milestone/history widgets coexist with
the new skill tree and XP breakdown. Inject `CurriculumService` or a thin
adapter so refreshes stay testable.

**Acceptance criteria:**
- opening Progress shows the tree and XP breakdown alongside existing content
- panel refresh pulls current skill state and XP events after session close
- totals displayed in the breakdown match service XP totals

**Automated verify:**
- `pytest tests/ui/test_progress_panel.py -q`

#### Task 5: Add XP + level widgets to the status bar
**Files:** `src/switchedonvoice/ui/main_window.py`, `tests/ui/test_main_window.py`

**Description:**
Extend the current status area so it still supports vocal-health warnings while
adding XP total and a level progress bar.

**Acceptance criteria:**
- XP counter is always visible during normal app usage
- progress bar reflects current level progress and next threshold
- existing health warning text still appears correctly

**Automated verify:**
- `pytest tests/ui/test_main_window.py -q`

### Wave 3 (depends on Wave 2) — Session refresh + level-up trigger

#### Task 6: Trigger unlock animation and level-up dialog from persisted state
**Files:** `src/switchedonvoice/ui/main_window.py`, `src/switchedonvoice/ui/skill_tree_widget.py`, `tests/ui/test_main_window.py`

**Description:**
After a session closes and curriculum state is refreshed, detect newly unlocked
skills and level threshold crossings. Animate the relevant nodes and show the
level-up dialog once.

**Acceptance criteria:**
- no restart is needed to see updated node states
- crossing a threshold shows the correct dialog payload
- merely reopening the app at the same XP total does not retrigger the dialog

**Automated verify:**
- `pytest tests/ui/test_skill_tree_widget.py tests/ui/test_main_window.py -q`
- `pytest -q`
</waves>

<test_strategy>
## Test Strategy

### Target commands
- `pytest tests/ui/test_skill_tree_widget.py tests/ui/test_level_up_dialog.py tests/ui/test_progress_panel.py tests/ui/test_main_window.py -q`
- `pytest -q`

### Key test cases
- state rendering for locked, in-progress, and complete nodes
- edge-count rendering for the full DAG
- XP counter refresh after injecting a new event from the service
- threshold-crossing dialog trigger when XP goes from just below to exactly at a boundary
- dialog non-trigger when XP remains unchanged
</test_strategy>

<edge_cases>
## Edge Case Notes

- zero-XP users should still see level 1 and a valid empty progress state
- users with all 15 skills unlocked should still see a readable tree with no animation spam on refresh
- if sound playback is unavailable, animation and dialog must still function
- tooltips must remain correct even during animated node pulses
</edge_cases>

<completion_criteria>
## Completion Criteria

Phase 7 is complete when:
- Progress tab shows the full tree and XP breakdown
- status bar shows XP and level progress continuously
- new unlocks animate on refresh without restart
- level thresholds trigger a single correct celebratory dialog
- widget tests and full `pytest -q` pass
</completion_criteria>

<output>
## Output

When implementation completes, create `.planning/phases/07-skill-tree-ui/07-SUMMARY.md`
using the standard summary template and update ROADMAP status accordingly.
</output>
