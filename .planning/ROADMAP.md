# SwitchedOnVoice — Full Product Roadmap

> **Milestone scope:** v1.1 through v2.0+ (post-Phase 1 completion)
> **Phase 1:** Complete — 25 tasks (Tasks 0–24), 104 tests passing, on `feature/phase-1`
> **Next phase:** Phase 2 (start of Milestone v1.1)
> **Last updated:** 2026-05-28

---

## Overview

Phase 1 shipped the acoustic engine and UI foundation. Every subsequent phase builds user-facing value on top of that base. Phases are ordered by dependency: data models precede their UIs; content infrastructure precedes content features; arcade infrastructure precedes individual games.

**Total phases:** 22 concrete (Phases 2–23) + 1 deferred future phase (Phase 20)
**Milestones:** v1.1 (4 phases) → v1.2 (5 phases) → v1.3 (4 phases) → v1.4 (5+1 phases) → v2.0 (3 phases)

---

## Phases

### ✅ Milestone v1.0 — Foundation (Complete)

- [x] **Phase 1: Foundation** — DSP pipeline, PySide6 UI, onboarding wizard, SQLite storage, gamification, 104 tests

---

### Milestone v1.1 — Reading / Narration Mode

- [ ] **Phase 2: Content Library & Book Ingestion** — Public domain books parsed into passages; SQLite schema for books/chapters/passages and reading progress
- [ ] **Phase 3: Reading Mode UI** — Passage display with word highlighting, chapter navigation, Kindle-style bookmarks
- [ ] **Phase 4: Live Acoustic Feedback & Session Summary** — Pitch/resonance/CPP overlay while reading; post-passage summary; per-passage score persistence
- [ ] **Phase 5: Recording & Playback History** — Opt-in session recording to WAV; history timeline per passage; waveform playback; storage management

---

### Milestone v1.2 — Structured Curriculum + Evaluations

- [ ] **Phase 6: Curriculum Data Model & Skill Tree Schema** — DAG skill definitions, XP tables, level definitions; CurriculumService
- [ ] **Phase 7: Skill Tree UI + XP & Level Display** — Visual skill tree widget with lock/unlock states; XP counter; level-up dialogs
- [ ] **Phase 8: Daily Goals, Streaks & Home Widget** — Goal-setting dialog; "Today's Goal" home widget; adaptive target adjustment
- [ ] **Phase 9: Evaluation Mode + Report Card** — Silent evaluation run; scored report card with plain-language explanations; per-passage trend graphs
- [ ] **Phase 10: Adaptive Recommendations Engine** — Weakness detection from recent sessions; 1–3 suggested next steps on home screen

---

### Milestone v1.3 — Vocal Arcade

- [ ] **Phase 11: Arcade Infrastructure + Pitch Targeting Game** — Arcade tab and launcher; score DB; ArcadeGame base class; Pitch Targeting game with difficulty scaling
- [ ] **Phase 12: Resonance Drill + Vowel Shaping** — Bullseye resonance drill on vowel space; vowel bubble-popping game with IPA target positions
- [ ] **Phase 13: Siren Glide + Rhythm & Cadence** — Path-following pitch glide game; syllable timing rhythm game
- [ ] **Phase 14: Arcade Personal Bests & History View** — Per-game personal best banners; 10-attempt history sparklines; arcade stats in Progress tab

---

### Milestone v1.4 — Instructor Mode

- [ ] **Phase 15: Multi-Profile Support** — profiles table; student/coach profile types; profile switcher on home screen; data isolation
- [ ] **Phase 16: Curriculum Authoring** — Coach curriculum builder; drag-drop exercise ordering; `.sov-curriculum` export/import format
- [ ] **Phase 17: Homework Assignment** — Coach assigns exercises to student profiles; student "Assigned by coach" section; completion reports
- [ ] **Phase 18: Session Reports & File Export** — HTML/PDF session reports; `.sov-session` export/import format; read-only report viewer
- [ ] **Phase 19: Coach Analytics View** — Per-student F0/resonance trend charts; first-vs-now comparison; session notes; full progress PDF export
- [ ] **Phase 20: Real-Time Remote Coaching *(Future — Deferred)*** — Requires backend infrastructure; no tasks planned until backend roadmap is initiated

---

### Milestone v2.0 — Singing Mode

- [ ] **Phase 21: Singing Mode Foundations** — Speaking/Singing mode selector; separate singing baselines; singing-specific CPP thresholds; fatigue detection
- [ ] **Phase 22: Melody Following** — Public domain melody library; note target display on pitch timeline; real-time melody scoring
- [ ] **Phase 23: Singing Exercise Library** — Warm-up scales, arpeggios, interval drills; soprano/mezzo/contralto variants; pitch contour display

---

## Phase Details

---

### Phase 1: Foundation *(Complete)*

**Goal**: App exists and works — real-time acoustic analysis running, UI navigable, sessions stored, onboarding complete.
**Status**: ✅ Complete (Tasks 0–24, `feature/phase-1`)
**Requirements**: AUDIO-01–06, UI-01–05, STORE-01–02, GAME-01–02, HEALTH-01
**Success Criteria**:
  1. User can open app, complete onboarding wizard, and see live pitch/formant/spectrum analysis
  2. User can complete a session and see it appear in session history with streak tracking
  3. 104 tests pass; app launches via `python -m switchedonvoice`
**Plans**: Complete

---

### Phase 2: Content Library & Book Ingestion

**Goal**: The app ships with readable books and knows exactly where the user left off in each one.
**Depends on**: Phase 1
**Requirements**: REQ-R01, REQ-R05 (schema foundation)
**Tasks**:
  1. Design and migrate SQLite schema: `books`, `chapters`, `passages` tables with FK relationships and content metadata
  2. Write book parser: split Project Gutenberg `.txt` files into chapters, then into ~150-word practisable passages; strip PG boilerplate
  3. Bundle 3 public domain books as package assets: *Alice's Adventures in Wonderland*, *The Wonderful Wizard of Oz*, *Anne of Green Gables*
  4. Implement `BookRepository` service class: `list_books()`, `get_chapters(book_id)`, `get_passages(chapter_id)`, `get_passage(id)`
  5. Implement folder-watcher service: monitor `~/.switchedonvoice/books/` for new `.txt` drops; auto-ingest on detection
  6. Migrate reading progress schema: `reading_progress` table (profile_id, passage_id, bookmark_offset, completion_count, last_attempted_at)
  7. Write unit tests for parser edge cases, passage splitting, repository queries, and folder-watcher ingestion
