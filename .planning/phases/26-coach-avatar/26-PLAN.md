# Phase 26: Coach Avatar Shell Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver coaching messages through a collapsible avatar shell with placeholder art, state-driven expression hooks, optional offline TTS, and packaged personality scripts.

**Architecture:** Build a small `coach_avatar` package that owns assets, state mapping, personality scripts, and TTS capability detection. Keep the existing coaching text panel authoritative, then compose it with an `AvatarWidget` inside a new `CoachShellWidget` so the avatar can be hidden, swapped, or upgraded without rewriting the coaching engine.

**Tech Stack:** Python 3.11+, PySide6 (including SVG-capable widgets/renderers), settings JSON persistence, subprocess/shutil for safe local TTS detection, pytest, pytest-qt, uv

---

**Prerequisite:** Execute Phase 25 first. This plan assumes `CoachingPanel`, `CoachingMessage`, and the dedicated Coach tab already exist.

## File Map

### New modules
- `src/switchedonvoice/coach_avatar/__init__.py` — package exports
- `src/switchedonvoice/coach_avatar/models.py` — avatar state, cues, and personality dataclasses
- `src/switchedonvoice/coach_avatar/state_machine.py` — maps coaching categories/events to avatar states
- `src/switchedonvoice/coach_avatar/avatar_widget.py` — renders placeholder SVG art and exposes state changes
- `src/switchedonvoice/coach_avatar/tts.py` — capability detection plus null/pyttsx3/espeak backends
- `src/switchedonvoice/coach_avatar/personality.py` — loads and validates packaged scripted events
- `src/switchedonvoice/coach_avatar/assets/placeholder_avatar.svg` — placeholder character art
- `src/switchedonvoice/coach_avatar/assets/personality.json` — scripted response sequences
- `src/switchedonvoice/ui/coach_shell_widget.py` — composes avatar + coaching panel + collapse control

### Modified modules
- `src/switchedonvoice/storage/settings.py` — add avatar visibility / TTS settings with backward-compatible defaults and explicit `load_settings()` field mapping
- `src/switchedonvoice/ui/settings_panel.py` — expose avatar/TTS toggles
- `src/switchedonvoice/ui/main_window.py` — replace the Coach tab’s content with `CoachShellWidget` and trigger personality events at first launch, first milestone, and streak-break recovery
- `tests/ui/test_main_window.py` — extend the existing mock-heavy window tests for Coach-tab integration

### Tests
- `tests/coach_avatar/__init__.py`
- `tests/coach_avatar/test_personality.py`
- `tests/coach_avatar/test_state_machine.py`
- `tests/coach_avatar/test_tts.py`
- `tests/ui/test_coach_shell_widget.py`
- `tests/storage/test_settings.py`
- `tests/ui/test_main_window.py`

## Chunk 1: Assets, state, and optional TTS

### Task 1: Extend settings and add packaged avatar/personality assets

**Files:**
- Modify: `src/switchedonvoice/storage/settings.py`
- Create: `src/switchedonvoice/coach_avatar/__init__.py`
- Create: `src/switchedonvoice/coach_avatar/models.py`
- Create: `src/switchedonvoice/coach_avatar/personality.py`
- Create: `src/switchedonvoice/coach_avatar/assets/placeholder_avatar.svg`
- Create: `src/switchedonvoice/coach_avatar/assets/personality.json`
- Create: `tests/coach_avatar/__init__.py`
- Test: `tests/coach_avatar/test_personality.py`
- Test: `tests/storage/test_settings.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

from switchedonvoice.coach_avatar.personality import load_personality_scripts
from switchedonvoice.storage.settings import Settings, load_settings, save_settings


def test_personality_scripts_include_required_event_ids() -> None:
    scripts = load_personality_scripts()

    assert {script.event_id for script in scripts} >= {
        "first-launch",
        "first-milestone",
        "streak-break-recovery",
    }


def test_settings_round_trip_avatar_visibility_and_tts(tmp_path) -> None:
    settings_path = tmp_path / "settings.json"
    save_settings(
        settings_path,
        Settings(avatar_visible=False, coach_tts_enabled=True, coach_tts_backend="espeak"),
    )

    loaded = load_settings(settings_path)
    assert loaded.avatar_visible is False
    assert loaded.coach_tts_enabled is True
    assert loaded.coach_tts_backend == "espeak"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/coach_avatar/test_personality.py tests/storage/test_settings.py -q`

