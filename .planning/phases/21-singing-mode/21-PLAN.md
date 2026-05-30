# Phase 21: Singing Mode Foundations Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the user switch between Speaking and Singing modes and immediately receive mode-appropriate pitch, CPP, fatigue, and rest-reminder feedback.

**Architecture:** Add a small `switchedonvoice.singing` domain package for mode-aware target ranges and vocal-health logic, extend `Settings` to persist singing preferences, and wire the Qt UI through `MainWindow._tick()` so all singing state updates stay on the main thread. No DSP changes are needed; the existing analysis thread continues to produce `AnalysisResult`, and the UI/domain layers reinterpret that data for singing use cases.

**Tech Stack:** Python 3.11, PySide6, dataclasses, existing `AnalysisResult` pipeline, JSON settings persistence, pytest, pytest-qt

---

## File map

**Create:**
- `src/switchedonvoice/singing/__init__.py`
- `src/switchedonvoice/singing/models.py`
- `src/switchedonvoice/singing/health.py`
- `src/switchedonvoice/ui/rest_reminder_dialog.py`
- `tests/singing/test_health.py`

**Modify:**
- `src/switchedonvoice/storage/settings.py`
- `src/switchedonvoice/ui/analysis_panel.py`
- `src/switchedonvoice/ui/main_window.py`
- `src/switchedonvoice/ui/settings_panel.py`
- `tests/storage/test_settings.py`
- `tests/ui/test_analysis_panel.py`
- `tests/ui/test_main_window.py`

**Why this split:**
- `storage/settings.py` remains the single persistence source of truth.
- `singing/health.py` keeps fatigue / CPP / reminder logic pure and unit-testable.
- `analysis_panel.py` owns the header toggle + warning presentation.
- `main_window.py` remains the only place that consumes the live queue and session clock.

## Chunk 1: Settings and pure singing domain logic

### Task 1: Persist mode and singing baselines in settings

**Files:**
- Modify: `src/switchedonvoice/storage/settings.py`
- Test: `tests/storage/test_settings.py`

- [ ] **Step 1: Write the failing settings tests**

Add focused tests to `tests/storage/test_settings.py`:

```python
def test_save_and_reload_preserves_voice_mode_and_singing_preset(settings_path: Path) -> None:
    settings = Settings(
        voice_mode="singing",
        singing=SingingModeSettings(selected_preset="contralto", rest_reminder_minutes=25),
    )
    save_settings(settings_path, settings)

    loaded = load_settings(settings_path)
    assert loaded.voice_mode == "singing"
    assert loaded.singing.selected_preset == "contralto"
    assert loaded.singing.rest_reminder_minutes == 25


def test_load_settings_defaults_singing_ranges_when_keys_missing(settings_path: Path) -> None:
    settings_path.write_text('{"voice_mode": "singing"}')
    loaded = load_settings(settings_path)
    assert loaded.singing.mezzo_min_hz == pytest.approx(220.0)
    assert loaded.singing.contralto_max_hz == pytest.approx(700.0)
```

- [ ] **Step 2: Run the failing tests**

Run: `pytest tests/storage/test_settings.py -k singing -q`

Expected: FAIL with `TypeError` or `AttributeError` because `Settings` has no
`voice_mode` / `singing` fields yet.

- [ ] **Step 3: Implement the minimal settings schema**

Extend `src/switchedonvoice/storage/settings.py`:

```python
from dataclasses import asdict, dataclass, field

SPEECH_MODE = "speaking"
SINGING_MODE = "singing"

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
    voice_mode: str = SPEECH_MODE
    singing: SingingModeSettings = field(default_factory=SingingModeSettings)
```

Requirements while implementing:
- Keep `from __future__ import annotations` as the first code line.
- Add helper loaders like `_load_singing_settings(data: dict[str, object]) -> SingingModeSettings`.
- Keep atomic writes through `save_settings()` unchanged.
- Validate all Hz fields with named helpers; do not scatter raw numeric checks.

- [ ] **Step 4: Run the settings tests again**

Run: `pytest tests/storage/test_settings.py -q`

Expected: PASS for the new singing tests and the pre-existing settings tests.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/storage/settings.py tests/storage/test_settings.py
git commit -m "feat: persist singing mode settings"
```

### Task 2: Add pure mode, CPP, fatigue, and reminder logic

**Files:**
- Create: `src/switchedonvoice/singing/__init__.py`
- Create: `src/switchedonvoice/singing/models.py`
- Create: `src/switchedonvoice/singing/health.py`
- Test: `tests/singing/test_health.py`

- [ ] **Step 1: Write the failing unit tests first**

Create `tests/singing/test_health.py` with pure-function coverage:

```python
def test_get_active_target_range_returns_singing_preset_when_mode_is_singing() -> None:
    settings = Settings(voice_mode="singing")
    target_range = get_active_target_range(settings)
    assert target_range.min_hz == pytest.approx(220.0)
    assert target_range.max_hz == pytest.approx(880.0)


