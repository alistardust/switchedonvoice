# Phase 23: Singing Exercise Library Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a structured singing exercise library with range-aware variants, contour-based visuals, XP/personal-best tracking, and singing skill-tree unlocks.

**Architecture:** Build canonical exercise definitions as relative contours in the singing domain, generate soprano/mezzo/contralto variants through pure transposition helpers, and extend the Phase 22 Singing tab with an exercise browser and practice panel. Persist each completion through the generic singing-attempt repository, mirror summary scores into `ArcadeRepository`, and let `CurriculumService` own unlock decisions for the new Singing skill category.

**Tech Stack:** Python 3.11, PySide6, JSON assets, existing melody renderer/scoring infrastructure, existing `ArcadeRepository`, existing `CurriculumService`, pytest, pytest-qt

---

## File map

**Create:**
- `src/switchedonvoice/content/singing_exercises/library.json`
- `src/switchedonvoice/singing/exercise_library.py`
- `src/switchedonvoice/ui/exercise_browser_widget.py`
- `src/switchedonvoice/ui/singing_exercise_panel.py`
- `tests/singing/test_exercise_library.py`
- `tests/ui/test_exercise_browser_widget.py`
- `tests/ui/test_singing_exercise_panel.py`

**Modify:**
- `src/switchedonvoice/ui/singing_panel.py`
- `src/switchedonvoice/storage/singing.py`
- `src/switchedonvoice/arcade/repository.py`
- `src/switchedonvoice/curriculum/service.py`
- `src/switchedonvoice/curriculum/seed.py`
- `src/switchedonvoice/ui/progress_panel.py`
- `tests/storage/test_singing_repository.py`
- `tests/ui/test_progress_panel.py`

**Why this split:**
- The exercise library stays pure and reusable.
- The singing panel remains the single top-level home for all singing content.
- Progression concerns stay in curriculum/arcade layers, not in the exercise widgets.

## Chunk 1: Exercise definitions, transposition, and filtering

### Task 1: Create the exercise library and range-variant generator

**Files:**
- Create: `src/switchedonvoice/content/singing_exercises/library.json`
- Create: `src/switchedonvoice/singing/exercise_library.py`
- Test: `tests/singing/test_exercise_library.py`

- [ ] **Step 1: Write failing pure-library tests**

Create `tests/singing/test_exercise_library.py`:

```python
def test_load_exercise_variants_returns_all_expected_shapes() -> None:
    variants = load_exercise_variants()
    assert any(variant.exercise_type == "scale" for variant in variants)
    assert any(variant.exercise_type == "arpeggio" for variant in variants)
    assert any(variant.exercise_type == "interval" for variant in variants)


def test_transpose_contour_generates_contralto_variant() -> None:
    definition = make_definition(base_start_hz=220.0, contour_steps=[0, 2, 4])
    variant = build_variant(definition, range_slug="contralto")
    assert variant.range_slug == "contralto"
    assert variant.notes[0].frequency_hz == pytest.approx(175.0)


def test_filter_variants_by_range_returns_only_matching_range() -> None:
    variants = load_exercise_variants()
    filtered = filter_variants(variants, range_slug="contralto")
    assert filtered
    assert all(variant.range_slug == "contralto" for variant in filtered)
```

- [ ] **Step 2: Run the failing pure tests**

Run: `pytest tests/singing/test_exercise_library.py -q`

Expected: FAIL with missing module/asset errors.

- [ ] **Step 3: Implement the canonical library + generator**

Add at least:
- 5 scale exercises
- 4 arpeggio patterns
- 6 interval drills

In `src/switchedonvoice/singing/exercise_library.py`, implement:

```python
from __future__ import annotations

@dataclass(frozen=True)
class ExerciseDefinition:
    slug: str
    title: str
    exercise_type: str
    difficulty: str
    base_start_hz: float
    contour_steps: tuple[int, ...]
    step_duration_ms: int
    optional_labels: tuple[str, ...]

@dataclass(frozen=True)
class ExerciseVariant:
    exercise_slug: str
    range_slug: str
    exercise_type: str
    difficulty: str
    title: str
    notes: tuple[MelodyNote, ...]
```

Rules:
- `from __future__ import annotations` must be the first code line in every new module.
- Put all range anchors in named constants (`_SOPRANO_BASE_HZ`, etc.).
- Generate variants by semitone transposition from the canonical contour.
- Precompute filterable metadata on the dataclass.
- Keep loader validation strict; malformed contours should raise `ValueError`.