Expected: FAIL because the new assets/fields do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

1. Add `avatar_visible`, `coach_tts_enabled`, and `coach_tts_backend` to the `Settings` dataclass with safe defaults.
2. Update `load_settings()` to read `data.get("avatar_visible", True)`, `data.get("coach_tts_enabled", False)`, and `data.get("coach_tts_backend")` explicitly, matching the existing constructor pattern.
3. Create placeholder SVG art and personality JSON with the required hyphenated event IDs.
4. Implement a tiny loader that returns typed script dataclasses.

```python
@dataclass(frozen=True)
class PersonalityScript:
    event_id: str
    lines: tuple[PersonalityLine, ...]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/coach_avatar/test_personality.py tests/storage/test_settings.py -q`

Expected: PASS with asset loading and settings persistence covered.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/storage/settings.py src/switchedonvoice/coach_avatar/__init__.py src/switchedonvoice/coach_avatar/models.py src/switchedonvoice/coach_avatar/personality.py src/switchedonvoice/coach_avatar/assets/placeholder_avatar.svg src/switchedonvoice/coach_avatar/assets/personality.json tests/coach_avatar/__init__.py tests/coach_avatar/test_personality.py tests/storage/test_settings.py
git commit -m "feat: add coach avatar assets and settings" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 2: Implement the avatar state machine and placeholder AvatarWidget

**Files:**
- Create: `src/switchedonvoice/coach_avatar/state_machine.py`
- Create: `src/switchedonvoice/coach_avatar/avatar_widget.py`
- Test: `tests/coach_avatar/test_state_machine.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

from switchedonvoice.coach_avatar.avatar_widget import AvatarWidget
from switchedonvoice.coach_avatar.models import AvatarState
from switchedonvoice.coach_avatar.state_machine import avatar_state_for_message


def test_avatar_state_for_achievement_message_is_encouraging() -> None:
    assert avatar_state_for_message("achievement") == AvatarState.ENCOURAGING


def test_avatar_widget_updates_state_label_and_asset(qtbot) -> None:
    widget = AvatarWidget()
    qtbot.addWidget(widget)

    widget.set_state(AvatarState.SPEAKING)

    assert widget.current_state() is AvatarState.SPEAKING
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /home/alice/git/switchedonvoice && QT_QPA_PLATFORM=offscreen uv run pytest tests/coach_avatar/test_state_machine.py -q`

Expected: FAIL because the state machine and widget do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

1. Introduce an `AvatarState` enum in `models.py`.
2. Map categories to states in one pure function.
3. Implement `AvatarWidget` as a focused Qt widget that renders the placeholder SVG and exposes `set_state(...)`.
4. Keep real animation minimal in v1; a state change hook plus visual label/CSS/SVG swap is enough.

```python
def avatar_state_for_message(category: str) -> AvatarState:
    return {
        "achievement": AvatarState.ENCOURAGING,
        "milestone": AvatarState.ENCOURAGING,
        "reminder": AvatarState.SPEAKING,
        "plateau": AvatarState.LISTENING,
    }.get(category, AvatarState.IDLE)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd /home/alice/git/switchedonvoice && QT_QPA_PLATFORM=offscreen uv run pytest tests/coach_avatar/test_state_machine.py -q`

Expected: PASS with deterministic category-to-state mapping.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/coach_avatar/state_machine.py src/switchedonvoice/coach_avatar/avatar_widget.py tests/coach_avatar/test_state_machine.py
git commit -m "feat: add avatar widget shell" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 3: Add optional offline TTS capability detection and graceful fallback

**Files:**
- Create: `src/switchedonvoice/coach_avatar/tts.py`
- Test: `tests/coach_avatar/test_tts.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

from switchedonvoice.coach_avatar.tts import NullTTSBackend, detect_tts_backend


def test_detect_tts_backend_returns_null_backend_when_no_runtime_available(monkeypatch) -> None:
    monkeypatch.setattr("switchedonvoice.coach_avatar.tts._import_pyttsx3", lambda: None)
    monkeypatch.setattr("switchedonvoice.coach_avatar.tts.which", lambda _: None)

    backend = detect_tts_backend()

    assert isinstance(backend, NullTTSBackend)


def test_detect_tts_backend_prefers_espeak_when_binary_exists(monkeypatch) -> None:
    monkeypatch.setattr("switchedonvoice.coach_avatar.tts._import_pyttsx3", lambda: None)
    monkeypatch.setattr("switchedonvoice.coach_avatar.tts.which", lambda _: "/usr/bin/espeak")

    backend = detect_tts_backend()

    assert backend.backend_name == "espeak"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/coach_avatar/test_tts.py -q`

