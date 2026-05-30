# Phase 12: Resonance Drill + Vowel Shaping - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 12 adds the first two formant-driven arcade games on top of Phase 11's
Arcade tab, repository, and `ArcadeGame` lifecycle. It must prove that the
arcade foundation supports non-pitch mechanics cleanly: target cycling on the
vowel plane, dwell-based resonance scoring, and target matching against named
vowel centroids.

This phase should not redesign launcher infrastructure, score persistence, or XP
plumbing. It should add two new games that feel distinct while sharing the same
base runtime and game-over flow.
</domain>

<decisions>
## Implementation Decisions

### Reuse of existing vowel-space rendering
- **D-12-01:** Reuse the existing vowel-space visual language from
  `ui/vowel_space.py` rather than inventing a new coordinate system. If the
  existing widget is too tightly coupled for direct reuse, extract pure mapping
  helpers or a lightweight painter helper into the arcade package.
- **D-12-02:** Keep all game-specific overlays (bullseye ring, bubbles, particle
  bursts, snap flash) inside arcade game modules so the shared vowel-space widget
  does not become game-aware.

### Resonance Drill mechanics
- **D-12-03:** Score is primarily dwell time inside a moving bullseye radius,
  using the current voiced formant centroid from `AnalysisResult.formants`.
- **D-12-04:** Quadrant targets are explicit normalized anchor points
  (front/high, front/low, back/high, back/low), cycled by difficulty-driven
  cadence constants. The game should not randomize arbitrary coordinates yet;
  tactile repetition matters more than entropy.
- **D-12-05:** The snap flash is a short-lived QPainter animation state driven by
  elapsed time in the game loop; no external animation framework.

### Vowel Shaping mechanics
- **D-12-06:** Vowel matching uses normalized F1/F2 coordinates on `[0,1]` with
  fixed reference ranges: F1 200–900 Hz, F2 700–2800 Hz.
- **D-12-07:** A Euclidean distance `< 0.12` is a hit. Boundary tests must prove
  `0.11` matches and `0.13` misses.
- **D-12-08:** IPA targets are explicit metadata rows (symbol, display label,
  normalized centroid, optional color/icon), not ad hoc tuples embedded in paint
  code. Future curriculum or coaching phases may reuse these centroids.

### XP and curriculum integration
- **D-12-09:** Both games reuse the Phase 11 XP helper shape and declare their
  own class constants for `GAME_ID`, `GAME_XP_MULTIPLIER`, and linked skill IDs.
- **D-12-10:** Resonance Drill and Vowel Shaping should both contribute to the
  Resonance branch, but keep mappings additive and data-like so later balancing
  does not require DB schema changes.
</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md` — REQ-A02 and REQ-A04
- `.planning/ROADMAP.md` §Phase 12 — canonical task list and success criteria
- `.planning/phases/11-arcade-infrastructure/11-CONTEXT.md` — base runtime,
  score storage, and XP-shape decisions this phase builds on
- `src/switchedonvoice/audio/capture.py` — source of voiced formant data through
  `AnalysisResult.formants`
- `src/switchedonvoice/ui/vowel_space.py` — current vowel-space rendering and
  coordinate conventions to reuse or extract from
</canonical_refs>

<code_context>
## Existing Code Insights

- By Phase 12, `ArcadeGame` should already provide timer lifecycle, audio-frame
  delivery, pause/resume handling, and result finalisation. These games should be
  thin subclasses with formant-specific state.
- `AnalysisResult.formants` may be empty for unvoiced frames. Both games must
  treat missing formants as "no cursor update" rather than as `(0, 0)`.
- Progress/XP UI already exists from Phases 6–7. Arcade should emit standard XP
  events instead of inventing a separate reward channel.
</code_context>

<pitfalls>
## Pitfalls and Constraints

- **Do not hard-code raw Hz coordinates in paint logic.** Normalize first, then
  map to pixels, so tests can assert math without involving QPainter.
- **Do not score unvoiced frames.** Empty formants should neither move the cursor
  nor incorrectly pop targets.
- **Avoid coupling to one visual widget class if it makes testing hard.** Put
  coordinate transforms in pure helpers where possible.
- **Particle and flash effects must degrade gracefully offscreen.** Tests should
  validate state changes, not human-perceived animation polish.
</pitfalls>

<open_questions>
## Open Questions / Assumptions

- **Vowel target set:** The roadmap names `/iː/, /æ/, /ɑː/, /uː/, /ɛ/, /ɔː/`.
  Planning assumes those six are sufficient for Phase 12 and that additional
  vowels can wait until later content balancing.
- **Reuse vs extraction of `VowelSpaceWidget`:** Preferred default is extraction
  of pure mapping/math helpers if the widget is too tied to the Analysis tab.
</open_questions>

<deferred>
## Deferred Ideas

- Adaptive vowel targets based on each user's baseline tract profile — defer
  until more resonance history exists.
- Multi-target combo chains or bubble streak bonuses — defer until fun/clarity of
  the basic mechanic is validated.
</deferred>

---

*Phase: 12-resonance-drill*
*Context gathered: 2026-05-30 for phase planning*