**Success Criteria**:
  1. All 3 bundled books appear in the app with correct chapter counts and passage boundaries
  2. User can drop a `.txt` file into `~/.switchedonvoice/books/` and the book appears in the library without restarting
  3. `BookRepository` returns correct passage text for any (book, chapter, passage) address
  4. Reading progress table exists and records are schema-valid
**Estimated complexity**: M

---

### Phase 3: Reading Mode UI

**Goal**: User can open any passage from any book, read it comfortably with their place tracked, and navigate between chapters.
**Depends on**: Phase 2
**Requirements**: REQ-R02
**Tasks**:
  1. Add a "Reading" tab to the main window (fifth tab, or repurpose the placeholder Exercises tab); wire to `BookRepository`
  2. Build `PassageDisplayWidget`: large, high-contrast font (WCAG AA minimum), full passage text rendered with line wrapping
  3. Implement word-level highlight cursor: advance highlight word-by-word using a manual "next word" key or automatic timer mode
  4. Build chapter navigation widget: Previous Chapter / Next Chapter buttons and a Jump-to-Chapter dropdown
  5. Implement Kindle-style bookmark persistence: write current word offset to `reading_progress` on tab leave / app close; restore on re-open
  6. Write widget tests for passage rendering, highlight state advancement, chapter navigation, and bookmark round-trip
**Success Criteria**:
  1. User opens the Reading tab, selects a book and chapter, and sees passage text in a large readable font
  2. Highlight advances word-by-word and the displayed position persists correctly when the user closes and reopens the app
  3. User can navigate to any chapter via prev/next buttons or the jump list without losing their position in the previous chapter
  4. All text elements pass WCAG AA contrast check
**Estimated complexity**: M
**UI hint**: yes

---

### Phase 4: Live Acoustic Feedback Overlay & Session Summary

**Goal**: User gets real-time pitch and resonance feedback while reading, and sees a summary of how they performed when they finish.
**Depends on**: Phase 3
**Requirements**: REQ-R03, REQ-R05 (acoustic scores; completes REQ-R05)
**Tasks**:
  1. Connect the existing audio analysis pipeline to the Reading tab: pitch meter, vowel space plot, and spectrum widget activate when the tab is entered and deactivate cleanly on exit
  2. Implement word-colouring overlay: record per-word mean F0 during reading; colour each word green / amber / red based on proximity to user's F0 target range
  3. Build `SessionSummaryDialog`: displays avg F0 (Hz + linguistic label), mean F1/F2 resonance, CPP health indicator, total time, and a one-sentence plain-language verdict
  4. Store per-passage first and most recent acoustic scores in `reading_progress` (avg_f0, resonance_score, cpp_score, recorded_at) — updating "first" only if null, "recent" always
  5. Ensure CPP vocal health warnings (from Phase 1 `HEALTH-01`) surface correctly within the Reading tab's active analysis session
  6. Write tests for per-word F0 aggregation, colour threshold logic, score persistence (first/recent semantics), and summary computation
**Success Criteria**:
  1. Pitch meter, vowel plot, and spectrum are live while the user reads; they go idle when the user switches away from the Reading tab
  2. After reading a passage, words are colour-coded and the session summary dialog appears with meaningful scores
  3. After completing the same passage twice, the Progress tab shows both "first attempt" and "most recent" scores for comparison
  4. CPP warning triggers correctly if the user strains their voice during a reading session
**Estimated complexity**: L
**UI hint**: yes

---

### Phase 5: Recording & Playback History

**Goal**: User can listen back to how they sounded on any passage over time, seeing their voice evolve.
**Depends on**: Phase 4
**Requirements**: REQ-R04, REQ-NF02 (storage management)
**Tasks**:
  1. Add opt-in recording toggle: global default in Settings + per-session prompt at reading start ("Record this session?")
  2. Implement recording pipeline: stream audio to WAV (44.1 kHz, 16-bit mono) at `~/.switchedonvoice/recordings/<book_slug>/<chapter_slug>/<YYYY-MM-DD_HH-MM>.wav`
  3. Build `RecordingHistoryWidget`: scrollable timeline list of all recordings for the currently displayed passage, sorted by date ascending
  4. Implement recording playback: Play/Stop button per recording entry; audio plays via `sounddevice.play()`
  5. Render a waveform thumbnail next to each recording entry using the existing `WaveformWidget` (load WAV file, render static snapshot)
  6. Add storage management panel to Settings: estimated total recording storage used (MB), per-book recording counts, "Delete recordings for this book" and "Delete all before date" controls
  7. Write tests for recording file naming, opt-in logic, playback state machine, storage size estimation, and deletion
**Success Criteria**:
  1. With recording enabled, finishing a reading session creates a correctly-named WAV file at the expected path
  2. Recording History view shows all past recordings for a passage as a dated list; each entry is playable
  3. Waveform thumbnails render for each recording entry without blocking the UI
  4. Settings shows accurate storage usage; "Delete recordings for this book" removes all expected files
**Estimated complexity**: M
**UI hint**: yes

---

### Phase 6: Curriculum Data Model & Skill Tree Schema

