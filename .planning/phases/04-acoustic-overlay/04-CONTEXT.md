# Phase 4: Live Acoustic Feedback Overlay & Session Summary - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning after Phase 3 UI contracts land

<domain>
## Phase Boundary

Phase 4 adds live coaching to Reading Mode. While the user reads, the tab
should show the same acoustic core signals already available on the Analysis
tab (pitch, vowel space, spectrum) and attach those signals to words so the
user can see how each spoken word tracked against her target range.

At the end of a reading attempt, the app should persist “first” and “most
recent” acoustic outcomes for that passage and present a short plain-language
summary dialog.
</domain>

<decisions>
## Key Implementation Decisions

### Shared capture, no duplicate pipeline
- **D-04-01:** Reuse the single `AudioCapture` instance owned by
  `MainWindow`. Reading Mode should receive `AnalysisResult` frames through a
  panel method such as `update_result()` when active; it must not create or
  start its own capture object.
- **D-04-02:** Add explicit tab activation/deactivation routing in
  `MainWindow._tick()` so Reading widgets go idle when the tab is inactive.
  “Idle” should mean no UI updates and no accumulation of reading metrics,
  not tearing down and recreating the capture each time.

### Keep acoustic math out of widgets
- **D-04-03:** Implement per-word aggregation and session summary math in a
  pure module (for example `reading/feedback.py`) rather than inside Qt
  widgets. Input: active word index + `AnalysisResult`. Output: word-level
  score buckets, summary metrics, and verdict text.
- **D-04-04:** Colour a word only after that word is complete. The current
  active word should keep the Phase 3 cursor style; previously spoken words
  get post-hoc green/amber/red colouring. This avoids flicker and keeps the
  cursor visually distinct from the retrospective score.

### Persistence model
- **D-04-05:** Extend `reading_progress` with first/recent score columns on a
  new migration. “first_*” writes only once when null; “recent_*” overwrites
  on every completed reading attempt. Update all related columns in one DB
  transaction per completed attempt.
- **D-04-06:** Treat “complete attempt” as a panel-level event (for example,
  user reaches the final word and confirms/ends the passage), not as a side
  effect of visiting the passage. Score persistence should happen exactly
  once per attempt.

### Summary dialog
- **D-04-07:** The session summary dialog should derive its verdict sentence
  from score buckets, not raw thresholds copied into UI code. Keep the label
  logic centralised with the summary computation.
- **D-04-08:** Reuse the existing target F0 range from `Settings` as the
  primary scoring range. If Phase 2 passages carry
  `recommended_f0_target`, treat that as future/extensible data, not a
  required scoring dependency for this phase.
</decisions>

<architecture>
## Architecture Fit

- `audio/capture.py` already produces `AnalysisResult(f0, formants, cpp,
  spectrum, raw_audio)` at ~30 Hz. Phase 4 should consume that contract
  rather than inventing a second analysis path.
- `ui/analysis_panel.py` already composes `PitchMeterWidget`,
  `VowelSpaceWidget`, and `SpectrumWidget`. Reading Mode should reuse these
  widget classes inside a reading-specific overlay/panel rather than clone
  their paint logic.
- `health.py` is currently a pure module. Any reading-session warning logic
  should preserve that style: pure functions returning semantic warning
  levels; widgets just render the result.
- `ui/progress_panel.py` currently shows session-level history. Phase 4 is
  the first phase that needs passage-level score comparison in the app UI, so
  its plan must include where that comparison lives rather than stopping at
  persistence only.
</architecture>

<dependencies>
## Required Upstream Artifacts

Phase 4 assumes all of the following already exist and are stable:

- Phase 3 `ReadingPanel` with activation/deactivation hooks.
- Phase 3 word-index cursor state and bookmark persistence by `passage_slug`.
- Phase 2 `reading_progress` table, ready for a new migration that adds
  acoustic score columns.
- Phase 1 shared `AudioCapture` polling loop in `MainWindow` and reusable
  analysis widgets (`PitchMeterWidget`, `VowelSpaceWidget`,
  `SpectrumWidget`).

The same Phase 2 identity mismatch still applies here: if Phase 2 stores
progress by integer `passage_id` but Phase 3/4 use `passage_slug`, the score
persistence contract must be reconciled before implementation begins.
</dependencies>

<pitfalls>
## Critical Pitfalls to Avoid

- **Do not aggregate unvoiced frames as 0 Hz.** Words with no voiced frames
  should stay unscored / neutral rather than being treated as failed pitch.
- **Do not couple word advancement timing to audio frame rate.** The active
  word index changes according to the Reading UI; acoustic frames are merely
  sampled against that current index.
- **Do not write first/recent columns in separate transactions.** A partial
  update would make comparison views lie.
- **Do not recolour the current word on every frame.** Score colour should
  stabilise when the word is completed; otherwise the passage will flicker.
- **Do not leave Reading overlay widgets updating while the tab is hidden.**
  This wastes GUI work and makes tests around idle state unreliable.
- **Do not bury threshold values in UI classes.** Keep scoring thresholds in
  pure code so tests can cover them without Qt.
</pitfalls>

<open_questions>
## Open Questions Before Execution

1. **`health.py` mismatch:** the current checked-in `health.py` only models
   elapsed-time rest warnings, not CPP strain warnings. The brief says “reuse
   existing `health.py` logic,” so Phase 4 needs a concrete decision: extend
   `health.py` with CPP helpers, or add a new pure health module and keep the
   time-based warning separate.
2. **Progress tab UX:** where exactly should “first vs most recent” passage
   scores appear? `ProgressPanel` currently has only session-level tables and
   charts. A small dedicated reading-progress section is likely sufficient,
   but it needs an explicit design.
3. **Passage completion trigger:** is completion automatic when the user
   advances past the last word, or should there be an explicit “Finish
   passage” action before summary/persistence? Automatic completion is
   simpler, but must be confirmed.
</open_questions>

---

*Phase: 04-acoustic-overlay*
*Context gathered: 2026-05-30*
