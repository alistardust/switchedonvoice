# Phase 10: Adaptive Recommendations Engine - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase gives the home screen a gentle sense of direction: after a scored
session, the app surfaces one to three useful next steps rather than forcing
the user to infer what to do from raw metrics. The recommendations should feel
helpful and lightweight, never mandatory or nagging.

Recommendation generation is a decision layer; it should consume Phase 7–9
state, not invent new scoring systems.
</domain>

<decisions>
## Key Decisions

- **D-10-01:** Use a dedicated `WeaknessDetector` pure/service layer that ranks
  weak dimensions from recent scored history against the user's own past data.
- **D-10-02:** Store recommendation rules as packaged JSON so the mapping from
  weak dimension → skill IDs / future arcade IDs is declarative and reviewable.
- **D-10-03:** Persist the last recommendation batch in settings under a
  profile-scoped key so the app can avoid repeating the same cards on
  consecutive opens when nothing changed.
- **D-10-04:** "Just let me choose" is session-scoped only. It hides the panel
  until the next fresh session but does not wipe weakness history or cached
  recommendations.
- **D-10-05:** The first iteration should deep-link only to content that
  already exists (skill tree nodes, reading content, exercises). Arcade IDs may
  exist in rules as placeholders, but unresolved links must not render as live
  buttons before Phase 11.

- **D-10-06:** The initial route map is fixed in this phase: `progress/open_skill`,
  `reading/open_passage`, and `analysis/open_exercise`. `arcade/open_game` may be
  present in rules only with `is_live=false` until Phase 11 ships.
- **Reasoning:** Rules authors and UI implementers need one canonical contract or
  recommendation buttons will drift into dead links.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/REQUIREMENTS.md` — REQ-C04 and the XP/skill context from REQ-C05
- `.planning/ROADMAP.md` §Phase 10 — canonical task list and success criteria
- `.planning/phases/07-skill-tree-ui/07-PLAN.md` — skill IDs and Progress/UI destinations
- `.planning/phases/08-daily-goals/08-PLAN.md` — Analysis-tab home layout
- `.planning/phases/09-evaluation-mode/09-PLAN.md` — scored-dimension outputs
- `src/switchedonvoice/storage/settings.py` — existing settings persistence conventions

</canonical_refs>

<architecture>
## Architecture Fit

### Inputs this phase consumes
- evaluation/report-card scores from Phase 9
- curriculum skill IDs and unlock state from Phase 6/7
- today's home-screen layout from Phase 8, where the suggestion panel will sit

### Recommended new modules
- `recommendations/weakness.py` — pure weakness detection and ranking helpers
- `recommendations/service.py` — rule application, deduplication, settings cache
- `recommendations/rules.json` — mapping table for dimensions to skill/exercise targets
- `ui/recommendations_panel.py` — card rendering and dismiss button

### Settings impact
`storage/settings.py` will likely need a profile-scoped structure for the last
recommendation batch and its source fingerprint. Keep it version-tolerant so
Phase 15 can migrate it cleanly.
</architecture>

<pitfalls>
## Pitfalls to Avoid

- Do not recommend content the user cannot navigate to yet.
- Do not recompute identical recommendations on every paint or tab switch; use
  a stable service call and cache/fingerprint results.
- Do not treat all equal scores as weaknesses; the panel should hide or fall
  back gracefully when no useful distinction exists.
- Do not make dismiss permanent. The requirement says it hides only for the
  current session.
- Do not let rule coverage drift. Every dimension emitted by the detector must
  have at least one valid rule target.
</pitfalls>

<dependencies>
## Specific Dependencies on Earlier Phases

- **Phase 7:** skill tree node IDs become recommendation targets
- **Phase 8:** Analysis tab already hosts the daily goal widget; recommendations
  should slot below it without disrupting the rest of the analysis view
- **Phase 9:** provides the richest dimension scores for weakness detection and
  should be the primary scored-history input

The roadmap note about Phase 11 matters: arcade links may be seeded now but
should remain inert/hidden until the Arcade tab exists.
</dependencies>

<deferred>
## Deferred Ideas

- LLM- or coach-script-based recommendation copy generation. v1.2 should stay
  deterministic and offline.
- Bandit or confidence-weighted recommendations that mix difficulty, novelty,
  and streak risk. Start with simple weakness ranking.
- Cross-session explanation history ("why we suggested this yesterday"). Useful
  later, but unnecessary for the first release.
</deferred>

<open_questions>
## Open Questions

1. Should weakness detection use only evaluation scores, or blend Phase 4
   passage-summary scores when evaluation history is sparse? Product guidance
   is needed because the answer changes how quickly recommendations appear.
2. What should happen when the user has improved across all dimensions and no
   clear weakness remains? A "keep reinforcing your best skill" fallback may be
   desirable, but it is not in the current requirement.
</open_questions>

---

*Phase: 10-recommendations*
*Context gathered: 2026-05-30 for planning*