Expected: FAIL because the TTS module does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

1. Create a `TTSBackend` protocol plus `NullTTSBackend`, `Pyttsx3Backend`, and `EspeakBackend`.
2. Use `from shutil import which` so the monkeypatch path in the tests is valid.
3. Use guarded detection in priority order: pyttsx3, then espeak, then null.
4. Call `subprocess.Popen([...])` with an argument list, never `shell=True`.

```python
def detect_tts_backend() -> TTSBackend:
    pyttsx3_module = _import_pyttsx3()
    if pyttsx3_module is not None:
        return Pyttsx3Backend(pyttsx3_module)
    espeak_path = which("espeak")
    if espeak_path is not None:
        return EspeakBackend(espeak_path)
    return NullTTSBackend()
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/coach_avatar/test_tts.py -q`

Expected: PASS with both null and espeak fallback paths covered.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/coach_avatar/tts.py tests/coach_avatar/test_tts.py
git commit -m "feat: add optional avatar tts backends" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

## Chunk 2: UI composition and integration

### Task 4: Build the CoachShellWidget that composes avatar, coaching text, and personality cues

**Files:**
- Create: `src/switchedonvoice/ui/coach_shell_widget.py`
- Test: `tests/ui/test_coach_shell_widget.py`

- [ ] **Step 1: Write the failing UI tests**

```python
from __future__ import annotations

from switchedonvoice.coaching.models import CoachingMessage
from switchedonvoice.coach_avatar.models import AvatarState
from switchedonvoice.ui.coach_shell_widget import CoachShellWidget


achievement_message = CoachingMessage(
    rule_id="achievement-01",
    priority=10,
    category="achievement",
    text="Great work today.",
    action_hint=None,
)
reminder_message = CoachingMessage(
    rule_id="reminder-01",
    priority=20,
    category="reminder",
    text="A short reset session still counts.",
    action_hint=None,
)


def test_coach_shell_updates_avatar_state_when_messages_arrive(qtbot) -> None:
    widget = CoachShellWidget()
    qtbot.addWidget(widget)

    widget.set_messages([achievement_message])

    assert widget.avatar_widget.current_state() is AvatarState.ENCOURAGING


def test_coach_shell_can_collapse_avatar_without_hiding_message_text(qtbot) -> None:
    widget = CoachShellWidget()
    qtbot.addWidget(widget)
    widget.set_messages([reminder_message])

    widget.set_avatar_visible(False)

    assert widget.avatar_widget.isHidden()
    assert widget.message_count() == 1
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /home/alice/git/switchedonvoice && QT_QPA_PLATFORM=offscreen uv run pytest tests/ui/test_coach_shell_widget.py -q`

Expected: FAIL because the shell widget does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

1. Compose `AvatarWidget` and the Phase 25 `CoachingPanel` in a single container widget.
2. Drive avatar state from the first/highest-priority visible message.
3. Optionally trigger TTS only when settings permit and a non-null backend is available.
4. Add a `play_personality_event(event_id)` hook that loads the JSON script and steps through its lines.

```python
def set_messages(self, messages: list[CoachingMessage]) -> None:
    self._coaching_panel.set_messages(messages)
    if messages:
        self._avatar_widget.set_state(avatar_state_for_message(messages[0].category))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd /home/alice/git/switchedonvoice && QT_QPA_PLATFORM=offscreen uv run pytest tests/ui/test_coach_shell_widget.py -q`

Expected: PASS, including collapsed-avatar behavior with message text preserved.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/ui/coach_shell_widget.py tests/ui/test_coach_shell_widget.py
git commit -m "feat: add coach shell widget" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 5: Wire the coach shell into settings and the main window lifecycle

