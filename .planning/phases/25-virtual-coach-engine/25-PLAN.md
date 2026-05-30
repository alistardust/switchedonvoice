# Phase 25: Virtual Coach Engine Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide 1–3 affirming, deterministic coaching messages based on the user's real progress data, with durable dismiss/snooze behavior and no network or LLM dependency.

**Architecture:** Split Phase 25 into four layers: packaged JSON rule content, a pure `CoachingEngine`, SQLite-backed message state persistence, and a Qt `CoachingPanel` shown in a dedicated Coach tab. Build user state in a separate context-builder/service layer so the core engine remains a pure function whose output depends only on explicit inputs. Use a small `CoachingContextBuilder` class that wraps the pure `build_coaching_context(...)` helper and exposes `.build(now=...)` to the service.

**Tech Stack:** Python 3.11+, sqlite3, dataclasses, json, pathlib, PySide6, pytest, pytest-qt, uv

---

## File Map

### New modules
- `src/switchedonvoice/coaching/__init__.py` — package exports
- `src/switchedonvoice/coaching/models.py` — immutable dataclasses for context, rules, state, and service output
- `src/switchedonvoice/coaching/rule_loader.py` — JSON loading/validation
- `src/switchedonvoice/coaching/engine.py` — pure rule evaluation and ranking
- `src/switchedonvoice/coaching/context_builder.py` — contains the pure `build_coaching_context(...)` helper plus a thin `CoachingContextBuilder` class that fetches storage data and exposes `.build(now)`
- `src/switchedonvoice/coaching/service.py` — orchestration layer that loads rules, builds context, filters by persistence state, and returns the top 1–3 messages
- `src/switchedonvoice/coaching/assets/default_rules.json` — default catalog with at least 40 rule-message pairs
- `src/switchedonvoice/storage/coaching.py` — repository for shown/dismissed/snoozed state
- `src/switchedonvoice/ui/coaching_panel.py` — UI for top messages and dismiss/snooze actions

### Modified modules
- `src/switchedonvoice/storage/db.py` — add DDL + next schema migration for coaching-message state
- `src/switchedonvoice/ui/main_window.py` — add a dedicated Coach tab and connect it to the coaching service
- `tests/storage/test_db.py` — bump schema-version assertion

### Tests
- `tests/coaching/__init__.py`
- `tests/coaching/conftest.py`
- `tests/coaching/test_rule_loader.py`
- `tests/coaching/test_engine.py`
- `tests/coaching/test_context_builder.py`
- `tests/coaching/test_service.py`
- `tests/storage/conftest.py` (create if still absent; otherwise extend)
- `tests/storage/test_coaching.py`
- `tests/ui/test_coaching_panel.py`
- `tests/ui/test_main_window.py`

## Chunk 1: Rule catalog and pure engine

### Task 1: Create the coaching rule schema, loader, and default rule catalog

**Files:**
- Create: `src/switchedonvoice/coaching/__init__.py`
- Create: `src/switchedonvoice/coaching/models.py`
- Create: `src/switchedonvoice/coaching/rule_loader.py`
- Create: `src/switchedonvoice/coaching/assets/default_rules.json`
- Create: `tests/coaching/__init__.py`
- Test: `tests/coaching/test_rule_loader.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

from switchedonvoice.coaching.rule_loader import load_coaching_rules


def test_default_rule_catalog_contains_minimum_40_rules() -> None:
    rules = load_coaching_rules()

    assert len(rules) >= 40
    assert {rule.category for rule in rules} >= {
        "plateau",
        "recovery",
        "achievement",
        "fatigue",
        "milestone",
    }


def test_each_rule_has_stable_id_priority_and_message_text() -> None:
    rules = load_coaching_rules()

    assert all(rule.rule_id for rule in rules)
    assert all(rule.priority >= 0 for rule in rules)
    assert all(rule.text.strip() for rule in rules)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/coaching/test_rule_loader.py -q`

Expected: FAIL because the package, loader, and JSON asset do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

Use a strict schema with stable IDs and declarative conditions.

```json
{
  "rule_id": "plateau-f0-encouragement-01",
  "priority": 30,
  "category": "plateau",
  "condition": {
    "all": [
      {"metric": "recent_sessions_count", "op": "gte", "value": 3},
      {"metric": "is_pitch_plateau", "op": "eq", "value": true}
    ]
  },
  "text": "You've still been showing up, and that matters. Try one shorter, lighter practice block today.",
  "action_hint": "Open a gentle pitch-focused exercise"
}
```

