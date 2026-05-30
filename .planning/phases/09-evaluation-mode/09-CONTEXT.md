# Phase 9: Evaluation Mode + Report Card - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase adds a formal assessment workflow on top of Reading Mode. The user
chooses a passage, enters a no-hints evaluation run, completes the reading,
and receives a scored report card plus longitudinal trend data for that same
passage.

Evaluation mode should feel meaningfully different from ordinary practice:
same analysis pipeline, but no live coaching overlays during the run.
</domain>

<decisions>
## Key Decisions

- **D-09-01:** Evaluation mode suppresses visible feedback only; it does not
  disable underlying audio analysis. The existing pipeline continues collecting
  F0/formant/CPP data in the background for scoring.
- **D-09-02:** Evaluation results are stored by `passage_slug`, not numeric
  passage ID, matching the project context and keeping history stable across
  future content migrations.
- **D-09-03:** Score computation should be split into pure per-dimension
  functions plus a thin orchestration service. This makes the report card and
  trend graph trustworthy and testable.
- **D-09-04:** Evaluation recording ignores the ordinary recording preference
  and always captures the full run silently.
- **D-09-05:** XP for evaluations should be derived from the mean of the five
  normalised dimension scores (`average_score * 100`) and awarded through
  `CurriculumService`, not directly via UI code.

- **D-09-06:** Use a fixed feminine reference ellipse for v1.2 resonance scoring
  until personal baselines are deliberately introduced: centroid `(F1=450,
  F2=1650)` with radii `(180, 420)`, score derived from normalised ellipse
  distance and clamped to `[0, 1]`.
- **Reasoning:** The requirement needs a concrete scoring rule now;
  personalisation can be layered in later without changing the storage shape.

- **D-09-07:** Pacing uses a deterministic local heuristic syllable estimator
  over the selected passage text (vowel-group counting with silent-e handling)
  and computes syllables per minute from estimated syllables divided by
  recording duration. If Phase 2 later adds a canonical syllable_count field, the
  scorer should prefer that persisted value.
- **Reasoning:** Pacing cannot be left unspecified; this gives implementation a
  concrete offline method with a clean upgrade path.

- **D-09-08:** Evaluation recordings must be tagged `recording_kind =
  "evaluation"` (or an equivalent metadata flag in the Phase 5 recording model)
  and filtered out of ordinary practice-history lists by default.
- **Reasoning:** Graded evaluations are a distinct artifact type and should not be
  mixed silently into practice playback history.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/REQUIREMENTS.md` — REQ-C03 and REQ-C05
- `.planning/ROADMAP.md` §Phase 9 — canonical scope and success criteria
- `.planning/phases/04-acoustic-overlay/04-PLAN.md` — existing passage-score
  flow and overlay assumptions
- `.planning/phases/05-recording-playback/05-PLAN.md` — recording pipeline and
  `reading_panel.py` integration points
- `.planning/phases/06-curriculum-schema/06-PLAN.md` — XP service contract
- `src/switchedonvoice/ui/progress_panel.py` — current trend/history container

</canonical_refs>

<architecture>
## Architecture Fit

### Expected touch points from prior phases
- Reading UI module from Phases 3–5 (expected to own passage header, reading
  controls, and overlay visibility)
- recording subsystem from Phase 5 for silent capture reuse
- `ProgressPanel` from Phase 7 for embedding the evaluation trend graph
- `CurriculumService` from Phase 6 for XP crediting

### Recommended new modules
- `storage/evaluations.py` — persistence and history queries
- `evaluation/scoring.py` — pure score calculators + plain-language summaries
- `evaluation/service.py` — run orchestration, storage, and XP award
- `ui/report_card_dialog.py` — post-run results display
- `ui/evaluation_trend_widget.py` — pyqtgraph-based multi-line chart

### Dependency note
`pyqtgraph` is not currently in `pyproject.toml`. If no existing dependency has
introduced it by the time this phase begins, Phase 9 should add it explicitly.
</architecture>

<pitfalls>
## Pitfalls to Avoid

- Do not leak live hints into evaluation mode through reused widgets or stale
  labels. Hidden must mean hidden for the full run.
- Do not couple scoring to paint-time UI state. The report card must be
  reproducible from persisted analysis data.
- Do not use local time strings without a consistent format; evaluation trend
  ordering depends on stable timestamps.
- Do not make pacing depend on unavailable metadata. If syllable counts are not
  already persisted with passages, Phase 9 needs a deterministic estimator.
- Do not forget that `record_by_default` is overridden in evaluation mode.
</pitfalls>

<dependencies>
## Specific Dependencies on Earlier Phases

- **Phase 4:** provides passage-level pitch/resonance/CPP scoring context and
  overlay controls that must be disabled in evaluation mode
- **Phase 5:** provides recording pipeline reuse for silent evaluation capture
- **Phase 6/7:** provide XP accounting and a visible XP breakdown panel that
  should reflect evaluation awards
- **Phase 2:** `storage/books.py` and passage slugs are the anchor for history
  grouping and FK integrity
</dependencies>

<deferred>
## Deferred Ideas

- Personalised resonance targets derived from onboarding or prior successful
  evaluations. Defer until the fixed ellipse has baseline validation data.
- Multi-passage comparison dashboards inside the report card. Phase 9 only needs
  same-passage trends in the Progress tab.
- Export/share of evaluation reports. That belongs with Phase 18 reporting.
</deferred>

<open_questions>
## Open Questions

1. Which reading UI file owns the Evaluate button after Phases 3–5 land? The
   likely target is a `reading_panel.py`/`reading_tab.py`, but implementation
   should confirm before editing.
2. Should trend graphs filter to the currently selected passage only, or allow
   passage switching from within the Progress tab? The requirement only needs
   per-passage graphs, so keep scope narrow unless product says otherwise.
</open_questions>

---

*Phase: 09-evaluation-mode*
*Context gathered: 2026-05-30 for planning*