**Goal**: The app has a structured map of voice skills, knows which ones the user has unlocked, and can credit and accumulate XP correctly.
**Depends on**: Phase 4 (needs acoustic scoring to evaluate skill criteria)
**Requirements**: REQ-C01 (data layer), REQ-C05 (data layer)
**Tasks**:
  1. Design DAG skill schema: `skills` (id, name, category, tier, description), `skill_dependencies` (skill_id, requires_skill_id), `user_skill_progress` (profile_id, skill_id, sessions_meeting_criteria, unlocked_at)
  2. Seed 15 initial skills across 5 categories: Pitch (F0 range targeting), Resonance (F1/F2 control), Vocal Quality (CPP), Clarity (consistency), Intonation (variation) — 3 tiers (entry/intermediate/advanced) each
  3. Create `exercises` table; map each existing Phase 1 exercise type and each planned arcade game to one or more skill tiers
  4. Design XP schema: `xp_events` (profile_id, source_type, source_id, xp_amount, earned_at), `user_xp` (profile_id, total_xp) as a materialised view or computed on read
  5. Define 24 level thresholds with meaningful names and flavour text (e.g., Level 1 "Finding My Voice", Level 12 "Resonance Sculptor", Level 24 "Vocal Alchemist")
  6. Implement `CurriculumService`: `get_unlocked_skills(profile_id)`, `evaluate_skill_unlock(profile_id, skill_id)`, `get_user_xp(profile_id)`, `award_xp(profile_id, source, amount)`, `get_level(xp)`
  7. Write unit tests for DAG traversal, transitive unlock logic, XP accumulation, level boundary computation
**Success Criteria**:
  1. All 15 skills exist in the DB with correct DAG dependency edges; unlocking a prerequisite skill correctly marks the dependent as available
  2. `CurriculumService.award_xp()` creates an `xp_events` row and `get_user_xp()` returns the correct total
  3. Level thresholds map correctly: given XP totals at known boundaries, `get_level()` returns the right level name
  4. All curriculum service tests pass with no direct DB access from test layer (service abstraction maintained)
**Estimated complexity**: M

---

### Phase 7: Skill Tree UI + XP & Level Display

**Goal**: User can see their skill progression as a visual tree, watch skills unlock, and feel rewarded when they level up.
**Depends on**: Phase 6
**Requirements**: REQ-C01 (UI completion), REQ-C05 (UI completion)
**Tasks**:
  1. Build `SkillTreeWidget`: render DAG as connected circular nodes; colour-code locked (grey) / in-progress (amber) / complete (teal); draw dependency edges as lines
  2. Implement unlock animation: node pulses and transitions from locked to unlocked colour when a skill tier is completed; play a soft chime
  3. Add persistent XP counter + level progress bar to the main window's status area (always visible, updates after each session)
  4. Build `LevelUpDialog`: full-screen celebratory overlay showing new level number, name, and flavour text; dismissible by click or key
  5. Add XP Breakdown panel to the Progress tab: itemised `xp_events` list — source type, amount, date — so the user understands what earned what
  6. Wire `SkillTreeWidget` to `CurriculumService`; refresh skill states after each session close; show skill detail tooltip on node hover
  7. Write widget tests for node colour states, edge rendering, XP counter update cycle, and level-up dialog trigger threshold
**Success Criteria**:
  1. Opening the Progress tab shows the full skill tree with visually distinct locked/in-progress/complete nodes and correct dependency edges
  2. Completing a session that meets a skill criterion triggers the node unlock animation without any app restart
  3. Reaching a level threshold triggers the `LevelUpDialog` with the correct level name and flavour text
  4. XP Breakdown lists all events with correct totals; sum matches the displayed XP counter
**Estimated complexity**: L
**UI hint**: yes

---

### Phase 8: Daily Goals, Streaks & Home Widget

**Goal**: User is greeted with a clear daily target that adapts to their habits, and the home screen makes it trivially easy to continue their streak.
**Depends on**: Phase 6 (XP/session data for adaptive calculation), Phase 1 (streak tracking)
**Requirements**: REQ-C02
**Tasks**:
  1. Add "Today's Goal" widget to the home/Analysis tab header: shows goal type (minutes / exercises), today's progress, and a compact progress bar
  2. Build goal-setting dialog (accessible from Settings): user picks goal type and target amount; sensible defaults (10 min / 3 exercises)
  3. Implement adaptive goal adjustment: after each completed session, compute rolling 7-day average and nudge the default target ±10% toward achievable; never adjust without user awareness (show "adjusted" badge)
  4. Integrate today's goal progress with Phase 1 streak tracker (`GAME-02`): a day counts toward the streak only when today's goal is met
  5. Persist goal settings in JSON settings file; persist today's progress in `daily_goals` SQLite table (profile_id, date, goal_type, target, achieved)
  6. Write tests for adaptive adjustment algorithm (edge cases: no history, single session, 7-day plateau), goal completion detection, and streak integration
**Success Criteria**:
  1. Home screen shows today's goal and a progress bar that updates after each session without requiring an app restart
  2. After 7 days of sessions, the adaptive goal suggestion reflects the user's actual average (within 10%)
  3. Streak increments only on days where the daily goal was met; missing goal breaks the streak correctly
  4. Goal settings round-trip correctly through Settings dialog
**Estimated complexity**: S
**UI hint**: yes

---

### Phase 9: Evaluation Mode + Report Card

**Goal**: User can take a formal "test" on any passage and get a scored report card that shows whether they're improving over time.
**Depends on**: Phase 4 (acoustic scoring pipeline), Phase 6 (skill/score schema)
**Requirements**: REQ-C03
**Tasks**:
  1. Add "Evaluate" button to the Reading tab passage header; entering evaluation mode suppresses all live overlays, colour hints, and acoustic widgets during reading
  2. Implement silent background recording of the full evaluation run (always on for evaluations, regardless of recording preference)
  3. Build `ReportCardDialog`: five scored dimensions — Pitch Accuracy (% time within target F0 range), Resonance Score (F1/F2 centroid proximity), CPP Health (mean CPP vs. threshold), Pacing (syllables per minute vs. natural range), Consistency (F0 standard deviation) — each with a plain-language sentence
  4. Store evaluation results in `evaluations` table (profile_id, passage_id, timestamp, f0_accuracy, resonance_score, cpp_score, pacing_score, consistency_score)
  5. Build evaluation trend graph in Progress tab: line chart per dimension, one point per evaluation of the same passage, ordered by date (use pyqtgraph)
  6. Wire XP award for evaluation completion via `CurriculumService.award_xp()` (scaled by average score)
  7. Write tests for each scoring dimension computation, evaluation storage round-trip, and trend graph data pipeline
