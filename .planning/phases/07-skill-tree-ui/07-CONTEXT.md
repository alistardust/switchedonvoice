# Phase 7: Skill Tree UI + XP & Level Display - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase turns the Phase 6 curriculum model into visible feedback. The user
should be able to inspect the skill map, understand what is locked vs
available vs complete, see total XP and current level at a glance, and get a
celebratory interruption when they cross a level threshold.

The phase is UI-heavy, but it should not redefine curriculum logic. All skill
state, XP totals, and level data must come from `CurriculumService`.
</domain>

<decisions>
## Key Decisions

- **D-07-01:** Use a deterministic manual layout for the first skill tree:
  five vertical category columns, three tier rows, and simple dependency lines.
  This matches the forest DAG chosen in Phase 6 and avoids implementing a
  general graph layout engine.
- **D-07-02:** Render the tree in a dedicated `SkillTreeWidget` using
  `QPainter`, but keep node layout data in testable Python structures so the
  widget is not the source of truth for graph semantics.
- **D-07-03:** Treat animation and sound as decoration layered on top of state
  changes. The unlock event must still be visible and testable when animation
  is disabled or sound playback fails.
- **D-07-04:** Put the always-visible XP counter and level progress bar in the
  main window status bar. This aligns with the current `QStatusBar` usage and
  keeps Progress-tab information visible while the user is training.
- **D-07-05:** Store prior displayed level in UI state, not the database.
  Phase 6 already stores enough information (XP totals) to determine whether a
  threshold was crossed.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/REQUIREMENTS.md` — REQ-C01 and REQ-C05 for unlock, XP, level, and
  breakdown requirements
- `.planning/ROADMAP.md` §Phase 7 — canonical task list and success criteria
- `.planning/phases/06-curriculum-schema/06-CONTEXT.md` and `06-PLAN.md` —
  seeded skill IDs, level ladder, service contract, and graph-shape decision
- `src/switchedonvoice/ui/main_window.py` — status bar and refresh orchestration
- `src/switchedonvoice/ui/progress_panel.py` — current Progress-tab composition

</canonical_refs>

<architecture>
## Architecture Fit

### Existing files this phase will likely touch
- `src/switchedonvoice/ui/main_window.py` — status bar widgets, post-session
  refresh hook, and level-up dialog trigger point
- `src/switchedonvoice/ui/progress_panel.py` — add the skill tree and XP
  breakdown panel beside existing history widgets
- `src/switchedonvoice/curriculum/service.py` — read-only consumer from UI

### New UI units recommended
- `ui/skill_tree_widget.py` — rendering, hover hit-testing, and animation state
- `ui/level_up_dialog.py` — full-window celebratory overlay
- `ui/xp_breakdown_widget.py` — itemised `xp_events` list and total display

### Why this split matters
`ProgressPanel` is already doing several jobs. Adding drawing code, XP list
models, and overlay dialog logic directly into it would make Phase 7 hard to
test and hard to evolve for Phase 9 graphs.
</architecture>

<pitfalls>
## Pitfalls to Avoid

- Do not let `SkillTreeWidget` query SQLite or the service directly during
  paint events. Provide prepared view models and repaint cheaply.
- Do not rely on colours alone for state communication. Tooltips, labels, or
  accessible names should expose locked / available / complete semantics.
- Do not block the UI thread when loading or playing the unlock chime. Sound
  failures should degrade silently.
- Do not trigger the level-up dialog on every app launch. It should appear
  only when XP crosses a threshold since the last displayed value.
- Do not hardcode graph geometry in multiple places. One layout helper should
  define node positions for painting, hover, and tests.
</pitfalls>

<dependencies>
## Specific Dependencies on Earlier Phases

- **Phase 6:** `CurriculumService`, skill IDs, level thresholds, and `xp_events`
  are all prerequisites.
- **Phase 4:** completed reading/passage sessions are the first likely source
  of curriculum unlocks and XP updates.
- **MainWindow close ordering from Phase 1:** the UI refresh path should keep
  the existing `close_session()` → stats → milestone update ordering intact,
  then append curriculum refreshes after persistence.
</dependencies>

<deferred>
## Deferred Ideas

- Auto-layout graph rendering for arbitrary cross-category DAGs. The manual grid
  is enough for the fixed Phase 6 forest.
- Replayable, multi-node chain animations for bulk unlocks. One pulse per newly
  unlocked node is sufficient for v1.2.
- Theme-level animation customisation. Not needed before the tree proves useful.
</deferred>

<open_questions>
## Open Questions

1. Should the unlock chime be a packaged WAV in repo assets, or generated via
   `QtMultimedia`/`QSoundEffect` from a minimal embedded resource? Packaging
   choice affects test seams.
3. If the status bar becomes crowded on narrow windows, should XP and level be
   collapsible into a single compact widget rather than two separate controls?
</open_questions>

---

*Phase: 07-skill-tree-ui*
*Context gathered: 2026-05-30 for planning*
