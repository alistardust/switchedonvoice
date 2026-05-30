# Phase 13: Siren Glide + Rhythm & Cadence - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 13 adds the two most analysis-heavy arcade games: one for continuous pitch
path following and glottal-break reduction, and one for phrase rhythm matching
using onset detection and DTW. Both games must still fit within the existing
`AnalysisResult` stream and Qt-driven arcade runtime rather than introducing a
parallel signal-processing subsystem.

This phase completes the four-game v1.3 launcher lineup promised by the roadmap.
It should leverage Phase 11's runtime contracts and Phase 12's discipline around
pure helper functions for testable signal math.
</domain>

<decisions>
## Implementation Decisions

### Siren Glide
- **D-13-01:** The target path is represented as a deterministic function of
  elapsed game time (e.g. sine/arc helper), not a pre-rendered image. This keeps
  both painting and RMS-deviation tests consistent.
- **D-13-02:** Accuracy uses semitone-domain RMS deviation between target pitch
  and observed user F0 so high and low notes are weighted perceptually rather
  than linearly in Hz.
- **D-13-03:** Glottal-break penalties are computed from contiguous voiced-gap
  duration during expected glide windows: 10% score penalty per 0.1 s of break,
  capped so scores cannot go negative.

### Rhythm & Cadence
- **D-13-04:** Phrase prompts and target timing patterns should be data objects
  (phrase text + target onset timestamps/stress groupings), not hard-coded paint
  literals. Future curriculum mapping may reuse them.
- **D-13-05:** Onset detection operates on RMS/energy envelopes derived from the
  already-available `raw_audio` buffer in `AnalysisResult`, avoiding a second
  microphone stream.
- **D-13-06:** Alignment uses DTW over onset timestamps so timing errors can be
  measured even when the user inserts/skips slight pauses.
- **D-13-07:** Score output should expose separate rushing and dragging sub-scores
  in addition to a combined 0–100 value so game-over feedback is actionable.

### Runtime fit
- **D-13-08:** Heavy helper math (path generation, RMS/onset extraction, DTW)
  belongs in pure module-level functions or light helper dataclasses inside the
  game modules. The Qt paint/tick path should consume precomputed state.
- **D-13-09:** Both games continue to save via `ArcadeRepository` and award XP
  with per-game multipliers through the shared Phase 11 formula shape.
</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md` — REQ-A03 and REQ-A05
- `.planning/ROADMAP.md` §Phase 13 — canonical tasks and success criteria
- `.planning/phases/11-arcade-infrastructure/11-CONTEXT.md` — runtime and XP
  rules that still govern these games
- `src/switchedonvoice/audio/capture.py` — provides `f0`, `is_voiced`, and
  `raw_audio` used by both games
- Any Phase 9/10 curriculum or recommendation assets that define reusable phrase
  content, if available by the time implementation starts
</canonical_refs>

<code_context>
## Existing Code Insights

- `AnalysisResult.raw_audio` already carries the 200 ms analysis buffer used for
  waveform display. Rhythm & Cadence should reuse that payload instead of adding
  a second capture channel.
- `AnalysisResult.is_voiced` provides a direct glottal-break signal candidate for
  Siren Glide; gap duration logic should build on it instead of re-detecting
  voicing from scratch.
- By this point, the launcher, repository, and game-over infrastructure already
  exist. The real implementation risk is mathematical correctness and keeping the
  UI responsive while those calculations run every frame.
</code_context>

<pitfalls>
## Pitfalls and Constraints

- **Do not compare glide error in raw Hz.** That over-penalizes higher pitches
  and breaks the perceptual intent of the exercise.
- **Do not let DTW/onset code hide inside widget methods.** Those algorithms need
  isolated unit tests on synthetic signals.
- **Beware empty/unvoiced buffers.** Both games must handle sparse voiced input
  without dividing by zero or fabricating timing events.
- **Avoid prompt-content sprawl.** Phase 13 needs enough phrases to ship a game,
  not a full authored content library.
</pitfalls>

<open_questions>
## Open Questions / Assumptions

- **Prompt phrase source:** Planning assumes a small built-in prompt set can live
  with the game module or an adjacent data file. A larger authored library is out
  of scope for this phase.
- **DTW implementation:** If no dependency already exists, use a small internal
  DP implementation rather than adding a new package just for one algorithm.
</open_questions>

<deferred>
## Deferred Ideas

- Stress-pattern coaching beyond onset timing (intonation contour coaching,
  lexical stress classification) — defer until a later speaking-prosody phase.
- Adaptive personalized glide paths based on the user's historical range — defer
  until enough arcade history exists.
</deferred>

---

*Phase: 13-siren-glide-rhythm*
*Context gathered: 2026-05-30 for phase planning*
