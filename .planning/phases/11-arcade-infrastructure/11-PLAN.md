---
phase: 11-arcade-infrastructure
plan: 01
type: execute
waves:
  - 1
  - 2
  - 3
depends_on:
  - 06-curriculum-schema
  - 07-skill-tree-ui
files_expected:
  - src/switchedonvoice/storage/db.py
  - src/switchedonvoice/arcade/__init__.py
  - src/switchedonvoice/arcade/models.py
  - src/switchedonvoice/arcade/repository.py
  - src/switchedonvoice/arcade/base.py
  - src/switchedonvoice/arcade/launcher.py
  - src/switchedonvoice/arcade/games/__init__.py
  - src/switchedonvoice/arcade/games/pitch_targeting.py
  - src/switchedonvoice/ui/arcade_panel.py
  - src/switchedonvoice/ui/main_window.py
  - tests/storage/test_arcade_repository.py
  - tests/arcade/test_arcade_game_base.py
  - tests/arcade/test_pitch_targeting.py
  - tests/ui/test_arcade_panel.py
autonomous: true
requirements:
  - REQ-A01
  - REQ-A06
---

<objective>
Create the arcade foundation for Milestone v1.3: add the Arcade tab, persist all
arcade scores, define the shared `ArcadeGame` runtime, and ship Pitch Targeting
as a fully playable 60-second game with tiered difficulty and XP rewards.
</objective>

<architecture>
## File Structure and Responsibilities

- `src/switchedonvoice/storage/db.py` — schema migration adding `arcade_scores`
- `src/switchedonvoice/arcade/models.py` — small dataclasses/enums shared across
  repository, launcher, and games (difficulty config, result summary, game
  metadata)
- `src/switchedonvoice/arcade/repository.py` — `ArcadeRepository` CRUD and
  aggregate queries; one connection per method
- `src/switchedonvoice/arcade/base.py` — `ArcadeGame` base widget and state
  machine; timer-driven loop; audio-frame contract; score finalisation hook
- `src/switchedonvoice/arcade/launcher.py` — launcher-grid tile metadata and
  tile widget helpers, isolated from top-level tab wiring
- `src/switchedonvoice/arcade/games/pitch_targeting.py` — Pitch Targeting game,
  tier definitions, target generation, scoring, and XP multiplier constant
- `src/switchedonvoice/ui/arcade_panel.py` — tab widget that switches between
  launcher, active game, and game-over summary
- `src/switchedonvoice/ui/main_window.py` — adds Arcade tab and forwards
  `AnalysisResult` frames to the active arcade game from `_tick()`
- Tests split by concern: repository, base runtime, game scoring, and UI wiring
</architecture>

<waves>
## Wave 1 — Data layer and shell

### Task 1: Add arcade score persistence

**Files:**
- Modify: `src/switchedonvoice/storage/db.py`
- Create: `src/switchedonvoice/arcade/__init__.py`
- Create: `src/switchedonvoice/arcade/models.py`
- Create: `src/switchedonvoice/arcade/repository.py`
- Test: `tests/storage/test_arcade_repository.py`

**Steps:**
- [ ] Write failing storage tests covering schema version bump, table creation,
      `save_score()`, `get_personal_best()`, and `get_recent_scores()` ordering.
- [ ] Run `pytest tests/storage/test_arcade_repository.py -q` and confirm the new
      repository/table expectations fail.
- [ ] Add a migration block for `arcade_scores` with columns
      `(id, profile_id, game_id, score, difficulty_level, earned_xp, played_at)`
      plus indexes on `(profile_id, game_id)` and `played_at`.
- [ ] Implement `ArcadeRepository` with per-method connection handling and a
      small result dataclass for returned score rows.
- [ ] Re-run `pytest tests/storage/test_arcade_repository.py -q` until green.
- [ ] Commit only the storage/repository slice.

**Acceptance criteria:**
- `save_score()` inserts one row per completed attempt.
- `get_personal_best(profile_id, game_id)` returns the highest score or `None`.
- `get_recent_scores(profile_id, game_id, n)` returns exactly `n` or fewer rows,
  oldest-first, suitable for future sparklines.
- Schema follows the existing migration pattern and remains idempotent.

### Task 2: Define the shared arcade runtime contract

**Files:**
- Create: `src/switchedonvoice/arcade/base.py`
- Update: `src/switchedonvoice/arcade/models.py`
- Test: `tests/arcade/test_arcade_game_base.py`

**Steps:**
- [ ] Write failing tests for `ArcadeGame` state transitions:
      `idle -> playing -> paused -> playing -> game_over`, timer stopping, and
      `on_audio_frame()` forwarding while active.
- [ ] Run `pytest tests/arcade/test_arcade_game_base.py -q` to verify the base
      API is still missing.
- [ ] Implement `ArcadeGame` as a `QWidget` with a private `QTimer`, elapsed-time
      accounting, `start_game()`, `pause_game()`, `resume_game()`, `stop_game()`,
      and `finish_game()` methods plus abstract hooks for subclasses.
- [ ] Add a simple state enum/dataclass contract so tests can assert public state
      without peeking into Qt timer internals.
- [ ] Re-run `pytest tests/arcade/test_arcade_game_base.py -q`.
- [ ] Commit the reusable runtime.

**Acceptance criteria:**
- The base class owns timer lifecycle and state changes.
- `finish_game()` emits enough result data for repository save + XP award.
- Pause/resume preserves elapsed game time instead of resetting the run.
- No audio/DSP code is duplicated outside `AnalysisResult` consumption.

## Wave 2 — Arcade tab and first game

### Task 3: Build the launcher and tab integration