```python
@dataclass(frozen=True)
class CoachingRule:
    rule_id: str
    priority: int
    category: str
    condition: dict[str, object]
    text: str
    action_hint: str | None


@dataclass(frozen=True)
class CoachingMessage:
    rule_id: str
    priority: int
    category: str
    text: str
    action_hint: str | None
```

Also add `CoachingDecision(messages, suppressed_rule_ids, generated_at)` to `models.py` so the context doc and service contract stay aligned, and so Phase 26 can safely read `message.category` when driving avatar states.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/coaching/test_rule_loader.py -q`

Expected: PASS, with 40+ validated rule entries.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/coaching/__init__.py src/switchedonvoice/coaching/models.py src/switchedonvoice/coaching/rule_loader.py src/switchedonvoice/coaching/assets/default_rules.json tests/coaching/__init__.py tests/coaching/test_rule_loader.py
git commit -m "feat: add coaching rule catalog" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 2: Implement the pure CoachingEngine and deterministic ranking

**Files:**
- Create: `src/switchedonvoice/coaching/engine.py`
- Test: `tests/coaching/test_engine.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

from datetime import datetime, timezone

from switchedonvoice.coaching.engine import evaluate_coaching_rules
from switchedonvoice.coaching.models import CoachingContext, CoachingRule


def test_engine_returns_same_ranked_output_for_same_input() -> None:
    context = CoachingContext(
        recent_sessions_count=5,
        is_pitch_plateau=True,
        streak_days=12,
        now=datetime(2026, 5, 30, tzinfo=timezone.utc),
    )
    rules = [
        CoachingRule(
            rule_id="plateau-01",
            priority=20,
            category="plateau",
            condition={"metric": "is_pitch_plateau", "op": "eq", "value": True},
            text="You're not stuck — you're consolidating.",
            action_hint="Repeat yesterday's warmup",
        ),
    ]

    assert evaluate_coaching_rules(context, rules) == evaluate_coaching_rules(context, rules)