**Success Criteria**:
  1. In Evaluation mode, no live acoustic hints are visible during reading; the recording runs silently in the background
  2. After finishing, the Report Card shows five numeric scores with plain-language labels ("Your average pitch was 187 Hz — solidly in the feminine range!")
  3. After evaluating the same passage three times, the Progress tab shows a trend graph with three data points per dimension
  4. Evaluation XP is correctly credited and visible in the XP Breakdown panel
**Estimated complexity**: M
**UI hint**: yes

---

### Phase 10: Adaptive Recommendations Engine

**Goal**: After each session, the app surfaces 1–3 targeted suggestions so the user always knows the most valuable next thing to practice.
**Depends on**: Phase 9 (evaluation scores), Phase 7 (skill tree), Phase 11 note: can be built against Phase 9 data; arcade links added when Phase 11 lands
**Requirements**: REQ-C04
**Tasks**:
  1. Implement `WeaknessDetector` service: aggregate last 3 sessions' scores per dimension; identify dimensions scoring below the 50th percentile of the user's own history
  2. Build recommendation rule table: map each weak dimension → candidate skill tree nodes and (later) arcade game IDs; store as structured config (JSON/TOML)
  3. Add "Suggested Next" card panel to the home screen: renders 1–3 suggestion cards with icon, title, and deep-link to the recommended content
  4. Implement "Just let me choose" dismiss button: hides the panel for the current session without resetting the weakness detection data
  5. Persist last recommendation batch in settings (profile-scoped) to avoid serving identical suggestions on consecutive app opens
  6. Write tests for weakness detection edge cases (no history, all dimensions equal, single-session history), rule mapping coverage, and suggestion deduplication
**Success Criteria**:
  1. After two sessions where pitch scores are lower than resonance, the home screen suggests a pitch-focused exercise or arcade game
  2. Tapping a suggestion card navigates directly to the recommended content
  3. "Just let me choose" hides the panel; it reappears after the next session with potentially updated suggestions
  4. Suggestions never repeat the same item on two consecutive app opens when data hasn't changed
**Estimated complexity**: M
**UI hint**: yes

---

### Phase 11: Arcade Infrastructure + Pitch Targeting Game

**Goal**: The Arcade tab is open for business and the first game — Pitch Targeting — is fully playable with difficulty scaling and XP rewards.
**Depends on**: Phase 6 (XP system), Phase 7 (XP display)
**Requirements**: REQ-A01, REQ-A06 (data layer)
**Tasks**:
  1. Add "Arcade" tab to the main window; build the arcade launcher screen as a responsive grid of game tiles (icon, name, personal best, locked/unlocked state)
  2. Design `arcade_scores` table: (profile_id, game_id, score, difficulty_level, earned_xp, played_at); implement `ArcadeRepository` with `save_score()`, `get_personal_best()`, `get_recent_scores(n)`
  3. Implement abstract `ArcadeGame` base class: shared game loop (QTimer-driven), start/pause/stop state machine, score accumulation, DSP data hook (`on_audio_frame(f0, formants, cpp)`)
  4. Build Pitch Targeting game: falling pitch-target rectangles on a scrolling F0 timeline; user must vocalise and hold pitch within the target band; score = accuracy % × dwell bonus
  5. Implement 5-tier difficulty system: adjusts target width (semitones), fall speed (px/s), required hold duration (ms), and number of simultaneous targets
  6. Wire completed game score to `CurriculumService.award_xp()` with game-appropriate XP formula; animate XP gain on game-over screen
  7. Write tests for `ArcadeRepository` CRUD, difficulty parameter computation at each tier, game state machine transitions, and score-to-XP formula
**Success Criteria**:
  1. Arcade tab shows the game launcher grid; Pitch Targeting tile is selectable and launches the game
  2. Targets fall, the user's live F0 trace is visible, and scoring responds correctly to held pitch within target bounds
  3. Game ends after a fixed duration; game-over screen shows score, accuracy %, XP earned, and personal best indicator
  4. Increasing difficulty tier produces measurably narrower/faster targets (verified by test)
**Estimated complexity**: L
**UI hint**: yes

---

### Phase 12: Resonance Drill + Vowel Shaping

**Goal**: User can practice targeted formant control through two distinct games that make resonance exploration feel tactile and rewarding.
**Depends on**: Phase 11 (ArcadeGame base, score infrastructure)
**Requirements**: REQ-A02, REQ-A04
**Tasks**:
  1. Build Resonance Drill game: animated bullseye target overlaid on the live vowel space plot (F1/F2 scatter); score based on dwell time with cursor centroid inside bullseye radius
  2. Implement target cycling: sequentially place bullseye at front/back/high/low vowel quadrant positions; increase cycle speed with difficulty
  3. Build Vowel Shaping game: "bubble" targets placed at specific IPA vowel positions on the F1/F2 plane (e.g., /iː/, /æ/, /ɑː/, /uː/, /ɛ/); user must produce that vowel to "pop" the bubble
  4. Implement vowel proximity detector: compute Euclidean distance in normalised F1/F2 space between user's current formants and target vowel centroid; pop when distance < threshold
  5. Add visual feedback: snap flash animation when Resonance Drill cursor enters bullseye; bubble pop particle effect on successful vowel match
  6. Wire both games to `ArcadeRepository.save_score()` and `CurriculumService.award_xp()`; connect to Resonance skill tree node
  7. Write tests for dwell-time accumulation, vowel proximity detection at boundary distances, and target position cycling
