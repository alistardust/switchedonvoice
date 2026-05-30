---
phase: 12-resonance-drill
plan: 01
type: execute
waves:
  - 1
  - 2
  - 3
depends_on:
  - 11-arcade-infrastructure
files_expected:
  - src/switchedonvoice/arcade/games/resonance_drill.py
  - src/switchedonvoice/arcade/games/vowel_shaping.py
  - src/switchedonvoice/arcade/launcher.py
  - src/switchedonvoice/ui/arcade_panel.py
  - src/switchedonvoice/ui/progress_panel.py
  - tests/arcade/test_resonance_drill.py
  - tests/arcade/test_vowel_shaping.py
  - tests/ui/test_arcade_panel.py
autonomous: true
requirements:
  - REQ-A02
  - REQ-A04
---

<objective>
Add two formant-control arcade games — Resonance Drill and Vowel Shaping — using
Phase 11's arcade runtime, persistence, and XP infrastructure, while keeping the
vowel-space math testable and reusable.
</objective>

<architecture>
## File Structure and Responsibilities

- `src/switchedonvoice/arcade/games/resonance_drill.py` — bullseye target game,
  quadrant cycling, dwell scoring, and snap-flash animation state
- `src/switchedonvoice/arcade/games/vowel_shaping.py` — vowel centroid metadata,
  normalization helpers, bubble targets, distance matching, and particle state
- `src/switchedonvoice/arcade/launcher.py` — add two new game registrations and
  lock/unlock metadata
- `src/switchedonvoice/ui/arcade_panel.py` — route launcher clicks to the new
  games and reuse the shared game-over flow
- `src/switchedonvoice/ui/progress_panel.py` — only if needed to ensure arcade XP
  events remain visible in the existing XP Breakdown views
- Tests split into pure gameplay math + widget integration
</architecture>

<waves>
## Wave 1 — Pure gameplay math first

### Task 1: Implement normalized vowel-space helpers and Resonance Drill scoring

**Files:**
- Create: `src/switchedonvoice/arcade/games/resonance_drill.py`
- Test: `tests/arcade/test_resonance_drill.py`

**Steps:**
- [ ] Write failing tests for quadrant anchor selection, difficulty-driven target
      cycling cadence, dwell-time accumulation, and ignoring unvoiced/empty-
      formant frames.
- [ ] Run `pytest tests/arcade/test_resonance_drill.py -q` and confirm failure.
- [ ] Implement pure helpers for mapping formants into normalized/pixel space and
      determining whether the live centroid is inside the bullseye radius.
- [ ] Implement the Resonance Drill subclass using those helpers, with explicit
      difficulty constants and snap-flash animation state.
- [ ] Re-run `pytest tests/arcade/test_resonance_drill.py -q`.
- [ ] Commit the Resonance Drill logic slice.

**Acceptance criteria:**
- Dwell time increases only while voiced formants stay inside the bullseye.
- Difficulty affects target cycling speed predictably.
- Target quadrants cover the four required positions.
- Snap flash can be asserted via state/time rather than visual guesswork.

### Task 2: Implement vowel normalization and proximity matching

**Files:**
- Create: `src/switchedonvoice/arcade/games/vowel_shaping.py`
- Test: `tests/arcade/test_vowel_shaping.py`

**Steps:**
- [ ] Write failing tests for F1/F2 normalization, centroid metadata, boundary
      matching (`0.11` hit, `0.13` miss), and pop scoring behavior.
- [ ] Run `pytest tests/arcade/test_vowel_shaping.py -q` and confirm failure.
- [ ] Implement explicit vowel target definitions for `/iː/, /æ/, /ɑː/, /uː/,
      /ɛ/, /ɔː/`.
- [ ] Implement the normalization helper using reference ranges F1 200–900 Hz and
      F2 700–2800 Hz plus Euclidean distance matching.
- [ ] Add particle-effect state objects driven by the main game timer.
- [ ] Re-run `pytest tests/arcade/test_vowel_shaping.py -q`.
- [ ] Commit the Vowel Shaping logic slice.

**Acceptance criteria:**
- Normalization math is test-covered and pure.
- Matching threshold behaves exactly at the named boundaries.
- Bubble-pop effect is represented as deterministic state that can be painted.
- The game has explicit metadata for each vowel target instead of anonymous tuples.

## Wave 2 — UI integration and launcher wiring

### Task 3: Register both games in the launcher and Arcade panel

**Files:**
- Modify: `src/switchedonvoice/arcade/launcher.py`
- Modify: `src/switchedonvoice/ui/arcade_panel.py`
- Test: `tests/ui/test_arcade_panel.py`

**Steps:**
- [ ] Extend or write failing widget tests for launcher tiles, game creation
      routes, and returning to the launcher after each game-over.
- [ ] Run `pytest tests/ui/test_arcade_panel.py -q`.
- [ ] Register Resonance Drill and Vowel Shaping in launcher metadata with game
      IDs, labels, icons, and lock state.
- [ ] Update `ArcadePanel` factory logic so each tile instantiates the correct
      `ArcadeGame` subclass.
- [ ] Re-run `pytest tests/ui/test_arcade_panel.py -q`.
- [ ] Commit the launcher integration.

**Acceptance criteria:**
- Both games appear on the launcher grid.
- Launcher click flow works without special-casing outside metadata/factory code.
- Existing Pitch Targeting behavior does not regress.

## Wave 3 — XP, progression, and end-to-end polish

### Task 4: Wire scoring into repository + XP + Progress feedback

**Files:**
- Modify: `src/switchedonvoice/arcade/games/resonance_drill.py`
- Modify: `src/switchedonvoice/arcade/games/vowel_shaping.py`
- Modify: `src/switchedonvoice/ui/arcade_panel.py`
- Possibly modify: `src/switchedonvoice/ui/progress_panel.py`
- Test: `tests/arcade/test_resonance_drill.py`
- Test: `tests/arcade/test_vowel_shaping.py`
- Test: `tests/ui/test_arcade_panel.py`

**Steps:**
- [ ] Add failing tests for XP award metadata, per-game score persistence, and
      launcher/game-over updates after successful runs.
- [ ] Run targeted pytest commands and capture failures.
- [ ] Reuse Phase 11 repository/XP hooks to save both games' scores and emit XP
      events tied to the Resonance skill branch.
- [ ] Ensure game-over summaries include score and XP earned for both games.
- [ ] Re-run targeted tests, then the full arcade test subset.
- [ ] Commit the final Phase 12 slice.

**Acceptance criteria:**
- Both games save scores and award XP through the shared path.
- XP events show up where the rest of the app expects them.
- Max difficulty remains playable but clearly faster/harder than low tiers.
- Phase 11 launcher/runtime tests stay green.
</waves>

<test_strategy>
## Test Strategy

- **Pure math tests:** formant normalization, quadrant anchor selection, target
  cycling cadence, dwell accumulation, and vowel-distance boundary behavior.
- **Subclass gameplay tests:** state changes from live audio frames, pop/flash
  animation state creation, and final score generation.
- **UI tests:** launcher grid includes both new games and routes into them.
- **Regression pass:** run the Phase 11 arcade suite plus the new Phase 12 tests,
  then `ruff check src tests` and `mypy src`.
</test_strategy>

<completion>
## Completion Criteria

Phase 12 is complete when Resonance Drill and Vowel Shaping both launch from the
Arcade tab, respond correctly to live formants, produce persisted scores + XP,
and the normalization/distance/dwell logic is fully test-covered.
</completion>
