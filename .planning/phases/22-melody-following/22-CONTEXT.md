# Phase 22: Melody Following - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Goal

Phase 22 adds a public-domain melody library and a real-time singing practice
loop where target notes scroll across the screen, the user sings against them,
and the app scores pitch, timing, and vibrato quality.
</domain>

<dependencies>
## Dependencies on Earlier Phases

- **Phase 21:** Singing mode, singing target ranges, mode-aware CPP handling,
  and session-health helpers already exist and can be assumed stable.
- **Phase 11:** `ArcadeRepository` and the generic score / XP completion flow
  already exist. Melody attempts should reuse that persistence/XP machinery
  instead of inventing a second scoring subsystem.
- **Phase 14:** XP Breakdown and history panels already know how to group
  score-derived XP by stable source IDs / `game_id`-style keys.
- **Phase 6/7:** `CurriculumService` and the Progress tab already exist for
  XP awards and user-visible progression summaries.
- **Current UI seams:** `MainWindow._tick()` can already forward every
  `AnalysisResult` to additional Qt widgets on the main thread; melody play
  should hook in there rather than reading the audio queue independently.
</dependencies>

<decisions>
## Key Decisions

- **D-22-01:** Store melodies as bundled JSON assets under
  `src/switchedonvoice/content/melodies/`, with one canonical library file or
  one file per song plus a loader-level schema validator. The assets must be
  traditional/public-domain songs only, and each entry should include source
  provenance metadata.
- **D-22-02:** Use absolute timeline note events (`start_time_ms`,
  `duration_ms`, `frequency_hz`) as the canonical runtime format. No staff
  notation, MIDI playback engine, or symbolic music parser is needed.
- **D-22-03:** Build the note renderer as a dedicated Qt widget that draws
  coloured rectangles on a scrolling pitch-vs-time plane. Rendering should use
  QPainter/QWidget and the existing Qt stack, not a second plotting library,
  unless Phase 14 already introduced one that cleanly fits the job.
- **D-22-04:** Keep pitch, onset, and vibrato scoring in pure functions or
  pure dataclass-based services. The renderer consumes prepared note geometry;
  the results screen consumes scored attempts; neither widget reimplements the
  math.
- **D-22-05:** Introduce a generic singing-attempt persistence layer now,
  rather than a melody-only schema. Store `content_type` (`"melody"` in Phase
  22) and `content_slug` so Phase 23 exercises can reuse the same tables.
- **D-22-06:** Mirror completed melody scores into `ArcadeRepository` using a
  stable namespace such as `melody/<slug>` for XP Breakdown and personal-best
  aggregation. Detailed per-note metrics live in the singing-attempt tables.
- **D-22-07:** `MelodyBrowserWidget` is browse/select UI only. Active playback,
  live scoring, and completion logic live in a separate practice panel so the
  browser stays cheap to test and extend.
</decisions>

<research>
## Research Findings

- **R-22-01:** The cents-deviation formula for pitch accuracy is
  `1200 * log2(observed_hz / target_hz)`. This should live in one helper and be
  tested directly; widget code should never inline it.
- **R-22-02:** Onset scoring is more robust when the renderer and scorer share
  the same monotonic session clock. Counting frames or relying on the number of
  received `AnalysisResult` objects will drift under load.
- **R-22-03:** Vibrato detection should use a band-limited oscillation-rate
  check (roughly 5–8 Hz) plus a minimum modulation depth so slow drift and
  jitter do not get mislabelled as vibrato.
- **R-22-04:** Public-domain melody data should record title, tune source,
  difficulty, and estimated vocal range in the asset itself. That avoids hard-
  coding UI metadata elsewhere and keeps licensing review auditable.
- **R-22-05:** Preparing note rectangles ahead of paint time (for example,
  `PreparedNoteBar` dataclasses) makes rendering deterministic and easy to test
  without a running audio stream.
- **R-22-06:** Results screens should present note-by-note feedback derived
  from stored segment scores rather than rescoring from raw F0 after the fact;
  otherwise historical results can change if the scoring algorithm changes.
</research>

<data_model>
## Data Model

### Bundled melody asset schema

