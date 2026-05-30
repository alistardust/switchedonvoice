# Phase 11: Arcade Infrastructure + Pitch Targeting Game - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 11 opens Milestone v1.3 by adding the Arcade tab, the shared arcade
runtime, persistent score storage, and the first fully playable game: Pitch
Targeting. This phase establishes the contracts every later arcade game will use:
launcher tiles, repository queries, game lifecycle, audio-frame delivery, score
finalisation, and XP awards.

This is both infrastructure and product work. The infrastructure must be stable
enough that Phases 12–14 can add new games and history features without changing
MainWindow's audio loop or reworking the DB schema.
</domain>

<decisions>
## Implementation Decisions

### Arcade package layout
- **D-11-01:** Introduce a dedicated `src/switchedonvoice/arcade/` package for
  game runtime, storage-facing repository code, launcher UI helpers, and future
  game modules. Keep the actual tab widget in `ui/arcade_panel.py` so the main
  window still owns top-level tab composition.
- **D-11-02:** Create a `games/` subpackage from the start even though only Pitch
  Targeting ships in this phase. Future phases add new games by adding modules,
  not by enlarging one file.

### ArcadeGame base class
- **D-11-03:** `ArcadeGame` is a `QWidget` subclass with an internal `QTimer`
  tick loop running on the Qt main thread. It must not spawn its own analysis
  thread or touch the sounddevice callback path.
- **D-11-04:** Games receive live analysis data only through
  `MainWindow._tick() -> ArcadePanel.on_audio_frame(result) -> active_game.on_audio_frame(result)`.
  This preserves the existing three-thread audio architecture: the callback still
  only appends, DSP still stays in `audio/capture.py`, and UI/game state stays on
  the Qt thread.
- **D-11-05:** The base class owns the state machine
  `idle -> countdown/playing -> paused -> game_over`, elapsed-time accounting,
  and final-score publication. Concrete games implement hooks for reset,
  simulation tick, painting, and audio-frame reaction.
- **D-11-06:** Tab switches pause the active game rather than stopping it. The
  Arcade tab or panel listens for visibility/current-tab changes and calls
  `pause_game(reason="tab_hidden")`. Resume requires explicit user action to
  avoid punishing accidental context switches.

### Score storage
- **D-11-07:** `arcade_scores.game_id` is a string constant defined per game
  class (for example `"pitch_targeting"`), not a DB enum. New games only add a
  new class constant and launcher registration entry.
- **D-11-08:** `arcade_scores` stores every attempt, not just personal bests.
  Phase 14 depends on this for sparklines and aggregated history.
- **D-11-09:** `ArcadeRepository.get_personal_best()` returns the highest score
  for `(profile_id, game_id)` and `get_recent_scores()` returns oldest-first data
  when a bounded recent history is requested for plotting.

### XP model
- **D-11-10:** Use one shared XP formula shape across arcade games, with a
  per-game multiplier stored as a class constant on each game. This keeps XP
  understandable for users and prevents divergent service logic.
- **D-11-11:** Recommended formula contract:
  `earned_xp = round(base_score_normalized * difficulty_multiplier * GAME_XP_MULTIPLIER)`
  with the exact multiplier published by each game class. Phase 11 defines the
  reusable helper and Pitch Targeting provides the first multiplier.

### Difficulty model
- **D-11-12:** Difficulty tiers are explicit named constants/dataclasses, not
  formulas scattered through paint/tick code. Tests should assert the exact tier
  values for width, fall speed, dwell, and simultaneous targets.
- **D-11-13:** Pitch Targeting bands are represented in cents relative to target
  pitch, while the live trace remains in Hz. Conversion helpers belong in the
  game module so pitch math stays isolated from the base class.

### Integration with existing systems
- **D-11-14:** Game completion writes score data through `ArcadeRepository`
  first, then awards XP through `CurriculumService`, then updates the game-over
  view with both values. Persisting score before UI celebration avoids losing the
  attempt if later UI work throws.
- **D-11-15:** Arcade tab lock/unlock state should be data-driven from launcher
  metadata plus current progression state, but Phase 11 may initially ship all
  non-Pitch tiles as visible-but-locked placeholders for Phases 12–13.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project requirements