**Success Criteria**:
  1. Resonance Drill shows an animated bullseye on the live F1/F2 plot; moving resonance into the target visually snaps and accumulates score
  2. Vowel Shaping shows bubble targets at recognisably correct vowel positions; producing /iː/ (front-high) pops the front-high bubble, not others
  3. Both games produce XP events that appear in the XP Breakdown panel
  4. At maximum difficulty, Resonance Drill cycles through all four quadrant positions at a challenging but playable speed
**Estimated complexity**: M
**UI hint**: yes

---

### Phase 13: Siren Glide + Rhythm & Cadence

**Goal**: User can practice smooth pitch gliding (eliminating glottal breaks) and natural speech rhythm through two skill-building mini-games.
**Depends on**: Phase 11 (ArcadeGame base)
**Requirements**: REQ-A03, REQ-A05
**Tasks**:
  1. Build Siren Glide game: render a smooth target path (sine wave or arc) on a scrolling pitch timeline; compute path-following accuracy as RMS deviation of user F0 from the path in semitones
  2. Implement glottal break detector: identify voiced→unvoiced transitions mid-glide; apply score penalty proportional to break duration
  3. Build Rhythm & Cadence game: display a prompt phrase and a target syllable timing pattern (stem-and-leaf timeline); user reads the phrase aloud
  4. Implement syllable onset detector: extract energy envelope onsets via a simple peak-picker on RMS; compare detected onset timestamps to target pattern using DTW alignment score
  5. Score rhythm accuracy as 0–100 % match; penalise over-pacing (rushing) and under-pacing (dragging) separately for diagnostic value
  6. Wire both games to score/XP infrastructure; link Siren Glide to Pitch/Clarity skill nodes; Rhythm & Cadence to Intonation node
  7. Write tests for RMS path-deviation calculation, glottal break detection threshold, syllable onset extraction on synthetic signals, and DTW alignment scoring
**Success Criteria**:
  1. Siren Glide renders a smooth path; the user's F0 trace is drawn alongside it in a contrasting colour; a score and deviation value appear on game over
  2. A deliberate voiced break mid-glide visibly impacts the score more than a smooth attempt
  3. Rhythm & Cadence shows the prompt phrase and target timing; reading too fast or too slow produces distinct lower scores than well-timed reading
  4. Both games appear on the Arcade launcher tile grid and are playable end-to-end
**Estimated complexity**: L
**UI hint**: yes

---

### Phase 14: Arcade Personal Bests & History View

**Goal**: User's arcade progress is celebrated and visualised, making the Arcade tab a satisfying place to return to over weeks.
**Depends on**: Phases 11–13 (all arcade games exist)
**Requirements**: REQ-A06 (UI completion)
**Tasks**:
  1. Build per-game personal best banner on each game-over screen: "🏆 New personal best!" vs. "Your best: X — today: Y"
  2. Build 10-attempt history sparkline for each game launcher tile (pyqtgraph `PlotWidget`, tiny, read-only) — shows score trend at a glance without entering the game
  3. Add arcade XP contribution line to the XP Breakdown panel (Phase 7): sum of arcade XP, broken down by game
  4. Add Arcade Statistics section to Progress tab: total arcade sessions played, most-played game, total XP earned from arcade, per-game personal best table
  5. Write tests for personal best comparison logic (strict greater-than, type-safe), history sparkline data preparation, and statistics aggregation queries
**Success Criteria**:
  1. Playing any game and beating a previous score shows the "New personal best!" banner on the game-over screen
  2. Arcade launcher tile sparklines update after each game session without requiring tab navigation
  3. Progress tab Arcade Statistics section shows accurate totals after a multi-game session
  4. XP Breakdown shows arcade contributions split by game name
**Estimated complexity**: S
**UI hint**: yes

---

### Phase 15: Multi-Profile Support

**Goal**: Multiple people can use the app on one machine (or a coach and student can coexist), each with a fully isolated history and settings.
**Depends on**: Phase 1 (all existing data tables)
**Requirements**: REQ-I01
**Tasks**:
  1. Add `profiles` table (id, name, profile_type [student/coach], created_at, avatar_colour); extend all user-scoped tables with `profile_id` FK: sessions, reading_progress, arcade_scores, xp_events, user_skill_progress, daily_goals, evaluations
  2. Write a data migration: wrap all existing data in a default profile (profile_id = 1, name = "Me", type = student) — zero data loss
  3. Build profile creation / edit / delete dialog: name input, profile type selector, avatar colour picker (no passwords — this is not a security boundary; note this clearly in UI)
  4. Add profile switcher to the home screen top bar: shows current profile avatar initial + name; dropdown lists all profiles + "Add new profile"
  5. Enforce profile isolation in all service layers: `BookRepository`, `CurriculumService`, `ArcadeRepository`, `SessionStore` all accept and require `profile_id`
  6. Write tests for data migration correctness, profile CRUD, switcher state changes, and cross-profile data isolation (profile A data is not visible to profile B)
**Success Criteria**:
  1. App opens with the default "Me" profile; no existing data is lost after the migration
  2. User can create a second profile, switch to it, complete a session, switch back, and see that neither profile's data has leaked into the other
  3. Coach profile type shows a "(Coach)" badge in the profile switcher dropdown
  4. Deleting a non-active profile removes all its data and disappears from the switcher
**Estimated complexity**: M

---

### Phase 16: Curriculum Authoring

**Goal**: A coach can build a custom structured curriculum on their machine and hand it to a student as a single importable file.
**Depends on**: Phase 15 (coach profile type), Phase 6 (curriculum schema)
**Requirements**: REQ-I02
**Tasks**:
  1. Build `CurriculumBuilderWindow` (accessible from coach profile settings): sidebar with exercise/passage/instruction-block palette; main area is an ordered drag-and-drop list
  2. Implement custom passage creation: plain-text editor pane (paste or type); passages created here are stored in `custom_passages` table and assignable within the curriculum
  3. Implement exercise target definition UI: for each curriculum item, optionally attach a measurable goal (e.g., "achieve avg F0 ≥ 180 Hz", "CPP ≥ 0.8 for 3 consecutive sessions") with operator + value fields
  4. Define `.sov-curriculum` package format: ZIP container with `manifest.json` (metadata, item order, targets) + bundled custom passage `.txt` files
  5. Implement export flow: "Save as .sov-curriculum" button → file-save dialog; implement import flow: "Import Curriculum" from file → validate manifest schema → load into DB under coach's profile
  6. Write tests for curriculum serialisation round-trip, target evaluation against session data, import validation (malformed manifest rejection), and drag-drop item ordering persistence
