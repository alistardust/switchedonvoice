---
phase: 14-arcade-history
plan: 01
type: execute
waves:
  - 1
  - 2
  - 3
depends_on:
  - 11-arcade-infrastructure
  - 12-resonance-drill
  - 13-siren-glide-rhythm
files_expected:
  - pyproject.toml
  - src/switchedonvoice/arcade/repository.py
  - src/switchedonvoice/arcade/launcher.py
  - src/switchedonvoice/ui/arcade_panel.py
  - src/switchedonvoice/ui/progress_panel.py
  - tests/storage/test_arcade_repository.py
  - tests/ui/test_arcade_panel.py
  - tests/ui/test_progress_panel.py
autonomous: true
requirements:
  - REQ-A06
---

<objective>
Use stored arcade history to celebrate personal bests and visualize progress:
show best-state banners on game-over, last-10-attempt sparklines on launcher
tiles, arcade XP grouped by game, and a dedicated Arcade Statistics section in
Progress.
</objective>

<architecture>
## File Structure and Responsibilities

- `pyproject.toml` — add `pyqtgraph` only if it is still missing when work starts
- `src/switchedonvoice/arcade/repository.py` — extend with aggregate/statistics
  queries and helper methods for recent-history preparation
- `src/switchedonvoice/arcade/launcher.py` — tile-level sparkline data binding
- `src/switchedonvoice/ui/arcade_panel.py` — personal-best banner logic and live
  refresh after each completed run
- `src/switchedonvoice/ui/progress_panel.py` — Arcade Statistics section and XP
  Breakdown grouping/presentation updates
- Tests cover pure comparison/query logic and UI refresh behavior
</architecture>

<waves>
## Wave 1 — Repository aggregates and comparison helpers

### Task 1: Extend repository queries for history and statistics

**Files:**
- Modify: `src/switchedonvoice/arcade/repository.py`
- Test: `tests/storage/test_arcade_repository.py`

**Steps:**
- [ ] Write failing tests for strict-greater personal-best comparison, recent
      history preparation returning exactly up to 10 points oldest-first, and
      arcade statistics aggregation queries.
- [ ] Run `pytest tests/storage/test_arcade_repository.py -q`.
- [ ] Add repository/helper methods for per-game recent scores, total arcade
      sessions, most-played game, total arcade XP, and per-game personal bests.
- [ ] Re-run `pytest tests/storage/test_arcade_repository.py -q`.
- [ ] Commit the aggregate-query slice.

**Acceptance criteria:**
- Personal-best helper does not flag ties as new records.
- Sparkline data is oldest-first and capped at 10 points.
- Statistics queries return stable values even with mixed games and difficulties.

## Wave 2 — Game-over celebration and launcher sparklines

### Task 2: Add personal-best banners and per-tile history visuals

**Files:**
- Modify: `pyproject.toml` (if `pyqtgraph` missing)
- Modify: `src/switchedonvoice/arcade/launcher.py`
- Modify: `src/switchedonvoice/ui/arcade_panel.py`
- Test: `tests/ui/test_arcade_panel.py`

**Steps:**
- [ ] Write failing UI tests for the two banner states:
      `🏆 New personal best!` and `Your best: X — today: Y`, plus launcher
      sparkline refresh after a completed run.
- [ ] Run `pytest tests/ui/test_arcade_panel.py -q`.
- [ ] Add `pyqtgraph` if needed and implement a tiny read-only sparkline widget
      wrapper for launcher tiles.
- [ ] Update game-over rendering to use the strict-greater comparison helper and
      display the correct banner/message.
- [ ] Trigger immediate launcher refresh after score save so the sparkline and
      best text update without navigation.
- [ ] Re-run `pytest tests/ui/test_arcade_panel.py -q`.
- [ ] Commit the launcher/celebration slice.

**Acceptance criteria:**
- New records show the trophy banner; ties and lower scores do not.
- Each launcher tile shows up to 10 attempts in order.
- Sparkline and best text update right after finishing a game.

## Wave 3 — Progress tab arcade statistics and XP Breakdown grouping

### Task 3: Surface arcade progress in Progress tab

**Files:**
- Modify: `src/switchedonvoice/ui/progress_panel.py`
- Possibly modify: `src/switchedonvoice/arcade/launcher.py` (shared display-name mapping)
- Test: `tests/ui/test_progress_panel.py`
- Test: `tests/storage/test_arcade_repository.py`

**Steps:**
- [ ] Write failing tests for Arcade Statistics totals, most-played game label,
      per-game best table rows, and XP Breakdown grouped by display game name.
- [ ] Run `pytest tests/ui/test_progress_panel.py -q`.
- [ ] Add a focused Arcade Statistics section to the Progress tab following the
      existing summary/table style.
- [ ] Update XP Breakdown preparation so arcade XP is grouped by game name.
- [ ] Re-run targeted tests, then `pytest -q`, `ruff check src tests`, and
      `mypy src`.
- [ ] Commit the final Phase 14 slice.

**Acceptance criteria:**
- Progress tab shows total arcade sessions, most-played game, total arcade XP,
  and a per-game best table.
- XP Breakdown clearly attributes arcade XP by game name.
- All four launcher tiles and Progress summaries stay in sync after new runs.
</waves>

<test_strategy>
## Test Strategy

- **Repository tests:** best comparison semantics, last-10 score preparation, and
  aggregate statistics queries.
- **Arcade panel tests:** banner state, sparkline refresh, and no-navigation
  update flow.
- **Progress panel tests:** rendered arcade totals and grouped XP breakdown data.
- **Verification:** targeted tests first, then full `pytest -q`, `ruff check src
  tests`, and `mypy src` after dependencies/UI changes settle.
</test_strategy>

<completion>
## Completion Criteria

Phase 14 is complete when the launcher visibly reflects recent history, beating a
record shows the correct banner, Progress tab arcade totals are accurate, and XP
Breakdown splits arcade gains by human-readable game name.
</completion>
