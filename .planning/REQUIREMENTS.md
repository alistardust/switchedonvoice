# Requirements — SwitchedOnVoice Full Product Vision

> **Milestone scope:** Full product roadmap (v1.1 through v2.0+)
> **Derived from:** Phase 1 validated constraints + milestone questioning (2026-05-28)
> **Status:** Draft — pending roadmap

---

## Vision Statement

SwitchedOnVoice is a solo desktop voice feminisation training companion for trans people. It combines real-time acoustic measurement with engaging practice modes — reading, exercises, structured curriculum, and eventually singing — to make voice training rewarding, trackable, and joyful over the long term.

Inspired by Rocksmith (instrument-teacher game), Duolingo (structured habit with adaptation), and Kindle (long-form progress through content) — but purpose-built for trans voice feminisation.

---

## Guiding Constraints (carried from Phase 1)

- **Python + PySide6 desktop app** (macOS/Linux/Windows)
- **No backend required initially** — fully local, all data on-device by default; architecture must not foreclose a future optional backend
- **No proprietary content** — exercises and reading passages use public domain texts only
- **Privacy-first** — audio never leaves the device without explicit user action
- **Open source** (MIT licence)
- **Accessible** — usable without musical training or prior voice coaching knowledge
- **Desktop first; mobile later** — architecture decisions must not foreclose mobile
- **Backend-ready** — domain/service layer must be decoupled from storage so a cloud backend can be added later without rewriting business logic

---

## Functional Requirements by Milestone

---

### MILESTONE v1.1 — Reading / Narration Mode

> Goal: Give users compelling practice content and a way to hear their progress over time.

#### REQ-R01: Content Library
- App ships with at least 3 public domain books (Alice in Wonderland, Wizard of Oz, Anne of Green Gables)
- Books are split into chapters; chapters into practisable passages (~100–200 words)
- Content stored as structured data (not hardcoded)
- New books can be added by dropping files into a watched folder or via an in-app browser

#### REQ-R02: Reading Mode UI
- Display passage text in a large, readable font with good contrast
- Highlight current word or sentence as user reads (visual progress tracking)
- Kindle-style bookmark: remember exact position in each book across sessions
- Chapter navigation (previous / next chapter, jump-to-chapter list)

#### REQ-R03: Real-Time Feedback While Reading
- Pitch meter, vowel space plot, and spectrum visualiser active while reading
- Optional overlay: colour-coded word highlighting based on whether pitch was in target range during that word
- Session summary shown after finishing a passage (avg F0, resonance score, CPP health, time)

#### REQ-R04: Recording and Playback
- Every reading session is optionally recorded (user opt-in per session or globally)
- Recordings saved locally: `~/.switchedonvoice/recordings/<book>/<chapter>/<date>.wav`
- "Listen to my history" view: timeline of recordings for the same passage, playable in order
- Waveform display for each recording in the history view

#### REQ-R05: Progress Persistence
- Per-book reading position persisted to SQLite
- Per-passage completion count and last-attempted date
- First and most recent acoustic scores per passage for comparison

---

### MILESTONE v1.2 — Structured Curriculum + Evaluations

> Goal: Give users a Duolingo-style learning path with scored assessments and adaptive guidance.

#### REQ-C01: Skill Tree / Curriculum
- Skills are organised in a directed graph (DAG): must demonstrate Skill A before unlocking Skill B
- Initial skill categories: Pitch (F0), Resonance (F1/F2/F3), Vocal Quality (CPP), Clarity, Intonation
- Each skill has entry-level, intermediate, and advanced tiers
- Completing exercises in a skill tier awards XP and unlocks the next tier

#### REQ-C02: Daily Goals and Streaks
- User sets a daily practice goal (minutes or exercises)
- Streak counter tracks consecutive days meeting the goal
- App surfaces a "Today's goal" widget on the home screen
- Daily goal adjusts based on session history (adaptive difficulty)

#### REQ-C03: Evaluation Mode
- User selects any passage and enters "Evaluation" mode (no live hints, no feedback during reading)
- After finishing: full report card with per-dimension scores (pitch accuracy, resonance, CPP, pacing, consistency)
- Each score dimension explained in plain language ("Your average pitch was 187 Hz — in the feminine range!")
- Scores stored and graphed over time per passage for trend analysis

#### REQ-C04: Adaptive Recommendations
- After each session, app surfaces 1–3 suggested next exercises based on weakest dimensions
- Suggestions link directly to relevant curriculum exercises or arcade games
- "Just let me choose" override always visible — suggestions are non-intrusive

#### REQ-C05: XP and Levels
- XP earned for: completing exercises, finishing passages, hitting daily goals, evaluation scores
- Levels are meaningful milestones with names/flavour text (not just numbers)
- XP breakdown visible so users understand what they earned

---

### MILESTONE v1.3 — Vocal Arcade

> Goal: Build skill through targeted, fun, arcade-style mini-games.

#### REQ-A01: Pitch Targeting Game
- Falling targets appear on a pitch-over-time display; user must hit and hold the pitch
- Difficulty: target size, speed, and required hold duration scale up
- Score: accuracy percentage + consistency bonus

#### REQ-A02: Resonance Drill Game
- Bullseye target appears on the vowel space plot; user moves their resonance to hit it
- Vowel targets cycle through front, back, high, low positions
- Feedback: immediate visual snap when on target; points for dwell time

#### REQ-A03: Siren Glide Exercise
- On-screen path (sine wave or arc) displayed over a pitch timeline
- User must follow the path smoothly — measures path-following accuracy
- Good for: smoothing glottal breaks, pitch range extension

