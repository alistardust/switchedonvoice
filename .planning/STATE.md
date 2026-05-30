# Planning State

**Milestone:** v1.1 — Reading / Narration Mode
**Phase:** 2
**Status:** Planned — ready to execute

## What's Done
- [x] PROJECT.md created with Phase 1 context
- [x] MILESTONES.md created — v1.0 archived
- [x] REQUIREMENTS.md created — full product vision v1.1–v3.0
- [x] ROADMAP.md created — 26 concrete phases (Phases 2–26) + 1 optional (27)
- [x] config.json created
- [x] Phase 1 merged to main (HEAD: da20998)
- [x] GitHub issues #1–#26 created (one per phase epic)
- [x] GitHub issues #27–#33 created (gap/spec issues)
- [x] `/gsd-discuss-phase 2` — context captured (02-CONTEXT.md)
- [x] `/gsd-plan-phase 2` — 5 plans created + verified (02-01 through 02-05)
- [x] `.sov-book` format spec written and reviewed (9 findings fixed, issue #27 closed)
- [x] Phase 2 plans updated: passage_slug TEXT FK throughout, schema_version field
- [x] **Full planning pass complete** — CONTEXT.md + PLAN.md created for all phases 3–26

## Planned Phases (all have CONTEXT.md + PLAN.md)
| Phase | Name | Plans |
|-------|------|-------|
| 02 | Content Library & Book Ingestion | 5 plans |
| 03 | Reading Mode UI | 1 plan |
| 04 | Acoustic Overlay & Session Summary | 1 plan |
| 05 | Recording & Playback | 1 plan |
| 06 | Curriculum Schema & Baseline | 1 plan |
| 07 | Skill Tree UI | 1 plan |
| 08 | Daily Goals & Habit Tracking | 1 plan |
| 09 | Evaluation Mode | 1 plan |
| 10 | Personalised Recommendations | 1 plan |
| 11 | Arcade Infrastructure | 1 plan |
| 12 | Resonance Drill | 1 plan |
| 13 | Siren Glide & Rhythm | 1 plan |
| 14 | Arcade History & Leaderboard | 1 plan |
| 15 | Multi-Profile Support | 1 plan |
| 16 | Curriculum Authoring | 1 plan |
| 17 | Homework Assignment | 1 plan |
| 18 | Session Reports | 1 plan |
| 19 | Coach Analytics | 1 plan |
| 20 | Real-Time Remote Coaching | deferred |
| 21 | Singing Mode Foundations | 1 plan |
| 22 | Melody Following | 1 plan |
| 23 | Singing Exercise Library | 1 plan |
| 24 | Milestone Recording & Comparison | 1 plan |
| 25 | Virtual Coach Engine | 1 plan |
| 26 | Coach Avatar Shell | 1 plan |

## Phase 2 Plans (5 plans, 3 waves)
- Wave 1 (parallel): `02-01` Schema + BookRepository · `02-02` CLI converter tool
- Wave 2 (parallel): `02-03` Bundled assets (Alice/Oz/Anne) · `02-04` Folder-watcher service
- Wave 3: `02-05` Tests (parser, repo, watcher, integration)

## What's Next
- [ ] `/gsd-execute-phase 2` — implement Phase 2

## Active Branch
`main` (Phase 1 merged; create `feature/phase-2` before executing)

## Milestone Goals (v1.1)
- Reading mode: display public domain book text, user reads aloud with live acoustic feedback
- Kindle-style progress: bookmark per book, chapter navigation
- Recording history: save sessions to WAV, play back progress over time
- Content library: Alice in Wonderland, Wizard of Oz, Anne of Green Gables (initial set)

*Last updated: 2026-05-30*