def test_engine_supports_changed_recently_and_category_rank_ordering() -> None:
    context = CoachingContext(
        streak_days=0,
        had_streak_break_recently=True,
        last_personal_best_at=datetime(2026, 5, 29, tzinfo=timezone.utc),
        now=datetime(2026, 5, 30, tzinfo=timezone.utc),
    )
    rules = [
        CoachingRule(
            rule_id="achievement-01",
            priority=10,
            category="achievement",
            condition={"metric": "last_personal_best_at", "op": "changed_recently", "days": 7},
            text="You hit a new personal best.",
            action_hint=None,
        ),
        CoachingRule(
            rule_id="streak-recovery-01",
            priority=10,
            category="recovery",
            condition={"metric": "had_streak_break_recently", "op": "eq", "value": True},
            text="A missed day doesn't erase your progress.",
            action_hint=None,
        ),
    ]

    messages = evaluate_coaching_rules(context, rules)
    assert [message.rule_id for message in messages] == ["achievement-01", "streak-recovery-01"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/coaching/test_engine.py -q`

Expected: FAIL because `evaluate_coaching_rules` does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

1. Add a tiny operator dispatcher (`eq`, `gte`, `lte`, `in`, `changed_recently`, `all`, `any`, `not`).
2. Resolve metric names against `CoachingContext` attributes only.
3. Define `_CATEGORY_RANK` and sort by `(priority, _CATEGORY_RANK[category], rule_id)`.

```python
_CATEGORY_RANK = {
    "achievement": 0,
    "milestone": 1,
    "plateau": 2,
    "recovery": 3,
    "fatigue": 4,
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/coaching/test_engine.py -q`

Expected: PASS, proving purity and deterministic ordering.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/coaching/engine.py tests/coaching/test_engine.py
git commit -m "feat: add pure coaching engine" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

## Chunk 2: Persistence, context assembly, and UI delivery

### Task 3: Add coaching-message state persistence and context building

**Files:**
- Modify: `src/switchedonvoice/storage/db.py`
- Create: `src/switchedonvoice/storage/coaching.py`
- Create or extend: `tests/storage/conftest.py`
- Modify: `tests/storage/test_db.py`
- Create: `src/switchedonvoice/coaching/context_builder.py`
- Test: `tests/storage/test_coaching.py`
- Test: `tests/coaching/test_context_builder.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from switchedonvoice.coaching.context_builder import build_coaching_context
from switchedonvoice.coaching.models import SessionHistorySummary
from switchedonvoice.storage.coaching import CoachingStateRepository


def test_snooze_defers_rule_for_exactly_seven_days(db_path) -> None:
    repository = CoachingStateRepository(db_path)
    now = datetime(2026, 5, 30, tzinfo=timezone.utc)

    repository.snooze("plateau-01", now)

    state = repository.get_state("plateau-01")
    assert state.snoozed_until == now + timedelta(days=7)


def test_context_builder_defaults_missing_milestone_recording_signal_to_false() -> None:
    context = build_coaching_context(
        history_summary=SessionHistorySummary(total_sessions=0, streak_days=0),
        milestone_recording_summary=None,
        now=datetime(2026, 5, 30, tzinfo=timezone.utc),
    )
    assert context.has_first_milestone_recording is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/storage/test_coaching.py tests/coaching/test_context_builder.py -q`

Expected: FAIL because the repository, migration, and context builder do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

1. Add `CREATE TABLE IF NOT EXISTS coaching_message_state (...)` to `_SCHEMA` in `src/switchedonvoice/storage/db.py`.
2. Read the current `_CURRENT_SCHEMA_VERSION` value and assign `NEXT_SCHEMA_VERSION` as the next literal integer. 3. Bump `_CURRENT_SCHEMA_VERSION` to `NEXT_SCHEMA_VERSION`.
4. In `_migrate()`, keep older blocks hard-coded to their own literal values, then append `if version < NEXT_SCHEMA_VERSION: con.execute(f"PRAGMA user_version = {NEXT_SCHEMA_VERSION}")`.
5. Update `tests/storage/test_db.py::test_schema_version_is_set` to assert `NEXT_SCHEMA_VERSION`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/storage/test_coaching.py tests/coaching/test_context_builder.py tests/storage/test_db.py -q`

Expected: PASS, including exact seven-day snooze math and safe default context assembly.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/storage/db.py src/switchedonvoice/storage/coaching.py src/switchedonvoice/coaching/context_builder.py tests/storage/conftest.py tests/storage/test_coaching.py tests/coaching/test_context_builder.py tests/storage/test_db.py
git commit -m "feat: persist coaching message state" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 4: Build the orchestration service that merges rules, context, and suppression state

**Files:**
- Create: `src/switchedonvoice/coaching/service.py`
- Create: `tests/coaching/conftest.py`
- Test: `tests/coaching/test_service.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

from datetime import datetime, timezone

from switchedonvoice.coaching.service import CoachingService


def test_service_returns_only_top_three_unsuppressed_messages(fake_context_builder, fake_repository, fake_rules) -> None:
    service = CoachingService(
        rules=fake_rules,
        context_builder=fake_context_builder,
        state_repository=fake_repository,
        now_fn=lambda: datetime(2026, 5, 30, tzinfo=timezone.utc),
    )

    messages = service.get_messages(limit=3)

    assert len(messages) == 3
    assert all(message.rule_id != "dismissed-rule" for message in messages)


def test_service_hides_recently_shown_rule_within_repeat_window(fake_context_builder, fake_repository, fake_rules) -> None:
    service = CoachingService(
        rules=fake_rules,
        context_builder=fake_context_builder,
        state_repository=fake_repository,
        now_fn=lambda: datetime(2026, 5, 30, tzinfo=timezone.utc),
    )

    messages = service.get_messages(limit=3)

    assert "repeat-too-soon" not in [message.rule_id for message in messages]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/coaching/test_service.py -q`

Expected: FAIL because the service layer does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

Create `tests/coaching/conftest.py` with `fake_context_builder`, `fake_repository`, and `fake_rules` fixtures so the tests stay deterministic. The fake context builder must expose `.build(now=...)` to match the real `CoachingContextBuilder` class introduced in Task 3.

```python
class CoachingService:
    def __init__(self, rules, context_builder, state_repository, now_fn) -> None:
        self._rules = rules
        self._context_builder = context_builder
        self._state_repository = state_repository
        self._now_fn = now_fn

    def get_messages(self, limit: int = 3) -> list[CoachingMessage]:
        context = self._context_builder.build(now=self._now_fn())
        ranked = evaluate_coaching_rules(context, self._rules)
        visible = [message for message in ranked if self._state_repository.should_display(message.rule_id, self._now_fn())]
        return visible[:limit]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd /home/alice/git/switchedonvoice && uv run pytest tests/coaching/test_service.py -q`

Expected: PASS, showing top-three truncation and repeat suppression.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/coaching/service.py tests/coaching/conftest.py tests/coaching/test_service.py
git commit -m "feat: add coaching service orchestration" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 5: Build the CoachingPanel widget and wire it into a dedicated Coach tab

**Files:**
- Create: `src/switchedonvoice/ui/coaching_panel.py`
- Modify: `src/switchedonvoice/ui/main_window.py`
- Test: `tests/ui/test_coaching_panel.py`
- Modify: `tests/ui/test_main_window.py`

- [ ] **Step 1: Write the failing UI/integration tests**

```python
from __future__ import annotations


def test_coaching_panel_renders_up_to_three_messages(qtbot) -> None:
    panel = CoachingPanel()
    qtbot.addWidget(panel)

    panel.set_messages(sample_messages)

    assert panel.message_count() == 3


def test_main_window_adds_coach_tab_when_service_is_available(qtbot) -> None:
    with patched_main_window_dependencies(coaching_messages=sample_messages[:2]) as window:
        qtbot.addWidget(window)
        assert window.centralWidget().count() >= 5
        assert window.centralWidget().tabText(3) == "Coach"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd /home/alice/git/switchedonvoice && QT_QPA_PLATFORM=offscreen uv run pytest tests/ui/test_coaching_panel.py tests/ui/test_main_window.py -q`

Expected: FAIL because the panel and Coach tab do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

1. Create a focused `CoachingPanel` with one message card per visible message.
2. Keep the widget passive: it receives `set_messages(...)` data and emits `dismiss_requested(rule_id)` / `snooze_requested(rule_id)`.
3. In `MainWindow`, instantiate the coaching service and add a new `Coach` tab immediately before `Settings` in the `QTabWidget`.
4. Use the existing `tests/ui/test_main_window.py` mocking pattern for `init_db`, `load_settings`, `AudioCapture`, and `create_session` so the new integration test does not hit real I/O.

- [ ] **Step 4: Run the focused UI tests, then the full phase slice**

Run: `cd /home/alice/git/switchedonvoice && QT_QPA_PLATFORM=offscreen uv run pytest tests/ui/test_coaching_panel.py tests/ui/test_main_window.py tests/coaching tests/storage/test_coaching.py -q`

Expected: PASS, including panel rendering, engine logic, storage behavior, and Coach-tab integration.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/ui/coaching_panel.py src/switchedonvoice/ui/main_window.py tests/ui/test_coaching_panel.py tests/ui/test_main_window.py
git commit -m "feat: add coaching panel ui" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 6: Final verification pass for Phase 25

**Files:**
- Verify only; no planned code changes in this task

- [ ] **Step 1: Run lint checks on the new coaching surface**

Run: `cd /home/alice/git/switchedonvoice && uv run ruff check src/switchedonvoice/coaching src/switchedonvoice/storage/coaching.py src/switchedonvoice/ui/coaching_panel.py tests/coaching tests/storage/test_coaching.py tests/ui/test_coaching_panel.py tests/ui/test_main_window.py`

Expected: `All checks passed!`

- [ ] **Step 2: Run type checking on the new modules**

Run: `cd /home/alice/git/switchedonvoice && uv run mypy src/switchedonvoice/coaching src/switchedonvoice/storage/coaching.py src/switchedonvoice/ui/coaching_panel.py`

Expected: `Success: no issues found`

- [ ] **Step 3: Run the full test suite**

Run: `cd /home/alice/git/switchedonvoice && QT_QPA_PLATFORM=offscreen uv run pytest -q`

Expected: PASS with the new coaching tests included.

- [ ] **Step 4: Manual smoke test**

Run: `cd /home/alice/git/switchedonvoice && uv run python run.py`

Expected: The Coach tab shows 1–3 relevant, non-repetitive coaching messages; dismiss suppresses immediately; snooze hides the message until exactly seven days later.

- [ ] **Step 5: Commit any final polish**

```bash
git add -A
git commit -m "chore: final polish for virtual coach engine" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

Plan complete and saved to `.planning/phases/25-virtual-coach-engine/25-PLAN.md`. Ready to execute?