def test_assess_cpp_uses_mode_specific_thresholds() -> None:
    settings = Settings()
    speaking = assess_cpp(VoiceMode.SPEAKING, 8.0, settings)
    singing = assess_cpp(VoiceMode.SINGING, 8.0, settings)
    assert speaking.is_warning is True
    assert singing.is_warning is False


def test_fatigue_detector_flags_fifteen_percent_drop() -> None:
    detector = FatigueDetector(window_minutes=5, drop_fraction=0.15)
    for second in range(120):
        detector.add_sample(timestamp_s=float(second), accuracy=0.92)
    snapshot = None
    for second in range(120, 480):
        snapshot = detector.add_sample(timestamp_s=float(second), accuracy=0.73)
    assert snapshot is not None
    assert snapshot.is_fatigued is True


def test_rest_reminder_snooze_defers_next_prompt() -> None:
    state = RestReminderState.started(now_s=0.0, reminder_after_minutes=20, snooze_minutes=5)
    assert should_prompt_rest(now_s=1200.0, state=state) is True
    snoozed = state.snooze(now_s=1200.0)
    assert should_prompt_rest(now_s=1499.0, state=snoozed) is False
    assert should_prompt_rest(now_s=1500.0, state=snoozed) is True
```

- [ ] **Step 2: Run the pure tests to confirm they fail**

Run: `pytest tests/singing/test_health.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'switchedonvoice.singing'`.

- [ ] **Step 3: Implement the minimal pure domain package**

Create `src/switchedonvoice/singing/models.py` and `src/switchedonvoice/singing/health.py`.
Start with:

```python
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import StrEnum

class VoiceMode(StrEnum):
    SPEAKING = "speaking"
    SINGING = "singing"

@dataclass(frozen=True)
class TargetRange:
    min_hz: float
    max_hz: float
    label: str
```

`health.py` should provide:
- `get_active_target_range(settings: Settings) -> TargetRange`
- `assess_cpp(mode: VoiceMode, cpp_db: float | None, settings: Settings) -> CppAssessment`
- `FatigueDetector.add_sample(timestamp_s: float, accuracy: float) -> FatigueSnapshot | None`
- `RestReminderState.started(...)` and `should_prompt_rest(...)`

Implementation rules:
- Use named constants such as `_SECONDS_PER_MINUTE`, `_DEFAULT_SINGING_LABEL`.
- Clamp accuracy samples to `[0.0, 1.0]` in one helper.
- Return `None` from `assess_cpp()` when `cpp_db is None`; the UI should not invent warnings.
- Keep the fatigue detector pure; it must not know about Qt, widgets, or timers.

- [ ] **Step 4: Re-run the singing unit tests**

Run: `pytest tests/singing/test_health.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/singing/__init__.py src/switchedonvoice/singing/models.py src/switchedonvoice/singing/health.py tests/singing/test_health.py
git commit -m "feat: add singing mode health logic"
```

## Chunk 2: Qt integration and session-time reminders

### Task 3: Add the analysis-tab mode toggle and singing settings UI

**Files:**
- Modify: `src/switchedonvoice/ui/analysis_panel.py`
- Modify: `src/switchedonvoice/ui/settings_panel.py`
- Test: `tests/ui/test_analysis_panel.py`

- [ ] **Step 1: Add failing Qt tests**

Extend `tests/ui/test_analysis_panel.py` with pytest-qt coverage:

```python
def test_analysis_panel_mode_toggle_updates_pitch_range(qtbot) -> None:
    panel = AnalysisPanel()
    qtbot.addWidget(panel)
    panel.apply_settings(Settings(voice_mode="speaking"))
    panel.set_voice_mode(VoiceMode.SINGING)
    assert panel.current_target_range().min_hz == pytest.approx(220.0)
    assert panel.current_target_range().max_hz == pytest.approx(880.0)


def test_cpp_warning_text_uses_singing_threshold(qtbot) -> None:
    panel = AnalysisPanel()
    qtbot.addWidget(panel)
    panel.apply_settings(Settings(voice_mode="singing"))
    result = make_result(f0=330.0, cpp=8.0, is_voiced=True)
    panel.update_result(result)
    assert "warning" not in panel.cpp_status_text().lower()
