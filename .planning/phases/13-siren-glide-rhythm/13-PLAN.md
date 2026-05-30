---
phase: 13-siren-glide-rhythm
plan: 01
type: execute
waves:
  - 1
  - 2
  - 3
depends_on:
  - 11-arcade-infrastructure
files_expected:
  - src/switchedonvoice/arcade/games/siren_glide.py
  - src/switchedonvoice/arcade/games/rhythm_cadence.py
  - src/switchedonvoice/arcade/launcher.py
  - src/switchedonvoice/ui/arcade_panel.py
  - tests/arcade/test_siren_glide.py
  - tests/arcade/test_rhythm_cadence.py
  - tests/ui/test_arcade_panel.py
autonomous: true
requirements:
  - REQ-A03
  - REQ-A05
---

<objective>
Add Siren Glide and Rhythm & Cadence as the final two v1.3 arcade games, with
pure, testable helpers for glide deviation, glottal-break penalties, onset
extraction, and DTW rhythm scoring.
</objective>

<architecture>
## File Structure and Responsibilities

- `src/switchedonvoice/arcade/games/siren_glide.py` — target path generation,
  semitone RMS error, voiced-gap penalty logic, and Siren Glide widget behavior
- `src/switchedonvoice/arcade/games/rhythm_cadence.py` — prompt metadata,
  envelope/onset extraction, DTW alignment, pacing subscores, and game widget
- `src/switchedonvoice/arcade/launcher.py` — register the two new games
- `src/switchedonvoice/ui/arcade_panel.py` — launch routing only, reusing the
  shared result/XP flow
- Tests isolate signal math from Qt integration as much as possible
</architecture>

<waves>
## Wave 1 — Siren Glide signal math

### Task 1: Implement path generation and glide scoring helpers

**Files:**
- Create: `src/switchedonvoice/arcade/games/siren_glide.py`
- Test: `tests/arcade/test_siren_glide.py`

**Steps:**
- [ ] Write failing tests for target-path generation, semitone RMS deviation on a
      synthetic F0 sequence, and glottal-break penalty calculation.
- [ ] Run `pytest tests/arcade/test_siren_glide.py -q`.
- [ ] Implement pure helpers for target pitch at elapsed time, semitone
      conversion, RMS deviation, and voiced-gap duration tracking.
- [ ] Implement the Siren Glide game subclass and paint state using those helpers.
- [ ] Re-run `pytest tests/arcade/test_siren_glide.py -q`.
- [ ] Commit the Siren Glide math/runtime slice.

**Acceptance criteria:**
- A smoother synthetic glide scores better than one with larger deviations.
- Voiced breaks reduce score proportionally to break duration.
- Game-over summary includes both score and deviation value.

## Wave 2 — Rhythm & Cadence timing analysis

### Task 2: Implement onset extraction and DTW rhythm scoring

**Files:**
- Create: `src/switchedonvoice/arcade/games/rhythm_cadence.py`
- Test: `tests/arcade/test_rhythm_cadence.py`

**Steps:**
- [ ] Write failing tests for onset extraction from synthetic RMS envelopes,
      session-max thresholding, DTW alignment scoring, and separate rushing vs
      dragging diagnostics.
- [ ] Run `pytest tests/arcade/test_rhythm_cadence.py -q`.
- [ ] Implement pure helper functions for envelope peak-picking, target phrase
      metadata, DTW cost calculation, and score derivation.
- [ ] Implement the Rhythm & Cadence widget around those helpers using
      `AnalysisResult.raw_audio` buffers.
- [ ] Re-run `pytest tests/arcade/test_rhythm_cadence.py -q`.
- [ ] Commit the rhythm-analysis slice.

**Acceptance criteria:**
- Synthetic onsets are detected deterministically.
- DTW score distinguishes well-timed, rushed, and dragged readings.
- Combined score remains 0–100 while preserving diagnostic subscores.

## Wave 3 — Launcher integration, XP, and regression hardening

### Task 3: Register both games and complete end-to-end flow

**Files:**
- Modify: `src/switchedonvoice/arcade/launcher.py`
- Modify: `src/switchedonvoice/ui/arcade_panel.py`
- Modify: `src/switchedonvoice/arcade/games/siren_glide.py`
- Modify: `src/switchedonvoice/arcade/games/rhythm_cadence.py`
- Test: `tests/ui/test_arcade_panel.py`
- Test: `tests/arcade/test_siren_glide.py`
- Test: `tests/arcade/test_rhythm_cadence.py`

**Steps:**
- [ ] Extend failing UI tests so the launcher includes Siren Glide and Rhythm &
      Cadence and both reach a game-over flow.
- [ ] Run `pytest tests/ui/test_arcade_panel.py -q`.
- [ ] Add launcher registrations, per-game XP multipliers, and skill-link
      metadata (Pitch/Clarity for Siren, Intonation for Rhythm).
- [ ] Ensure both games save scores and award XP through the shared Phase 11 path.
- [ ] Re-run the full arcade subset, then `pytest -q`, `ruff check src tests`,
      and `mypy src`.
- [ ] Commit the final Phase 13 slice.

**Acceptance criteria:**
- Both games appear on the launcher and play end-to-end.
- Deliberate glottal breaks materially reduce Siren Glide score.
- Reading too fast/slow produces worse Rhythm & Cadence scores than a well-timed
  synthetic/control attempt.
- No Phase 11 or 12 behavior regresses.
</waves>

<test_strategy>
## Test Strategy

- **Pure signal tests:** semitone conversion, RMS path-deviation math, gap
  duration penalties, onset extraction, DTW alignment, and score breakdowns.
- **Subclass tests:** state updates when fed synthetic `AnalysisResult` objects.
- **UI tests:** launcher visibility and launch/game-over flow for the new games.
- **Full verification:** targeted arcade tests first, then repository-wide
  `pytest -q`, `ruff check src tests`, and `mypy src`.
</test_strategy>

<completion>
## Completion Criteria

Phase 13 is complete when Siren Glide and Rhythm & Cadence are both playable from
the launcher, use test-covered helper math for their analysis, and persist score
+ XP through the shared arcade infrastructure.
</completion>