- [ ] **Step 4: Re-run the exercise-library tests**

Run: `pytest tests/singing/test_exercise_library.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/content/singing_exercises/library.json src/switchedonvoice/singing/exercise_library.py tests/singing/test_exercise_library.py
git commit -m "feat: add singing exercise library"
```

### Task 2: Build the exercise browser and contour-practice panel

**Files:**
- Create: `src/switchedonvoice/ui/exercise_browser_widget.py`
- Create: `src/switchedonvoice/ui/singing_exercise_panel.py`
- Modify: `src/switchedonvoice/ui/singing_panel.py`
- Test: `tests/ui/test_exercise_browser_widget.py`
- Test: `tests/ui/test_singing_exercise_panel.py`

- [ ] **Step 1: Add failing pytest-qt tests**

Create UI tests such as:

```python
def test_browser_filters_contralto_variants_only(qtbot) -> None:
    widget = ExerciseBrowserWidget(load_exercise_variants())
    qtbot.addWidget(widget)
    widget.set_range_filter("contralto")
    assert widget.visible_range_slugs() == {"contralto"}


def test_starting_exercise_loads_contour_graph(qtbot) -> None:
    panel = SingingExercisePanel()
    qtbot.addWidget(panel)
    panel.load_variant("chromatic-ascend-descend", "mezzo")
    assert panel.current_variant_slug() == "chromatic-ascend-descend/mezzo"
```

- [ ] **Step 2: Run the failing UI tests**

Run: `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_exercise_browser_widget.py tests/ui/test_singing_exercise_panel.py -q`

Expected: FAIL because the widgets and Singing-tab integration do not exist yet.

- [ ] **Step 3: Implement the minimal UI flow**

`ExerciseBrowserWidget` should expose filters for:
- range (`soprano`, `mezzo`, `contralto`)
- type (`scale`, `arpeggio`, `interval`)
- difficulty (`entry`, `intermediate`, `advanced`)

`SingingExercisePanel` should:
- reuse Phase 22 timeline/contour renderer
- show optional labels when present
- start/finish an exercise attempt
- expose `on_audio_frame(result)` so `MainWindow` forwarding remains unchanged

`src/switchedonvoice/ui/singing_panel.py` should become a two-section shell:
- Melodies
- Exercises

Use internal tabs/stacked widgets here, not a new top-level main-window tab.

- [ ] **Step 4: Re-run the focused UI tests**

Run: `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_exercise_browser_widget.py tests/ui/test_singing_exercise_panel.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/ui/exercise_browser_widget.py src/switchedonvoice/ui/singing_exercise_panel.py src/switchedonvoice/ui/singing_panel.py tests/ui/test_exercise_browser_widget.py tests/ui/test_singing_exercise_panel.py
git commit -m "feat: add singing exercise browser"
```

## Chunk 2: Progression, XP, and personal bests

### Task 3: Wire exercise completions to persistence and per-range personal bests

**Files:**
- Modify: `src/switchedonvoice/storage/singing.py`
- Modify: `src/switchedonvoice/arcade/repository.py`
- Modify: `tests/storage/test_singing_repository.py`

- [ ] **Step 1: Add failing persistence tests**

Extend `tests/storage/test_singing_repository.py`:

```python
def test_exercise_completion_uses_range_specific_score_key(db_path: Path) -> None:
    repository = SingingRepository(db_path)
    repository.save_attempt(make_exercise_summary(range_slug="contralto"), make_segments())
    best = repository.get_personal_best(content_type="exercise", content_slug="chromatic-ascend-descend/contralto")
    assert best is not None


def test_soprano_and_contralto_personal_bests_do_not_collide(db_path: Path) -> None:
    repository = SingingRepository(db_path)
    repository.save_attempt(make_exercise_summary(range_slug="soprano", overall_score=90.0), make_segments())
    repository.save_attempt(make_exercise_summary(range_slug="contralto", overall_score=75.0), make_segments())
    assert repository.get_personal_best(content_type="exercise", content_slug="chromatic-ascend-descend/soprano") == pytest.approx(90.0)
    assert repository.get_personal_best(content_type="exercise", content_slug="chromatic-ascend-descend/contralto") == pytest.approx(75.0)
```

- [ ] **Step 2: Run the failing persistence tests**

Run: `pytest tests/storage/test_singing_repository.py -q`