**Files:**
- Create: `src/switchedonvoice/arcade/launcher.py`
- Create: `src/switchedonvoice/ui/arcade_panel.py`
- Modify: `src/switchedonvoice/ui/main_window.py`
- Test: `tests/ui/test_arcade_panel.py`

**Steps:**
- [ ] Write failing widget tests for launcher tile rendering, locked/unlocked
      presentation, tile click launching Pitch Targeting, and auto-pause when
      the Arcade tab loses focus.
- [ ] Run `pytest tests/ui/test_arcade_panel.py -q` and confirm failures.
- [ ] Implement launcher metadata (game id, display name, icon, lock state,
      personal best summary) and a responsive tile grid widget.
- [ ] Implement `ArcadePanel` to own launcher view, active-game view, and
      game-over summary view.
- [ ] Add the Arcade tab to `MainWindow` and forward `AnalysisResult` objects from
      `_tick()` into `ArcadePanel.on_audio_frame(result)`.
- [ ] Wire tab-change/visibility hooks so leaving the Arcade tab pauses an active
      game without discarding the run.
- [ ] Re-run `pytest tests/ui/test_arcade_panel.py -q`.
- [ ] Commit the shell integration.

**Acceptance criteria:**
- The main window now includes an Arcade tab.
- Pitch Targeting appears as a playable tile; future games can appear locked.
- Active games receive live `AnalysisResult` frames from the existing UI timer.
- Leaving the tab pauses the run instead of letting time continue invisibly.

### Task 4: Implement Pitch Targeting gameplay

**Files:**
- Create: `src/switchedonvoice/arcade/games/__init__.py`
- Create: `src/switchedonvoice/arcade/games/pitch_targeting.py`
- Update: `src/switchedonvoice/ui/arcade_panel.py`
- Test: `tests/arcade/test_pitch_targeting.py`

**Steps:**
- [ ] Write failing tests for exact tier parameters (1–5), target generation,
      dwell accumulation, accuracy calculation, and final score normalisation.
- [ ] Run `pytest tests/arcade/test_pitch_targeting.py -q` and confirm failure.
- [ ] Implement named tier configs covering the required widths, speeds, hold
      durations, and simultaneous-target counts.
- [ ] Implement pitch-band target generation on a scrolling timeline, live F0
      trace capture from `AnalysisResult.f0`, and hit detection using cents-based
      distance to the current target band.
- [ ] Implement the 60-second game duration, score accumulation
      (`accuracy% * dwell bonus`), and game-over summary payload.
- [ ] Re-run `pytest tests/arcade/test_pitch_targeting.py -q`.
- [ ] Commit the first playable game.

**Acceptance criteria:**
- Tier 1 = 50 cents / 50 px/s / 0.5 s / 1 target.
- Tier 5 = 10 cents / 200 px/s / 2.0 s / 3 simultaneous targets.
- The live pitch trace is visible while playing.
- Holding pitch in-band affects score in a testable, deterministic way.

## Wave 3 — XP, game-over UX, and integration hardening

### Task 5: Award XP and finish the game-over flow

**Files:**
- Modify: `src/switchedonvoice/arcade/base.py`
- Modify: `src/switchedonvoice/arcade/games/pitch_targeting.py`
- Modify: `src/switchedonvoice/ui/arcade_panel.py`
- Possibly modify: `src/switchedonvoice/ui/progress_panel.py` (only if Phase 7
  integration requires a refresh hook)
- Test: `tests/arcade/test_pitch_targeting.py`
- Test: `tests/ui/test_arcade_panel.py`

**Steps:**
- [ ] Write/extend failing tests for score-to-XP conversion, repository save
      occurring before celebration state, and game-over rendering of score,
      accuracy percent, XP earned, and personal-best flag.
- [ ] Run targeted pytest commands to capture failures.
- [ ] Add a reusable XP helper using the shared formula shape and Pitch
      Targeting's class-level XP multiplier.
- [ ] On game completion, save the score, award XP through `CurriculumService`,
      and show the animated game-over summary.
- [ ] Refresh launcher personal best state after each completed run.
- [ ] Re-run targeted tests, then `pytest tests/storage/test_arcade_repository.py tests/arcade/test_arcade_game_base.py tests/arcade/test_pitch_targeting.py tests/ui/test_arcade_panel.py -q`.
- [ ] Commit the final Phase 11 slice.

**Acceptance criteria:**
- Every completed run persists a score row and an XP event.
- Game-over screen shows score, accuracy %, XP earned, and personal best state.
- Personal best updates immediately on returning to the launcher.
- XP logic is shared-structure, game-specific-multiplier driven.
</waves>

<test_strategy>
## Test Strategy

- **Repository tests:** schema creation, insert/query semantics, personal-best
  max query, and recent-score ordering.
- **Base runtime tests:** deterministic state transitions, paused timer behavior,
  and audio-frame forwarding.
- **Game logic tests:** exact difficulty tier values, target hit detection,
  dwell scoring, and score-to-XP conversion.
- **Qt widget tests:** launcher rendering, tile click flow, pause on tab switch,
  and game-over summary visibility.
- **Regression pass:** `pytest -q`, `ruff check src tests`, and `mypy src` after
  the final wave because this phase adds public APIs and UI integration points.
</test_strategy>

<completion>
## Completion Criteria

Phase 11 is complete when all of the following are true:
- Arcade tab exists in the main window and Pitch Targeting launches from it.
- The game plays for 60 seconds with visible falling targets and live F0 trace.
- Difficulty tiers 1–5 match the specified widths/speeds/holds/target counts.
- Game-over persists score, awards XP, and reports personal-best state.
- The new repository, runtime, UI, and game tests all pass, and full lint/type/
  pytest verification is clean.
</completion>