**Success Criteria**:
  1. Coach can build a 5-item curriculum (mix of built-in passages and custom text) via drag-drop in under 2 minutes
  2. Exported `.sov-curriculum` is a valid ZIP with a parseable `manifest.json`; importing it on a fresh profile recreates the curriculum exactly
  3. An exercise target of "avg F0 ≥ 180 Hz" correctly reports met/unmet against saved session data
  4. Importing a corrupt or schema-invalid `.sov-curriculum` shows a clear error message and makes no DB changes
**Estimated complexity**: L
**UI hint**: yes

---

### Phase 17: Homework Assignment

**Goal**: A student arrives at the app and immediately sees what their coach has asked them to work on, with their progress automatically tracked.
**Depends on**: Phase 15 (profiles), Phase 16 (curriculum exists to assign from)
**Requirements**: REQ-I03
**Tasks**:
  1. Build homework assignment UI (coach profile → student management view): select a student profile; choose exercises/passages from a list; set optional due date; confirm assignment
  2. Implement `homework` table: (id, coach_profile_id, student_profile_id, assigned_at, due_date, items JSON, status [pending/partial/complete])
  3. Add "Assigned by your coach" section to student home screen (appears only when homework exists): lists pending items with coach name, due date badge, and "Start" deep-link button
  4. Track homework completion separately: when a student completes a session against an assigned item, mark that item as done in homework record — does not merge with free-practice session history
  5. Build homework completion report view (coach profile → student management): per-assignment completion percentage, per-item completion date, acoustic scores achieved for each item
  6. Write tests for homework CRUD, student visibility (only assigned student sees the item), completion state machine, and coach report data aggregation
**Success Criteria**:
  1. Coach assigns 3 passages to a student; student's home screen immediately shows "Assigned by your coach" section with all 3 items
  2. Student completes one assigned passage; coach's homework report shows 1/3 complete with the session date and acoustic score
  3. Assigned items appear in the student's session history correctly labelled "Homework" vs. "Free practice"
  4. A student with no homework assigned sees no "Assigned by your coach" section
**Estimated complexity**: M
**UI hint**: yes

---

### Phase 18: Session Reports & File Export

**Goal**: Any session can be exported as a human-readable report and shared with a coach (or kept as a record) without any network connection.
**Depends on**: Phase 15 (profiles), Phase 9 (evaluation scoring), Phase 5 (recordings)
**Requirements**: REQ-I04
**Tasks**:
  1. Build HTML report template (Jinja2 or string-template): sections for session metadata, F0-over-time line chart (embedded as SVG), vowel trajectory scatter, per-dimension scores table, recording waveform image, and notes field
  2. Implement PDF export via Qt's `QPrinter` (render HTML to PDF); fall back to WeasyPrint if QPrinter output quality is insufficient; note platform caveat
  3. Define `.sov-session` file format: ZIP container with `session.json` (metadata + scores), `audio.wav` (recording if exists), `charts/` (SVG exports), `report.html`
  4. Build read-only `.sov-session` viewer: drag-in or file-open; renders the HTML report in a `QWebEngineView` (or plain widget fallback); no DB writes
  5. Add "Export session" button to the session history list (Phase 1 Progress tab): opens file-save dialog for `.sov-session` or PDF
  6. Write tests for HTML template rendering (snapshot test), `.sov-session` ZIP round-trip, PDF generation smoke test (file size > 0, valid PDF header), and viewer load from file
**Success Criteria**:
  1. Clicking "Export session" on any session in history produces a `.sov-session` file containing valid JSON metadata and an HTML report
  2. PDF export produces a readable multi-section document with at least one embedded chart
  3. Opening a `.sov-session` in the viewer on a second machine (with a fresh profile, no shared DB) shows the full report without errors
  4. A `.sov-session` file with a missing or corrupt `session.json` produces a clear error in the viewer rather than a crash
**Estimated complexity**: M
**UI hint**: yes

---

### Phase 19: Coach Analytics View

**Goal**: A coach can open the app in their profile and see a clear picture of each student's voice training journey over time.
**Depends on**: Phase 15 (coach profile), Phase 17 (homework), Phase 18 (session data)
**Requirements**: REQ-I06
**Tasks**:
  1. Build coach analytics dashboard: accessible from the coach profile's Progress tab; student selector dropdown shows all profiles on this machine
  2. Implement F0 trend chart per student: weekly mean F0 over a rolling 8-week window, rendered as a line chart (pyqtgraph); overlaid with target range band
  3. Implement resonance improvement chart: F1/F2 centroid (Euclidean distance from feminine reference point) per week over 8 weeks
  4. Build "First vs. Now" passage comparison panel: side-by-side rendering of oldest and most recent evaluation for any passage — waveform thumbnails, score table, delta badges (↑/↓/→)
  5. Add session notes field: free-text annotation per session entry (stored in `session_notes` table: profile_id, session_id, note_text, created_at); visible in session history and coach dashboard
  6. Implement full student progress PDF export: multi-page document — cover summary, F0 trend chart, resonance chart, first-vs-now comparison for top 3 passages, session list
  7. Write tests for analytics aggregation queries (weekly averages, correct date bucketing), PDF multi-page smoke test, and session notes CRUD
**Success Criteria**:
  1. Coach switching to student "Alex" sees Alex's F0 trend chart populated with weekly averages for each week Alex has trained
  2. "First vs. Now" panel for a passage shows visibly different scores if the student has improved, with correct delta badges
  3. Session note entered by coach appears in the session history view under the correct session entry
  4. Exported student progress PDF contains all expected sections and is longer than 2 pages for a student with 4+ weeks of data
