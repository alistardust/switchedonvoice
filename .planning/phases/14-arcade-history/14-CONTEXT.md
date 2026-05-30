# Phase 14: Arcade Personal Bests & History View - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 14 is the payoff layer for Milestone v1.3. All four arcade games already
exist; this phase turns score persistence into visible momentum by celebrating
personal bests, showing short-run trends on launcher tiles, and surfacing arcade
statistics in the Progress tab and XP Breakdown.

This phase should not add new games or redefine scoring formulas. It should read
from the history already stored in `arcade_scores` and make that history feel
rewarding, accurate, and instantly updated.
</domain>

<decisions>
## Implementation Decisions

### Personal best semantics
- **D-14-01:** A personal best is strictly `new_score > old_best`, never greater-
  than-or-equal. Ties should not trigger the celebration banner.
- **D-14-02:** Personal-best comparison logic belongs in a small pure helper or
  repository-facing service function so all game-over screens behave identically.

### History sparklines
- **D-14-03:** Launcher tiles should request the last 10 scores through
  `ArcadeRepository.get_recent_scores()` and render them oldest-first.
- **D-14-04:** Sparklines are read-only micro-visualizations. No zooming,
  panning, or hover tooltips are required in Phase 14.
- **D-14-05:** `pyqtgraph` is the intended plotting tool per roadmap, but it is
  not present in the current `pyproject.toml`. If still absent after Phases 11–13,
  add it in this phase rather than hand-rolling a second chart system.

### Progress and XP aggregation
- **D-14-06:** Arcade statistics should be repository-driven aggregate queries:
  total sessions played, most-played game, total arcade XP, and per-game bests.
- **D-14-07:** XP Breakdown should group arcade contributions by `game_id` and
  present user-facing game names, not raw IDs.
- **D-14-08:** Launcher and Progress views must refresh immediately after a game
  completes without requiring tab navigation or app restart.
</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md` — REQ-A06
- `.planning/ROADMAP.md` §Phase 14 — canonical task list and success criteria
- `.planning/phases/11-arcade-infrastructure/11-CONTEXT.md` — storage/history
  rules established by `arcade_scores`
- `src/switchedonvoice/ui/progress_panel.py` — existing statistics/XP panel style
- `src/switchedonvoice/arcade/repository.py` — score query layer from Phase 11
</canonical_refs>

<code_context>
## Existing Code Insights

- Phase 11 deliberately stores every attempt, which makes Phase 14 mostly a
  query + presentation problem rather than a migration-heavy feature.
- The Progress tab already knows how to render summaries and tabular history.
  Arcade statistics should fit that pattern instead of becoming a separate
  dashboard.
- Launcher tiles should already have metadata and a personal-best text area from
  earlier phases; Phase 14 extends that surface with sparkline history and richer
  best-state messaging.
</code_context>

<pitfalls>
## Pitfalls and Constraints

- **Do not recompute history in widgets by scanning all rows ad hoc.** Use
  repository methods so sorting/grouping rules stay consistent.
- **Do not trigger false personal-best banners on ties or float-rounding noise.**
  Comparison rules must be explicit and type-safe.
- **Keep launcher sparklines tiny and cheap.** They update often and sit in a
  grid, so avoid heavyweight redraw logic.
- **Do not leak raw `game_id` strings into user-facing UI.** Map them to display
  names consistently.
</pitfalls>

<open_questions>
## Open Questions / Assumptions

- **Dependency timing for `pyqtgraph`:** Planning assumes Phase 14 can add it if
  Phases 9 or earlier did not already. Confirm before implementation.
- **XP Breakdown structure after Phase 7:** If XP Breakdown is table-based rather
  than grouped, this phase may need a lightweight grouping adapter instead of a
  full UI redesign.
</open_questions>

<deferred>
## Deferred Ideas

- Calendar heatmaps, weekly arcade streaks, and long-range analytics beyond the
  last 10 attempts — defer to a later progress-focused milestone.
- Cross-game achievement badges based on arcade score thresholds — defer until
  the history surfaces prove useful.
</deferred>

---

*Phase: 14-arcade-history*
*Context gathered: 2026-05-30 for phase planning*
