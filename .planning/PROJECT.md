# SwitchedOnVoice

## What This Is

SwitchedOnVoice is an open-source PySide6 desktop application for voice feminisation training. It provides real-time acoustic analysis (pitch, formants, CPP, spectrum), structured exercises, gamification milestones, and progress tracking — designed specifically for trans women working on their voice.

## Core Value

A trans person practicing voice training sees accurate real-time acoustic feedback and feels genuinely supported in their journey — not just measured.

## Requirements

### Validated

<!-- Phase 1 shipped and confirmed complete -->

- ✓ **AUDIO-01**: Real-time F0 (pitch) extraction via pyworld at ~30 Hz — Phase 1
- ✓ **AUDIO-02**: Real-time formant analysis (F1/F2) via LPC at ~30 Hz — Phase 1
- ✓ **AUDIO-03**: Real-time CPP (cepstral peak prominence) computation — Phase 1
- ✓ **AUDIO-04**: Real-time spectrum display via FFT — Phase 1
- ✓ **AUDIO-05**: Voice activity detection (RMS + ZCR) — Phase 1
- ✓ **AUDIO-06**: Waveform display widget — Phase 1
- ✓ **UI-01**: Pitch meter widget with visual target range — Phase 1
- ✓ **UI-02**: Vowel space plot (F1/F2 scatter) — Phase 1
- ✓ **UI-03**: Spectrum widget — Phase 1
- ✓ **UI-04**: 4-tab main window (Analysis / Exercises / Progress / Settings) — Phase 1
- ✓ **UI-05**: Onboarding wizard (mic select, ambient calibration, baseline recording) — Phase 1
- ✓ **STORE-01**: SQLite session storage with per-frame acoustic data — Phase 1
- ✓ **STORE-02**: User settings persistence (JSON) — Phase 1
- ✓ **GAME-01**: Gamification milestone system (5 milestones) — Phase 1
- ✓ **GAME-02**: Session streak tracking — Phase 1
- ✓ **HEALTH-01**: Vocal health warning system (CPP threshold alerts) — Phase 1

### Active

<!-- Current milestone scope — defined below -->

(see Current Milestone section)

### Out of Scope

- **Mobile app** — Desktop-first; mobile later if community demands it
- **Cloud sync / accounts** — Privacy-first; all data stays local
- **Tauri/Rust rewrite** — Planned for future but out of scope while Python DSP matures
- **Real-time voice modification/transformation** — Training tool, not voice changer
- **aubio library** — GPL-licensed, excluded permanently; pyworld (BSD) is the F0 engine

## Current Milestone: v1.1 — TBD

**Goal:** TBD — defining now

**Target features:** TBD

## Context

- **Target users:** Trans women working on voice feminisation; self-directed learners
- **Platform:** CachyOS Linux (Arch-based); tested on Python 3.14, PySide6 6.x
- **Architecture:** Single-process Python desktop app. sounddevice callback → lock-free deque → analysis thread (~30 Hz) → Queue → QTimer (30 Hz) → widget repaints
- **Test infrastructure:** pytest + pytest-qt, 104 tests, all passing as of Phase 1
- **Branch strategy:** Feature branches off main; Phase 1 on `feature/phase-1` (not yet merged)
- **Public domain content** identified for use: Alice's Adventures in Wonderland (Carroll), The Wonderful Wizard of Oz (Baum), Anne of Green Gables (Montgomery), The Secret Garden (Burnett), A Little Princess (Burnett), Grimm's Fairy Tales

## Constraints

- **Tech stack**: PySide6 (LGPL) + Python 3.11+ — no GPL dependencies
- **Privacy**: No network calls, no telemetry, no cloud — all data local
- **Performance**: Audio analysis must complete within ~33 ms per frame to avoid buffer underruns
- **Accessibility**: App is for trans people; language must be gender-affirming throughout

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| pyworld for F0 (not aubio) | aubio is GPL; pyworld is BSD-licensed | ✓ Good |
| SQLite for storage | stdlib, zero-dependency, sufficient for local-only app | ✓ Good |
| Single-process architecture | Simpler than IPC; sufficient for 30 Hz analysis | ✓ Good — revisit if latency issues emerge |
| close_session() before get_history_stats() | Ensures current session included in milestone evaluation | ✓ Good |
| Rainbow Passage (gender-neutralised) for baseline calibration | Phonemically balanced; "man" → "person" | ✓ Good |
| Alice in Wonderland as primary reading exercise content | Public domain, thematically resonant for trans audience | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-28 — bootstrapped from Phase 1 completion*