**Estimated complexity**: M
**UI hint**: yes

---

### Phase 20: Real-Time Remote Coaching *(Future — Deferred)*

**Goal**: Coach can observe a student's live session remotely over the internet, seeing the same acoustic data the student sees, and annotate moments in real time.
**Depends on**: Phase 19 (all offline instructor features complete); requires a backend service not yet designed
**Requirements**: REQ-I05
**Tasks**: *None planned. This phase is a placeholder.*

**Design constraints for future implementation** (architecture must not foreclose this):
  - Domain/service layer must remain storage-agnostic (already a Phase 1 constraint)
  - Acoustic data frames must be serialisable to JSON/MessagePack (for WebSocket relay)
  - Coach annotation format must be designed so offline annotations (Phase 19 session notes) and live annotations (this phase) share the same data model
  - No proprietary A/V relay — SwitchedOnVoice handles only the acoustic data stream; video is external (Zoom, etc.)

**Success Criteria**: N/A (deferred)
**Estimated complexity**: XL *(backend + real-time sync + security design)*

---

### Phase 21: Singing Mode Foundations

**Goal**: User can switch the app into Singing mode and get appropriate feedback calibrated for singing rather than speech.
**Depends on**: Phase 1 (acoustic pipeline), Phase 6 (baseline/settings schema)
**Requirements**: REQ-S01, REQ-S04
**Tasks**:
  1. Add Speaking / Singing mode selector toggle to the Analysis tab header (persistent per profile in settings)
  2. Implement separate singing acoustic baseline: distinct F0 reference range (e.g., soprano 260–1050 Hz, mezzo 220–880 Hz) configurable in onboarding re-run or Settings
  3. Implement singing-specific CPP thresholds: singing CPP warning fires at a different (lower) threshold than speech CPP, reflecting different phonation effort norms
  4. Build fatigue detector: compute a rolling 5-minute pitch accuracy trend; alert when accuracy degrades >15 % from session start ("Your pitch control is dropping — consider a rest")
  5. Add rest reminder timer: configurable extended singing session threshold (default 20 min); display gentle reminder dialog with a snooze option
  6. Write tests for mode-switching state persistence, singing baseline loading, CPP threshold dispatch, fatigue detection on synthetic degrading data, and rest timer trigger
**Success Criteria**:
  1. Switching to Singing mode changes the pitch meter target range to the singing baseline; switching back restores the speech baseline — no app restart required
  2. A synthetic CPP value below the singing threshold triggers a warning; the same value does not trigger one in Speech mode (if above speech threshold)
  3. A simulated 20-minute session triggers the rest reminder at the correct time; snoozing defers it by 5 minutes
  4. Fatigue detection fires correctly on a sequence of gradually worsening synthetic accuracy values
**Estimated complexity**: M
**UI hint**: yes

---

### Phase 22: Melody Following

**Goal**: User can pick a song from a library of public domain melodies and practice singing it with real-time pitch accuracy feedback.
**Depends on**: Phase 21 (singing mode baseline active)
**Requirements**: REQ-S02
**Tasks**:
  1. Build public domain melody library: encode 12+ folk songs and nursery rhymes as note sequences in a JSON format (note name, start_time_ms, duration_ms, frequency_hz) — sources: traditional tunes free of copyright (e.g., *Scarborough Fair*, *Greensleeves*, *Twinkle Twinkle*)
  2. Build melody renderer: display note bars on a pitch-over-time scrolling timeline; each bar is a coloured rectangle at the target frequency, scrolling left as the song progresses
  3. Implement real-time melody scoring: for each note, compute pitch accuracy (cents deviation from target), onset timing accuracy (ms), and detect vibrato (F0 oscillation ≥ 5 Hz)
  4. Build `MelodyBrowserWidget`: scrollable song list with title, estimated range, and difficulty indicator; launches the melody game on selection
  5. Build performance results screen: pitch accuracy % per note (colour-coded bar chart), overall timing score, vibrato count, XP earned
  6. Write tests for note target rendering data preparation, per-note accuracy computation (cents formula correctness), vibrato detection on synthetic F0 waveforms, and melody library schema validation
**Success Criteria**:
  1. Melody browser shows at least 10 songs; selecting one launches the note-target scrolling display
  2. Singing near a target note frequency turns the bar green; singing off-pitch turns it red — transitions are smooth and responsive
  3. Performance results screen shows a meaningful breakdown after finishing a complete melody
  4. Melody scores feed into XP and appear in the XP Breakdown panel
**Estimated complexity**: L
**UI hint**: yes

---

### Phase 23: Singing Exercise Library

**Goal**: User can warm up their singing voice and work on range extension through structured exercises that require no musical reading ability.
**Depends on**: Phase 21 (singing mode), Phase 22 (melody infrastructure reused)
**Requirements**: REQ-S03
**Tasks**:
  1. Define exercise library: 5 warm-up scales (chromatic ascend/descend, major scale, pentatonic), 4 arpeggio patterns, and 6 interval drills (thirds, fifths, octaves) — each as a pitch contour sequence
  2. Create soprano / mezzo-soprano / contralto range variants for each exercise via transposition (semitone offset applied to base sequence)
  3. Render all exercises as pitch contour graphs using the melody note-target renderer from Phase 22 — no musical notation used; numbers or solfège syllables only as optional labels
  4. Build exercise browser: filterable by range (soprano/mezzo/contralto), type (scale/arpeggio/interval), and difficulty (entry/intermediate/advanced)
  5. Integrate singing exercises into the skill tree: add a "Singing" skill category with Pitch Range, Vibrato, and Breath Control skills; map exercises to tiers
  6. Wire exercise completion to XP and personal bests via `ArcadeRepository` + `CurriculumService`; write tests for range filter logic, contour transposition arithmetic, and skill tree integration
