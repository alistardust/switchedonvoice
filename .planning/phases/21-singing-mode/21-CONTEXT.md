# Phase 21: Singing Mode Foundations - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning

<domain>
## Phase Goal

Phase 21 adds a first-class Singing mode so the app can switch between
speech-oriented feedback and singing-oriented feedback without restarting,
while preserving the existing three-thread audio pipeline.
</domain>

<dependencies>
## Dependencies on Earlier Phases

- **Phase 1 (Acoustic pipeline):** `AudioCapture` already delivers `AnalysisResult`
  frames with `f0`, `cpp`, voiced-state, and spectrum data on the Qt thread.
  Singing mode must consume those frames; it must not add DSP work to the
  sounddevice callback or analysis thread.
- **Phase 6 (Baseline/settings schema):** speech target-range settings,
  baseline persistence, and profile-aware curriculum assumptions already exist.
  Singing mode should extend the same settings persistence model rather than
  inventing a second configuration store.
- **Phase 7 (Progress UI):** warnings and status changes need a visible place
  to surface in the UI without blocking the 33 ms update loop.
- **Phase 15 (Multi-profile):** roadmap ordering means a future `profile_id`
  source exists before v2.0 ships. Settings and alert state should remain
  explicit about the active profile, but Phase 21 must still behave sensibly
  for the single-profile fallback.
- **Current codebase seams:** `src/switchedonvoice/ui/analysis_panel.py`
  already owns the pitch meter + CPP label, `src/switchedonvoice/ui/main_window.py`
  already drains the results queue in `_tick()`, and `src/switchedonvoice/storage/settings.py`
  already persists analysis settings atomically.
</dependencies>

<decisions>
## Key Decisions

- **D-21-01:** Add an explicit `VoiceMode` domain enum with stable persisted
  string values (`"speaking"`, `"singing"`). UI code reads and writes the enum;
  settings JSON stores only the stable lowercase strings.
- **D-21-02:** Keep speaking and singing targets as separate baseline objects.
  Speaking mode continues using the existing speech `f0_target_min/max`; singing
  mode uses a dedicated configurable range preset (`soprano`, `mezzo`,
  `contralto`) with overridable min/max values.
- **D-21-03:** Singing thresholds belong in a small pure domain/service layer
  (`switchedonvoice.singing`) rather than inside widgets. `AnalysisPanel` should
  receive resolved display state (active target range, CPP warning status,
  fatigue warning text) instead of hard-coding singing rules.
- **D-21-04:** CPP threshold dispatch is mode-aware and table-driven. The
  threshold lookup should return a named constant for the active mode instead
  of scattering `if mode == ...` checks throughout the UI.
- **D-21-05:** Fatigue detection compares a rolling five-minute pitch-accuracy
  window against an early-session reference window, not against a single frame.
  This avoids false warnings from transient pitch dips.
- **D-21-06:** Rest reminders are driven by monotonic elapsed session time plus
  a snooze-until timestamp kept on the Qt thread. The reminder UI may be modal
  or sheet-like, but it must not block the analysis thread or callback thread.
- **D-21-07:** Phase 21 introduces no new SQLite tables. Persistent singing
  configuration belongs in `settings.json`; per-session fatigue/rest state is
  ephemeral and resets each app launch.
</decisions>

<research>
## Research Findings

- **R-21-01:** Session-health timers should use a monotonic clock (for example,
  `time.monotonic()`) rather than wall-clock timestamps. System sleep, timezone
  changes, and manual clock edits otherwise create reminder drift.
- **R-21-02:** Fatigue detection is more robust when it uses downsampled,
  already-available accuracy samples (for example, once per voiced frame batch
  or once per decimated stored frame) instead of retaining every raw frame.
  That keeps memory bounded for long singing sessions.
- **R-21-03:** Sustained singing and vibrato commonly produce lower CPP than
  steady speech with otherwise healthy phonation. The singing warning threshold
  therefore needs a distinct, lower default than the speech threshold.
- **R-21-04:** Mode switching should only swap presentation targets and
  evaluation thresholds. It must not reconfigure the audio stream, restart the
  `AudioCapture` thread, or clear the queue, because that would introduce audible
  interruptions and unnecessary device churn.