```json
{
  "slug": "twinkle-twinkle",
  "title": "Twinkle, Twinkle, Little Star",
  "source": "Traditional",
  "difficulty": "entry",
  "range_min_hz": 261.63,
  "range_max_hz": 392.00,
  "notes": [
    {
      "note_name": "C4",
      "start_time_ms": 0,
      "duration_ms": 750,
      "frequency_hz": 261.63
    }
  ]
}
```

### SQLite additions (generic singing-attempt schema)

Add a new migration block in `src/switchedonvoice/storage/db.py` using an
independent `if version < N:` clause:

- `singing_attempts`
  - `id INTEGER PRIMARY KEY AUTOINCREMENT`
  - `profile_id INTEGER`
  - `content_type TEXT NOT NULL` (`melody`, later `exercise`)
  - `content_slug TEXT NOT NULL`
  - `started_at TEXT NOT NULL`
  - `completed_at TEXT`
  - `pitch_accuracy_pct REAL NOT NULL`
  - `timing_accuracy_pct REAL NOT NULL`
  - `vibrato_count INTEGER NOT NULL`
  - `overall_score REAL NOT NULL`
  - `earned_xp INTEGER NOT NULL`
  - indexes on `(profile_id, content_type, content_slug)` and `completed_at`
- `singing_segment_scores`
  - `attempt_id INTEGER NOT NULL REFERENCES singing_attempts(id) ON DELETE CASCADE`
  - `segment_index INTEGER NOT NULL`
  - `target_name TEXT NOT NULL`
  - `target_frequency_hz REAL NOT NULL`
  - `observed_frequency_hz REAL`
  - `cents_error REAL`
  - `onset_error_ms REAL`
  - `is_pitch_hit INTEGER NOT NULL`
  - `vibrato_detected INTEGER NOT NULL`
  - `PRIMARY KEY (attempt_id, segment_index)`

### New runtime dataclasses

- `MelodyNote`
- `MelodySong`
- `PreparedNoteBar`
- `ScoredSegment`
- `SingingAttemptSummary`
- `VibratoWindow`

### Key interfaces

- `load_melody_library() -> list[MelodySong]`
- `prepare_note_bars(song: MelodySong, viewport_ms: int, now_ms: int) -> list[PreparedNoteBar]`
- `score_note_segment(target: MelodyNote, observed_hz: float | None, observed_onset_ms: float | None) -> ScoredSegment`
- `detect_vibrato(f0_series_hz: Sequence[float], sample_rate_hz: float) -> bool`
- `SingingRepository.save_attempt(summary: SingingAttemptSummary, segments: list[ScoredSegment]) -> int`
</data_model>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md` — `REQ-S02`
- `.planning/ROADMAP.md` §Phase 22
- `.planning/phases/21-singing-mode/21-CONTEXT.md`
- `.planning/phases/11-arcade-infrastructure/11-CONTEXT.md`
- `.planning/phases/14-arcade-history/14-CONTEXT.md`
- `src/switchedonvoice/audio/capture.py`
- `src/switchedonvoice/ui/main_window.py`
- `src/switchedonvoice/ui/progress_panel.py`
</canonical_refs>

<pitfalls>
## Pitfalls to Avoid

- Do **not** add copyrighted melodies. Every bundled song needs a public-domain
  source citation in the asset metadata.
- Do **not** compute note geometry inside `paintEvent()`. Prepare it first so it
  can be tested and profiled.
- Do **not** award XP before persistence succeeds. Follow Phase 11 ordering:
  store attempt → award XP → refresh results/progress UI.
- Do **not** derive history from raw `arcade_scores` alone. Detailed note-level
  metrics need a singing-specific repository.
</pitfalls>

<open_questions>
## Open Questions Deferred to Later Phases

1. Should future melody practice support adjustable tempo or key transposition,
   or keep the library fixed for now?
2. Should the app eventually play an audible backing guide tone, or remain
   visual-only to avoid audio-output complexity?
3. How should lyrics be handled if a future melody includes multiple verses?
4. Should vibrato quality later include smoothness/depth scoring instead of a
   simple count?
</open_questions>

---

*Phase: 22-melody-following*
*Context gathered: 2026-05-30 for phase planning*