**Success Criteria**:
  1. Exercise browser lists all exercises with correct range and type labels; filtering by "contralto" shows only contralto variants
  2. Completing a chromatic scale exercise displays a pitch contour graph — not musical staff notation — and awards XP
  3. After completing entry-tier singing exercises, the intermediate-tier singing skill node unlocks in the skill tree
  4. Personal best is tracked per exercise per range variant independently (a contralto score does not overwrite a soprano score for the same exercise)
**Estimated complexity**: M
**UI hint**: yes

---

## Requirement Coverage

| Requirement | Description | Phase |
|-------------|-------------|-------|
| REQ-R01 | Public domain book content library | Phase 2 |
| REQ-R02 | Reading Mode UI (display, highlight, navigation, bookmark) | Phase 3 |
| REQ-R03 | Real-time acoustic feedback while reading | Phase 4 |
| REQ-R04 | Recording & playback history | Phase 5 |
| REQ-R05 | Progress persistence (bookmark, completion, scores) | Phase 4 *(schema: 2, bookmark: 3, scores: 4, completion: 5)* |
| REQ-C01 | Skill tree / curriculum DAG | Phase 6 (data), Phase 7 (UI) |
| REQ-C02 | Daily goals and streaks | Phase 8 |
| REQ-C03 | Evaluation mode with report card | Phase 9 |
| REQ-C04 | Adaptive recommendations | Phase 10 |
| REQ-C05 | XP and levels | Phase 6 (data), Phase 7 (UI) |
| REQ-A01 | Pitch Targeting game | Phase 11 |
| REQ-A02 | Resonance Drill game | Phase 12 |
| REQ-A03 | Siren Glide exercise | Phase 13 |
| REQ-A04 | Vowel Shaping game | Phase 12 |
| REQ-A05 | Rhythm & Cadence exercise | Phase 13 |
| REQ-A06 | Personal bests and arcade history | Phase 11 (data), Phase 14 (UI) |
| REQ-I01 | Multi-profile support | Phase 15 |
| REQ-I02 | Curriculum authoring | Phase 16 |
| REQ-I03 | Homework assignment | Phase 17 |
| REQ-I04 | Session reports (offline/file-based) | Phase 18 |
| REQ-I05 | Real-time remote coaching (future) | Phase 20 *(deferred)* |
| REQ-I06 | Coach analytics view | Phase 19 |
| REQ-S01 | Singing vs. speaking mode selector | Phase 21 |
| REQ-S02 | Melody following | Phase 22 |
| REQ-S03 | Singing exercise library | Phase 23 |
| REQ-S04 | Vocal health in singing mode | Phase 21 |
| REQ-NF01 | Latency ≤ 20 ms (cross-cutting) | All phases — maintained from Phase 1 |
| REQ-NF02 | Storage usage display + deletion | Phase 5 |
| REQ-NF03 | Offline-first (architectural constraint) | All phases |
| REQ-NF04 | Cross-platform (macOS/Linux/Windows) | All phases |
| REQ-NF05 | Accessibility (WCAG AA, keyboard nav) | All phases with UI |
| REQ-NF06 | Privacy (no outbound network) | All phases |

**Coverage: 26/26 functional requirements mapped (REQ-I05 mapped to Phase 20 as deferred). ✓**
**4 non-functional requirements are cross-cutting architectural constraints applied throughout. ✓**

---

## Progress

| Phase | Goal | Milestone | Plans Complete | Status | Completed |
|-------|------|-----------|----------------|--------|-----------|
| 1 — Foundation | DSP pipeline + UI + storage | v1.0 | 25/25 | ✅ Complete | 2026-05-28 |
| 2 — Content Library | Books ingested, progress schema | v1.1 | 0/? | Not started | — |
| 3 — Reading Mode UI | Passage display, navigation, bookmark | v1.1 | 0/? | Not started | — |
| 4 — Acoustic Overlay | Live feedback + session summary | v1.1 | 0/? | Not started | — |
| 5 — Recording History | Recording pipeline + playback | v1.1 | 0/? | Not started | — |
| 6 — Curriculum Schema | Skill DAG + XP tables + levels | v1.2 | 0/? | Not started | — |
| 7 — Skill Tree UI | Visual tree + XP display + level-up | v1.2 | 0/? | Not started | — |
| 8 — Daily Goals | Home widget + adaptive streaks | v1.2 | 0/? | Not started | — |
| 9 — Evaluation Mode | Report card + trend graphs | v1.2 | 0/? | Not started | — |
| 10 — Recommendations | Weakness detection + suggestions | v1.2 | 0/? | Not started | — |
| 11 — Arcade + Pitch Game | Arcade tab + Pitch Targeting | v1.3 | 0/? | Not started | — |
| 12 — Resonance + Vowel | Resonance Drill + Vowel Shaping | v1.3 | 0/? | Not started | — |
| 13 — Siren + Rhythm | Siren Glide + Rhythm & Cadence | v1.3 | 0/? | Not started | — |
| 14 — Arcade History | Personal bests + sparklines | v1.3 | 0/? | Not started | — |
| 15 — Multi-Profile | Profile switcher + data isolation | v1.4 | 0/? | Not started | — |
| 16 — Curriculum Authoring | Coach curriculum builder + export | v1.4 | 0/? | Not started | — |
| 17 — Homework | Assignment flow + completion tracking | v1.4 | 0/? | Not started | — |
| 18 — Session Export | HTML/PDF reports + .sov-session | v1.4 | 0/? | Not started | — |
| 19 — Coach Analytics | Per-student dashboards + PDF export | v1.4 | 0/? | Not started | — |
| 20 — Remote Coaching | *Deferred — requires backend* | v1.4 | N/A | Deferred | — |
| 21 — Singing Foundations | Mode selector + singing baselines | v2.0 | 0/? | Not started | — |
| 22 — Melody Following | Note targets + scoring | v2.0 | 0/? | Not started | — |
| 23 — Singing Exercises | Exercise library + range variants | v2.0 | 0/? | Not started | — |

---

*Last updated: 2026-05-28*