Expected: FAIL because exercise namespacing and PB helpers are incomplete.

- [ ] **Step 3: Implement exercise persistence rules**

Update `src/switchedonvoice/storage/singing.py` and, if required, the Phase 11
repository helper layer so exercise completions:
- save with `content_type="exercise"`
- use `content_slug="<exercise-slug>/<range-slug>"`
- mirror summary score into `ArcadeRepository` key
  `exercise/<exercise-slug>/<range-slug>`
- expose a `get_personal_best()` helper for singing content

Keep the namespacing logic centralized in one helper, for example:

```python
def exercise_score_key(exercise_slug: str, range_slug: str) -> str:
    return f"exercise/{exercise_slug}/{range_slug}"
```

- [ ] **Step 4: Re-run the persistence tests**

Run: `pytest tests/storage/test_singing_repository.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/storage/singing.py src/switchedonvoice/arcade/repository.py tests/storage/test_singing_repository.py
git commit -m "feat: track exercise personal bests by range"
```

### Task 4: Add the Singing skill-tree category and unlock flow

**Files:**
- Modify: `src/switchedonvoice/curriculum/seed.py`
- Modify: `src/switchedonvoice/curriculum/service.py`
- Modify: `src/switchedonvoice/ui/progress_panel.py`
- Modify: `tests/ui/test_progress_panel.py`

- [ ] **Step 1: Write the failing progression tests**

Add tests that prove the new category unlocks correctly:

```python
def test_entry_tier_singing_exercise_unlocks_intermediate_skill(tmp_path: Path) -> None:
    service = CurriculumService.for_test(tmp_path)
    service.record_completion(source_type="exercise", source_id="chromatic-ascend-descend/mezzo", earned_xp=40)
    snapshot = service.get_skill_tree_snapshot()
    assert snapshot.is_unlocked("singing.intermediate.pitch_range") is True


def test_progress_panel_shows_singing_category_after_seed_load(qtbot, tmp_path: Path) -> None:
    panel = ProgressPanel(db_path=tmp_path / "data.db")
    qtbot.addWidget(panel)
    assert "Singing" in panel.skill_tree_category_names()
```

- [ ] **Step 2: Run the failing progression tests**

Run: `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_progress_panel.py -q`

Expected: FAIL because the singing category and unlock rules do not exist yet.

- [ ] **Step 3: Implement curriculum integration**

In `src/switchedonvoice/curriculum/seed.py`:
- add a `singing` category
- add entry/intermediate/advanced nodes for pitch range, vibrato, breath control
- map exercise completions to those nodes via stable source IDs or tags

In `src/switchedonvoice/curriculum/service.py`:
- add a dedicated exercise-completion helper if one does not already exist
- ensure exercise XP awards re-query unlock state immediately after save

In `src/switchedonvoice/ui/progress_panel.py`:
- refresh the skill tree and XP Breakdown after exercise completion
- do not hard-code singing nodes in the widget; consume the service snapshot

- [ ] **Step 4: Re-run the progression tests and affected suite**

Run:
- `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_progress_panel.py -q`
- `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_progress_panel.py tests/ui/test_singing_exercise_panel.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/switchedonvoice/curriculum/seed.py src/switchedonvoice/curriculum/service.py src/switchedonvoice/ui/progress_panel.py tests/ui/test_progress_panel.py
git commit -m "feat: add singing skill tree progression"
```

## Final verification

- [ ] Run: `pytest tests/singing/test_exercise_library.py tests/storage/test_singing_repository.py -q`
- [ ] Run: `QT_QPA_PLATFORM=offscreen pytest tests/ui/test_exercise_browser_widget.py tests/ui/test_singing_exercise_panel.py tests/ui/test_progress_panel.py -q`
- [ ] Run: `ruff check src tests`
- [ ] Run: `mypy src`
- [ ] Manual smoke test: start `python run.py`, open the Singing tab, verify the Exercise browser lists all exercise families, filter to Contralto and confirm only contralto variants remain, complete one chromatic-scale exercise, confirm XP/personal best updates, then open Progress and verify the Singing category unlock state refreshes.

Expected final state:
- Exercise browser filters correctly by range/type/difficulty.
- Exercises render as contour-based targets, not staff notation.
- XP and personal bests are tracked independently per range variant.
- Completing entry-tier exercises unlocks intermediate singing skills.

Plan complete and saved to `.planning/phases/23-singing-exercises/23-PLAN.md`. Ready to execute?