- **R-21-05:** A one-shot fatigue warning with explicit reset conditions is
  safer than repeated per-frame alerts. Re-triggering on every degraded frame
  would spam the UI and train users to ignore the warning.
- **R-21-06:** Settings schema changes are cheapest when the JSON structure is
  nested now (for example, `voice_mode`, `speaking_targets`, `singing_targets`,
  `rest_reminder_minutes`). That keeps the eventual Phase 15 profile split a
  data-migration problem instead of a widget rewrite.
</research>

<data_model>
## Data Model

### Settings JSON additions

`src/switchedonvoice/storage/settings.py` should be extended with nested,
future-proof singing configuration:

```python
@dataclass
class SingingRangePreset:
    preset_slug: str
    min_hz: float
    max_hz: float

@dataclass
class SingingModeSettings:
    selected_preset: str = "mezzo"
    soprano_min_hz: float = 260.0
    soprano_max_hz: float = 1050.0
    mezzo_min_hz: float = 220.0
    mezzo_max_hz: float = 880.0
    contralto_min_hz: float = 175.0
    contralto_max_hz: float = 700.0
    speech_cpp_warning_db: float = 9.0
    singing_cpp_warning_db: float = 7.0
    fatigue_window_minutes: int = 5
    fatigue_drop_fraction: float = 0.15
    rest_reminder_minutes: int = 20
    snooze_minutes: int = 5

@dataclass
class Settings:
    ...
    voice_mode: str = "speaking"
    singing: SingingModeSettings = field(default_factory=SingingModeSettings)
```

### New pure domain types

- `VoiceMode` enum — persisted mode contract
- `TargetRange` dataclass — `{min_hz, max_hz, label}` for pitch-meter updates
- `CppAssessment` dataclass — `{threshold_db, is_warning}`
- `FatigueSnapshot` dataclass — `{baseline_accuracy, rolling_accuracy,
  drop_fraction, is_fatigued}`
- `RestReminderState` dataclass — `{started_monotonic_s, next_prompt_s,
  snooze_until_s | None}`

### Runtime interfaces

- `get_active_target_range(settings: Settings) -> TargetRange`
- `assess_cpp(mode: VoiceMode, cpp_db: float | None, settings: Settings) -> CppAssessment`
- `update_fatigue_detector(sample: float, timestamp_s: float) -> FatigueSnapshot | None`
- `should_prompt_rest(now_s: float, state: RestReminderState) -> bool`

No new SQLite migration is required in this phase.
</data_model>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md` — `REQ-S01`, `REQ-S04`
- `.planning/ROADMAP.md` §Phase 21
- `src/switchedonvoice/audio/capture.py` — live `AnalysisResult` delivery
- `src/switchedonvoice/storage/settings.py` — JSON persistence pattern
- `src/switchedonvoice/ui/analysis_panel.py` — current analysis-tab composition
- `src/switchedonvoice/ui/main_window.py` — `_tick()` integration seam
- `src/switchedonvoice/ui/pitch_meter.py` — runtime target-range override API
</canonical_refs>

<pitfalls>
## Pitfalls to Avoid

- Do **not** restart audio capture when the user flips the mode toggle.
- Do **not** keep fatigue calculations in a widget paint method; they must be
  deterministic, testable, and independent from repaint cadence.
- Do **not** hard-code soprano / mezzo / contralto values in multiple widgets.
  They belong in one named settings/domain source of truth.
- Do **not** use `elif version < N` if a later implementation decides a DB
  migration is needed after all; project convention requires independent
  `if version < N` blocks because the version is read once.
</pitfalls>

<open_questions>
## Open Questions Deferred to Later Phases

1. Should the app eventually auto-suggest Speaking vs Singing based on note
   stability or user intent, or remain manual-only?
2. Should fatigue/rest warnings be logged into progress history for coaching
   review, or remain session-local UX only?
3. When Phase 15 profiles are active, does each profile need separate custom
   singing-range overrides or just a shared preset choice?
4. Should singing mode eventually show additional health signals (for example,
   vibrato regularity or sustained-note duration) alongside CPP?
</open_questions>

---

*Phase: 21-singing-mode*
*Context gathered: 2026-05-30 for phase planning*