**Files:**
- Modify: `src/switchedonvoice/ui/settings_panel.py`
- Modify: `src/switchedonvoice/ui/main_window.py`
- Modify: `tests/ui/test_main_window.py`
- Test: `tests/ui/test_coach_shell_widget.py`
- Test: `tests/storage/test_settings.py`

- [ ] **Step 1: Write the failing integration tests**

```python
from __future__ import annotations


def test_settings_panel_persists_avatar_visibility_toggle(qtbot, settings_path) -> None:
    panel = SettingsPanel(settings_path=settings_path)
    qtbot.addWidget(panel)

    panel._avatar_visible_checkbox.setChecked(False)
    panel._save_button.click()

    assert load_settings(settings_path).avatar_visible is False


def test_main_window_plays_personality_event_for_first_milestone(qtbot) -> None:
    with patched_main_window_dependencies() as window:
        qtbot.addWidget(window)
        window._handle_first_milestone_recorded()
        assert window._coach_shell.last_personality_event_id() == "first-milestone"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /home/alice/git/switchedonvoice && QT_QPA_PLATFORM=offscreen uv run pytest tests/ui/test_main_window.py tests/ui/test_coach_shell_widget.py tests/storage/test_settings.py -q`

Expected: FAIL because the settings and main-window wiring are incomplete.

- [ ] **Step 3: Write the minimal implementation**

1. Add avatar visibility and TTS controls to `SettingsPanel`.
2. In `MainWindow`, replace the Coach tab’s widget with `CoachShellWidget` rather than modifying `AnalysisPanel`.
3. Extend the existing `tests/ui/test_main_window.py` patching pattern (`init_db`, `load_settings`, `AudioCapture`, `create_session`, etc.) for the new personality-event test.
4. Trigger personality events at first launch, first milestone, and streak-break recovery.
5. Persist every visibility/TTS change through the existing `save_settings()` flow.

```python
self._settings.avatar_visible = self._avatar_visible_checkbox.isChecked()
self._settings.coach_tts_enabled = self._coach_tts_checkbox.isChecked()
```

- [ ] **Step 4: Run the focused tests, then the full phase slice**

Run: `cd /home/alice/git/switchedonvoice && QT_QPA_PLATFORM=offscreen uv run pytest tests/coach_avatar tests/ui/test_coach_shell_widget.py tests/ui/test_main_window.py tests/storage/test_settings.py -q`

Expected: PASS, including persistence, state transitions, and graceful TTS fallback.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/ui/settings_panel.py src/switchedonvoice/ui/main_window.py tests/ui/test_main_window.py tests/ui/test_coach_shell_widget.py tests/storage/test_settings.py
git commit -m "feat: integrate coach avatar shell" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 6: Final verification pass for Phase 26

**Files:**
- Verify only; no planned code changes in this task

- [ ] **Step 1: Run lint checks on the new avatar surface**

Run: `cd /home/alice/git/switchedonvoice && uv run ruff check src/switchedonvoice/coach_avatar src/switchedonvoice/ui/coach_shell_widget.py src/switchedonvoice/ui/settings_panel.py tests/coach_avatar tests/ui/test_coach_shell_widget.py tests/ui/test_main_window.py`

Expected: `All checks passed!`

- [ ] **Step 2: Run type checking on the new modules**

Run: `cd /home/alice/git/switchedonvoice && uv run mypy src/switchedonvoice/coach_avatar src/switchedonvoice/ui/coach_shell_widget.py src/switchedonvoice/ui/settings_panel.py`

Expected: `Success: no issues found`

- [ ] **Step 3: Run the full test suite**

Run: `cd /home/alice/git/switchedonvoice && QT_QPA_PLATFORM=offscreen uv run pytest -q`

Expected: PASS with all avatar, coaching, and existing tests included.

- [ ] **Step 4: Manual smoke test**

Run: `cd /home/alice/git/switchedonvoice && uv run python run.py`

Expected: The Coach tab renders placeholder art, shifts state when coaching messages arrive, optionally speaks when a local TTS backend is available and enabled, and stays collapsed/expanded across app restart.

- [ ] **Step 5: Commit any final polish**

```bash
git add -A
git commit -m "chore: final polish for coach avatar shell" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

Plan complete and saved to `.planning/phases/26-coach-avatar/26-PLAN.md`. Ready to execute?