- `.planning/REQUIREMENTS.md` — REQ-A01 and REQ-A06 are the canonical feature
  requirements for Pitch Targeting, personal bests, and arcade history
- `.planning/ROADMAP.md` §Phase 11 — canonical task list and success criteria

### Existing audio/runtime architecture
- `src/switchedonvoice/audio/capture.py` — `AnalysisResult`, queue delivery, and
  the rule that DSP already happens off the UI thread
- `src/switchedonvoice/ui/main_window.py` — `_tick()` polling loop and existing
  tab ownership; arcade audio hooks must fit here without changing the callback
  architecture

### Existing storage and progress systems
- `src/switchedonvoice/storage/db.py` — migration style using independent
  `if version < N` blocks and `PRAGMA user_version`
- `src/switchedonvoice/ui/progress_panel.py` — Phase 7 XP Breakdown/Progress tab
  integration point for later arcade summaries
- Phase 6/7 outputs — `CurriculumService.award_xp(profile_id, source_type,
  source_id, amount)`, level display, and skill tree UI contracts supplied by
  earlier phases
</canonical_refs>

<code_context>
## Existing Code Insights

### MainWindow integration seam
- `MainWindow._tick()` already drains all queued `AnalysisResult` objects on the
  Qt thread and updates widgets. Arcade delivery should piggyback on that same
  loop instead of adding a second queue or second timer.
- `MainWindow` currently owns tab creation directly. Adding Arcade should follow
  the same pattern as Analysis / Exercises / Progress / Settings.

### Storage conventions to preserve
- Storage modules use `structlog`, open/close their own SQLite connections, and
  rely on `get_connection()` per method. `ArcadeRepository` must match this.
- Migrations use named constants, `PRAGMA user_version`, and ordered `if`
  migration blocks. Phase 11 should add a new schema version block for
  `arcade_scores`; never reorder prior migrations.

### Testing seams already present
- Qt widgets are tested with `pytest-qt` and offscreen rendering.
- Existing code prefers self-contained widgets with explicit constructor
  dependencies (`db_path`, `settings_path`). `ArcadePanel` and game-over widgets
  should follow the same style for easier tests.
</code_context>

<pitfalls>
## Pitfalls and Constraints

- **Do not run DSP in the game loop.** Games only consume `AnalysisResult`; they
  never call `estimate_f0()`, `estimate_formants()`, or other audio modules.
- **Do not block `_tick()`.** Game updates must stay light enough that Analysis,
  Progress, and other tabs remain responsive at 33 ms timer cadence.
- **Avoid hidden pause bugs.** If a game keeps advancing while the Arcade tab is
  not current, users will lose runs unfairly.
- **Do not encode game IDs in SQL enums or switch-heavy schema logic.** Phases
  12–13 need additive game registration.
- **Be careful with `profile_id`.** Curriculum APIs already accept it, but
  formal multi-profile support arrives in Phase 15. Repository APIs should keep
  `profile_id` explicit and future-friendly.
- **No external animation libraries.** All motion/celebration should remain Qt /
  QPainter / QTimer driven.
</pitfalls>

<open_questions>
## Open Questions / Assumptions

- **Current profile source:** The post-Phase-10 codebase must expose an active
  `profile_id` source before XP can be awarded. Planning assumes that contract
  already exists alongside `CurriculumService`; if it does not, Phase 11 needs a
  tiny adapter for the current default profile.
- **Launcher tile art:** Planning assumes icons can be simple emoji or bundled
  SVG/PNG assets and does not require commissioned artwork.
- **Locked tiles:** Recommended default is to show future game tiles as locked so
  the launcher layout is stable before Phases 12–13 land.
</open_questions>

<deferred>
## Deferred Ideas

- Cross-game combo bonuses or daily arcade quests — defer until the base arcade
  loop is proven fun and readable.
- Online leaderboards or social comparison — permanently out of scope for this
  privacy-first desktop app.
- Audio recording inside arcade games — defer unless a later phase explicitly
  needs replay.
</deferred>

---

*Phase: 11-arcade-infrastructure*
*Context gathered: 2026-05-30 for phase planning*
