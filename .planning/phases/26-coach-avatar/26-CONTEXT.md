# Phase 26: Coach Avatar Shell - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Goal

Phase 26 wraps the Phase 25 coaching messages in an expressive visual shell: a
placeholder avatar, state/animation hooks, optional offline TTS, and simple
personality scripts that make the coach feel like a character without making the
message system dependent on commissioned art or network services.

This phase is presentation and delivery infrastructure. The underlying coaching
logic remains in Phase 25.
</domain>

<dependencies>
## Dependencies on Earlier Phases

- **Phase 25 — Virtual Coach Engine:** supplies the message objects, categories,
  and panel events the avatar layer will render and speak.
- **Existing settings persistence:** `src/switchedonvoice/storage/settings.py`
  already stores user preferences atomically and is the correct place for avatar
  visibility and TTS-enable flags.
- **Existing Qt UI shell:** `src/switchedonvoice/ui/settings_panel.py` and
  `src/switchedonvoice/ui/main_window.py` are the likely host/integration points
  for replacing the dedicated Coach tab with the avatar shell.
- **Offline-only project constraint:** no network calls, cloud voices, or remote
  asset fetching are allowed.

Assume the visual design will be commissioned later. The implementation must be
useful with placeholder art and a pluggable asset contract.
</dependencies>

<decisions>
## Key Decisions

### D-26-01: Ship a placeholder SVG avatar with a swappable asset contract
Use packaged placeholder SVG art in the repository for the first implementation.
The avatar widget should load named assets/states from a manifest-friendly path so
commissioned art can replace the placeholder without changing widget logic.

### D-26-02: Avatar behavior is driven by a small state machine
Represent animation/rendering states with a named enum such as `idle`,
`speaking`, `encouraging`, and `listening`. Map coaching message categories onto
those states in a dedicated state-machine module rather than scattering category
checks across widgets.

### D-26-03: TTS is optional and capability-detected
Support a simple backend chain:
1. `pyttsx3` if importable and initializable,
2. `espeak` executable if present on `PATH`,
3. null backend otherwise.

The feature must degrade silently when unavailable and never block message display.

### D-26-04: Personality scripts live in packaged JSON
Store event-driven scripted sequences in JSON (`first-launch`, `first-milestone`,
`streak-break-recovery`, etc.) with stable event IDs and short step arrays. This
keeps copy editing separate from UI code and lets the shell reuse the same loading/
validation path as the coaching rules.

### D-26-05: Visibility is a user preference, not a runtime-only toggle
Whether the avatar is expanded or collapsed must persist in `Settings` so the UI
comes back the way the user left it after restart.

### D-26-06: Avatar delivery must remain accessible without animation or TTS
The avatar can add expression, but it must never become the sole carrier of
meaning. The text message panel stays authoritative; if the avatar is hidden or
TTS is unavailable, the user still sees every message.
</decisions>

<research>
## Research Findings

### R-26-01: PySide6 already supports vector-friendly avatar rendering paths
Because the app is already on PySide6, using SVG rendering (`QtSvg`/`QSvgRenderer`
or an equivalent widget) is the lightest way to ship placeholder art that scales
cleanly across DPI settings without pulling in a raster animation toolchain.

### R-26-02: Settings persistence is JSON-backed and backward-compatible by default
`storage/settings.py` loads a JSON dict into a dataclass with defaults. Adding new
fields such as `avatar_visible` and `coach_tts_enabled` is low-risk as long as the
loader keeps default values for older settings files.

### R-26-03: Linux offline TTS is uneven, so fallback logic matters
`pyttsx3` is convenient but can fail depending on the installed speech backend.
Checking for `espeak` on the system path gives a reliable second option for offline
speech on Linux. Both checks must be guarded and testable without real audio.

### R-26-04: UI responsiveness must win over character polish
The real-time app already has a strict three-thread model. Avatar rendering and TTS
must stay off the audio callback/analysis path and should never block the Qt event
loop when a coaching message arrives.

### R-26-05: Personality scripts should be treated as content, not logic
Common coach reactions are editorial data. If those scripts are embedded directly
into widgets, iterating on tone later becomes expensive and brittle.
</research>

<data_model>
## Data Model

### Settings additions

Recommended new `Settings` fields:

```python
avatar_visible: bool = True
coach_tts_enabled: bool = False
coach_tts_backend: str | None = None
```

### Dataclasses / Interfaces

- `AvatarState` enum: `IDLE`, `SPEAKING`, `ENCOURAGING`, `LISTENING`
- `AvatarCue(message_category, state, duration_ms)`
- `PersonalityLine(event_id, text, state, speak_aloud)`
- `PersonalityScript(event_id, lines)`
- `TTSBackend` protocol with `is_available()`, `speak(text)`, and `stop()`
- `AvatarDeliveryRequest(message, cue, personality_event_id | None)`

### Package Assets

- `src/switchedonvoice/coach_avatar/assets/placeholder_avatar.svg`
- `src/switchedonvoice/coach_avatar/assets/personality.json`

### UI Composition

Recommended shell components:

- `AvatarWidget` — renders current visual state
- `CoachShellWidget` — composes `AvatarWidget`, coaching text, and optional TTS
- `AvatarDirector`/state machine — maps incoming message categories and scripted
  events onto visual and spoken output
</data_model>

<open_questions>
## Open Questions Deferred to Later Phases

1. What exact commissioned asset format should the future art pack use: per-state
   SVGs, sprite sheets, or layered vector parts? The placeholder contract should
   stay simple until art direction is signed off.
2. Should the coach eventually support selectable personas or voices? Deferred;
   Phase 26 only needs one default shell.
3. Should TTS queue interruption rules be configurable (interrupt current speech,
   queue next message, or drop duplicates)? A minimal single-message policy is
   enough for the first release.
4. Should the avatar react continuously to live microphone state (`listening`) or
   only to coaching-message delivery? The roadmap only requires message-driven
   states, so live-listening animation is deferred.
</open_questions>

---

*Phase: 26-coach-avatar*
*Context gathered: 2026-05-30 for plan authoring*