#### REQ-A04: Vowel Shaping Game
- Phone-style bubble targets appear on the vowel space plot (F1/F2 plane)
- User must produce the target vowel sound to pop the bubble
- Teaches explicit control of tongue/lip position mapping to formant space

#### REQ-A05: Rhythm and Cadence Exercise
- Target speech waveform envelope or syllable timing displayed
- User reads a prompt phrase; score based on matching pace, pauses, and syllable stress
- Develops naturalness of intonation patterns

#### REQ-A06: Personal Bests and Arcade Leaderboard
- Each game stores all-time personal best scores
- In-game history graph (last 10 attempts)
- Score feeds into XP

---

### MILESTONE v1.4 — Instructor Mode

> Goal: Enable trans vocal coaches to use SwitchedOnVoice as a professional tool — creating custom curricula, assigning homework, and reviewing student sessions — both in-person and remotely.

#### REQ-I01: Multi-Profile Support
- App supports multiple named local profiles (student accounts on one machine)
- Each profile has independent: session history, progress, recordings, curriculum state, settings
- Profile switcher on the home screen (no passwords required — this is not a security boundary)
- Coach profile type: elevated permissions to create/edit curricula and view student data

#### REQ-I02: Curriculum Authoring
- Coaches can create custom exercise sequences, reading passage selections, and drills
- Custom curricula saved as structured data (JSON internally; exportable as a `.sov-curriculum` package)
- Curriculum builder UI: drag-and-drop ordering, free-text instruction blocks, passage assignments, exercise targets (e.g., "hit 180 Hz average for 3 sessions")
- Custom reading passages: coach can paste in their own text (not limited to built-in library)

#### REQ-I03: Homework Assignment
- Coach selects exercises/passages and marks them as assigned homework for a specific student profile
- Student's home screen shows "Assigned by your coach" section with pending homework
- Homework completion tracked separately from free-practice sessions
- Completion reports generated per homework assignment for coach review

#### REQ-I04: Session Reports (Offline / File-Based)
- Any session can be exported as a structured report: PDF or HTML with acoustic charts, scores, recording waveform
- Curriculum packages (`.sov-curriculum`) importable by student machines — coach creates on their machine, shares via email/file/cloud storage, student imports
- Session data exportable as `.sov-session` for coach to review on their own machine (drag in, see graphs)

#### REQ-I05: Real-Time Remote Session Sharing (Requires Backend — Future)
- **Phase 1 of instructor mode is fully offline/file-based (REQ-I01 through REQ-I04)**
- Future: optional backend enabling coach to observe a student's live session in real-time
  - Coach joins a session "room" (student shares a session link/code)
  - Coach sees live pitch meter, vowel space, spectrum — same data the student sees
  - Coach can annotate (text/audio) moments in the session; annotations saved to student's recording
  - Works alongside video call (Zoom, etc.) — SwitchedOnVoice is the data layer; video is external
  - No proprietary video/audio relay — coach just sees the acoustic data stream

#### REQ-I06: Coach-Specific Analytics View
- Per-student progress dashboard: F0 trend over weeks, resonance improvement, curriculum completion rate
- Compare first session vs. most recent session for any passage
- Session notes field: coach can annotate sessions with free text
- Export full student progress report (PDF)

---

> Goal: Extend the app to cover sung voice feminisation and general pitch training.

#### REQ-S01: Singing vs. Speaking Detection
- Distinct mode selector in UI: Speaking / Singing
- Separate acoustic baseline for singing (pitched note range vs. speech F0 range)

#### REQ-S02: Melody Following
- Public domain melody displayed as note targets on a pitch-over-time graph
- User sings; app scores pitch accuracy, timing, and vibrato quality
- Supports simple melodies (folk songs, nursery rhymes in public domain)

#### REQ-S03: Singing Exercise Library
- Warm-up scales, arpeggio exercises, and interval drills
- Sorted by range: soprano, mezzo, contralto friendly variants
- No musical reading required — all exercises shown as pitch contour graphs

#### REQ-S04: Vocal Health in Singing Mode
- Singing-specific CPP thresholds (separate from speech)
- Fatigue detection: warns if pitch accuracy is degrading over the session
- Rest reminder after extended singing sessions

---

## Non-Functional Requirements

#### REQ-NF01: Latency
- Audio analysis pipeline latency ≤ 20 ms end-to-end (maintained from Phase 1)
- UI rendering must not drop below 30 fps during active analysis

#### REQ-NF02: Storage
- Recordings stored in standard formats (WAV or FLAC, not proprietary)
- Storage usage estimate shown in Settings; user can delete recordings per book/date

#### REQ-NF03: Offline-First
- All features work without internet connection
- No analytics, telemetry, or outbound connections of any kind

#### REQ-NF04: Cross-Platform
- macOS, Linux, Windows support maintained throughout
- Desktop-first architecture decisions must not foreclose future mobile port

#### REQ-NF05: Accessibility
- All text at minimum WCAG AA contrast ratio
- Keyboard navigation for all primary workflows
- Screen reader compatible labels on all interactive elements (Qt accessibility layer)

#### REQ-NF06: Privacy
- Audio files never leave the device
- No user accounts, no cloud sync
- All data in `~/.switchedonvoice/` (user-controlled, deletable)

---

## Out of Scope (all milestones)

- Public social features, community leaderboards, or public sharing
- Speech therapy clinical integration or medical claims
- AI-generated voice coaching or LLM integration
- Proprietary content, licensed music, or DRM
- **Backend services are deferred, not ruled out** — instructor real-time sync (REQ-I05) is explicitly planned as a future backend feature

---

*Last updated: 2026-05-28*