```

- [ ] **Step 2: Run the failing UI tests headlessly**

Run: `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_analysis_panel.py -q`

Expected: FAIL because `AnalysisPanel` does not yet expose a mode toggle,
settings application API, or CPP status helpers.

- [ ] **Step 3: Implement the UI wiring**

In `src/switchedonvoice/ui/analysis_panel.py`:
- Add a header row with a `QComboBox` or `QButtonGroup` for Speaking / Singing.
- Add `voice_mode_changed = Signal(str)`.
- Add `apply_settings(settings: Settings)`, `set_voice_mode(mode: VoiceMode)`,
  `current_target_range()`, and `cpp_status_text()` helper methods for tests.
- On mode changes, call `PitchMeterWidget.set_f0_target_range()` with the
  resolved `TargetRange` from `singing.health`.
- Surface CPP warnings in a dedicated label under the CPP value; do not encode
  the warning solely as colour.

In `src/switchedonvoice/ui/settings_panel.py`:
- Add a “Singing mode” group with range-preset selection and min/max spinboxes.
- Add spinboxes for speech/singing CPP thresholds and rest reminder minutes.
- Save everything through the existing `save_settings()` path.

Suggested `analysis_panel.py` seam:

```python
self._mode_combo = QComboBox()
self._mode_combo.addItem("Speaking", VoiceMode.SPEAKING.value)
self._mode_combo.addItem("Singing", VoiceMode.SINGING.value)
self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
```

- [ ] **Step 4: Re-run the focused UI tests**

Run: `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_analysis_panel.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/ui/analysis_panel.py src/switchedonvoice/ui/settings_panel.py tests/ui/test_analysis_panel.py
git commit -m "feat: add singing controls to analysis ui"
```

### Task 4: Wire fatigue detection and rest reminders through MainWindow

**Files:**
- Create: `src/switchedonvoice/ui/rest_reminder_dialog.py`
- Modify: `src/switchedonvoice/ui/main_window.py`
- Test: `tests/ui/test_main_window.py`

- [ ] **Step 1: Add failing integration tests**

Extend `tests/ui/test_main_window.py` with patch-friendly tests:

```python
def test_mode_switch_persists_without_restart(tmp_path: Path) -> None:
    with patched_main_window_dependencies(tmp_path) as window:
        window._analysis_panel.voice_mode_changed.emit("singing")
        assert window._settings.voice_mode == "singing"


def test_rest_reminder_dialog_snooze_defers_reprompt(tmp_path: Path) -> None:
    with patched_main_window_dependencies(tmp_path, monotonic_values=[0.0, 1200.0, 1499.0, 1500.0]) as window:
        assert window._should_prompt_rest() is True
        window._snooze_rest_reminder()
        assert window._should_prompt_rest() is False
        assert window._should_prompt_rest() is True
```

- [ ] **Step 2: Run the failing integration tests**

Run: `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_main_window.py -q`

Expected: FAIL with missing singing-mode handlers / rest-reminder helpers.

- [ ] **Step 3: Implement the minimal integration path**

In `src/switchedonvoice/ui/rest_reminder_dialog.py`, create a small dialog with:
- message label
- `Snooze 5 min` button
- `Keep singing` / `Dismiss` button

In `src/switchedonvoice/ui/main_window.py`:
- subscribe to `self._analysis_panel.voice_mode_changed`
- update `self._settings.voice_mode` and call `save_settings()` immediately
- instantiate one `FatigueDetector` and one `RestReminderState` per session
- during `_tick()`, convert voiced `f0` samples into pitch-accuracy samples
  against the active `TargetRange`
- show a non-spamming fatigue warning in the status bar or panel when the
  detector first trips
- open `RestReminderDialog` when `should_prompt_rest()` returns `True`

Minimal accuracy helper (keep it private to `main_window.py` or move to the
singing domain if it becomes reusable):

```python
def _pitch_accuracy_for_range(f0_hz: float, target_range: TargetRange) -> float:
    if target_range.min_hz <= f0_hz <= target_range.max_hz:
        return 1.0
    if f0_hz < target_range.min_hz:
        distance = target_range.min_hz - f0_hz
    else:
        distance = f0_hz - target_range.max_hz
    return max(0.0, 1.0 - (distance / target_range.max_hz))
```

- [ ] **Step 4: Run the focused tests, then the whole affected suite**

Run:
- `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_main_window.py -q`
- `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_analysis_panel.py tests/ui/test_main_window.py tests/storage/test_settings.py tests/singing/test_health.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/ui/rest_reminder_dialog.py src/switchedonvoice/ui/main_window.py tests/ui/test_main_window.py
git commit -m "feat: add singing fatigue and rest reminders"
```

## Final verification

- [ ] Run: `QT_QPA_PLATFORM=offscreen pytest tests/storage/test_settings.py tests/singing/test_health.py tests/ui/test_analysis_panel.py tests/ui/test_main_window.py -q`
- [ ] Run: `ruff check src tests`
- [ ] Run: `mypy src`
- [ ] Verify manually: start `python run.py`, switch Speaking/Singing in the Analysis tab, confirm the pitch target band changes instantly, and confirm Settings retains the last selected mode after relaunch.

Expected final state:
- Singing mode persists in settings.
- CPP warnings are mode-specific.
- Fatigue detection fires on degrading synthetic accuracy data.
- Rest reminder triggers at 20 minutes and snooze defers by 5 minutes.

Plan complete and saved to `.planning/phases/21-singing-mode/21-PLAN.md`. Ready to execute?
