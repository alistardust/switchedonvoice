---
phase: 03-reading-mode-ui
plan: 01
type: execute
waves: 3
depends_on:
  - Phase 2 complete
files_modified:
  - src/switchedonvoice/ui/main_window.py
  - src/switchedonvoice/ui/settings_panel.py
  - src/switchedonvoice/storage/settings.py
  - src/switchedonvoice/storage/books.py
  - src/switchedonvoice/ui/book_selector_widget.py
  - src/switchedonvoice/ui/passage_display_widget.py
  - src/switchedonvoice/ui/reading_panel.py
  - tests/ui/test_main_window.py
  - tests/ui/test_book_selector_widget.py
  - tests/ui/test_passage_display_widget.py
  - tests/ui/test_reading_panel.py
  - tests/storage/test_settings.py
  - tests/content/test_books_repository.py
autonomous: true
requirements:
  - REQ-R02
  - REQ-NF05
must_haves:
  truths:
    - "MainWindow exposes a Reading tab and wires activate/deactivate hooks exactly once per tab change"
    - "Selecting a book/chapter/passage renders readable wrapped text at the configured font size"
    - "Manual and auto highlight modes both advance the same bookmark_offset word index"
    - "Leaving a passage and reopening it restores the same word index from reading_progress"
    - "Prev/next and jump navigation do not lose the old chapter bookmark"
    - "Rendered text/highlight colours satisfy WCAG AA contrast >= 4.5:1"
  artifacts:
    - path: "src/switchedonvoice/ui/reading_panel.py"
      provides: "Reading tab composition and persistence orchestration"
    - path: "src/switchedonvoice/ui/passage_display_widget.py"
      provides: "Passage rendering and word-cursor state machine"
    - path: "src/switchedonvoice/ui/book_selector_widget.py"
      provides: "Book/chapter/passage selector + navigation controls"
    - path: "tests/ui/test_reading_panel.py"
      provides: "Bookmark round-trip and navigation integration tests"
  key_links:
    - from: "ReadingPanel"
      to: "BookRepository"
      via: "book/chapter/passage queries + bookmark load/save"
    - from: "MainWindow.closeEvent()"
      to: "ReadingPanel.persist_bookmark()"
      via: "pre-session-close hook"
---

<objective>
Build the Reading Mode UI on top of the Phase 2 content library so a user
can choose any passage, read with a word-level cursor, navigate between
chapters, and resume later at the same word.
</objective>

<wave_plan>
## Wave Breakdown

### Wave 1 — foundation (parallel)
1. Extend settings + repository seams for reading preferences and bookmark
   persistence.
2. Build the selector/navigation widget.
3. Build the passage display/highlight widget.

### Wave 2 — composition
4. Compose `ReadingPanel` from the Wave 1 units and wire passage loading,
   restore, save-on-navigation, and keyboard/manual/auto advancement.

### Wave 3 — app integration + verification
5. Add the Reading tab to `MainWindow`, hook tab lifecycle + close-event
   persistence, then finish integration/accessibility tests.
</wave_plan>

<tasks>
## Tasks

### Task 1 (Wave 1): Reading settings and bookmark repository seam

**Description:** Add the minimal persisted state Phase 3 needs before any UI
work: reading font size, auto-WPM, and repository helpers for bookmark load /
save by stable passage identity.

**Files to create/modify**
- Modify: `src/switchedonvoice/storage/settings.py`
- Modify: `src/switchedonvoice/ui/settings_panel.py`
- Modify: `src/switchedonvoice/storage/books.py`
- Test: `tests/storage/test_settings.py`
- Test: `tests/content/test_books_repository.py`

**Acceptance criteria (runnable assertions)**
- `load_settings()` returns defaults for `reading_font_size_pt` and
  `reading_auto_wpm` when keys are absent.
- `save_settings()` round-trips the new values unchanged.
- `BookRepository.get_reading_progress("alice-wonderland-ch01-p001")`
  returns a zero/default bookmark on first read.
- After `save_reading_progress(..., bookmark_offset=17)`, a fresh
  repository instance returns `bookmark_offset == 17` for the same
  `passage_slug`.
- Updating the same passage twice overwrites the existing bookmark rather
  than inserting duplicate progress rows.

**Test strategy**
- `tests/storage/test_settings.py`
  - missing JSON keys fall back safely
  - explicit reading settings persist atomically
- `tests/content/test_books_repository.py`
  - bookmark get/save by `passage_slug`
  - duplicate update semantics
  - per-passage rows remain isolated

**Security / edge-case notes**
- Validate `reading_font_size_pt` and `reading_auto_wpm` to sane positive
  ranges; corrupt JSON must still fall back to defaults.
- Use parameterized SQL only; never interpolate `passage_slug` into SQL.

### Task 2 (Wave 1): Book selector and chapter navigation widget

**Description:** Create a focused widget that owns book/chapter/passage
selection and emits high-level navigation signals to the panel.

**Files to create/modify**
- Create: `src/switchedonvoice/ui/book_selector_widget.py`
- Test: `tests/ui/test_book_selector_widget.py`

**Acceptance criteria (runnable assertions)**
- With a repository seeded with bundled books, the book combo contains 3
  entries ordered consistently.
- Selecting a book repopulates the chapter combo with that book's chapters.
- Selecting a chapter repopulates the passage list for that chapter.
- On the first chapter, Previous is disabled; on the last chapter, Next is
  disabled.
- Activating Previous/Next emits the target chapter/passage selection and
  never skips a chapter.

**Test strategy**
- `tests/ui/test_book_selector_widget.py`
  - combo population
  - prev/next boundary states
  - jump-to-chapter selection signal
  - keyboard activation of navigation controls

**Security / edge-case notes**
- Empty-library state must not crash; show disabled controls and an empty
  message instead.
- All interactive controls need visible labels or accessible names.

### Task 3 (Wave 1): Passage display and word-cursor widget

**Description:** Build the render/highlight engine independently from the
selector so the cursor rules are unit-testable.

**Files to create/modify**
- Create: `src/switchedonvoice/ui/passage_display_widget.py`
- Test: `tests/ui/test_passage_display_widget.py`

**Acceptance criteria (runnable assertions)**
- `set_passage_text()` tokenises and renders the full passage with line
  wrapping.
- `set_bookmark_offset(0)` highlights the first word; `advance_word()` moves
  the highlight to the next token.
- In auto mode, the timer interval is derived from WPM and advancing the
  timer changes the same internal word index as manual mode.
- `current_word_index()` never exceeds the final token index.
- Contrast tests assert all configured foreground/background pairs satisfy
  `contrast_ratio >= 4.5`.

**Test strategy**
- `tests/ui/test_passage_display_widget.py`
  - render smoke test with punctuation and wrapping
  - manual advance via method and keyboard shortcut
  - auto-timer advance at configured WPM
  - bookmark restore to arbitrary word index
  - WCAG AA contrast helper assertion

**Security / edge-case notes**
- HTML-escape all passage text before wrapping highlighted spans.
- Preserve punctuation/whitespace display; do not collapse the visible text
  so that persisted word indices stay aligned with what the user saw.

### Task 4 (Wave 2): ReadingPanel composition and bookmark round-trip

**Description:** Compose selector + display + repository into the real tab,
including load, restore, save-on-navigation, and tab enter/leave hooks.

**Files to create/modify**
- Create: `src/switchedonvoice/ui/reading_panel.py`
- Modify: `src/switchedonvoice/ui/book_selector_widget.py`
- Modify: `src/switchedonvoice/ui/passage_display_widget.py`
- Test: `tests/ui/test_reading_panel.py`

**Acceptance criteria (runnable assertions)**
- Opening the panel with seeded content auto-selects the first available
  passage and renders it.
- If progress for `alice-wonderland-ch01-p001` is stored at offset 24, the
  panel restores offset 24 when that passage is opened.
- Advancing to offset 30, then navigating to a different chapter, writes 30
  for the old passage before rendering the new one.
- Returning to the original chapter restores 30 exactly.
- Calling `persist_bookmark()` twice is idempotent and does not mutate the
  active passage unexpectedly.

**Test strategy**
- `tests/ui/test_reading_panel.py`
  - initial selection + empty-state behaviour
  - bookmark round-trip (save -> fresh panel -> same offset)
  - prev/next and jump navigation persistence
  - space-bar advance only when Reading tab owns focus

**Security / edge-case notes**
- Persist the old passage before replacing in-memory state when navigating.
- Guard against passages with zero tokens; the cursor should stay at 0 and
  the widget should still render text or an explicit empty message.

### Task 5 (Wave 3): MainWindow integration and end-to-end verification

**Description:** Add the Reading tab to the real app, store a persistent tab
reference, connect lifecycle hooks, and prove the flow through Qt tests.

**Files to create/modify**
- Modify: `src/switchedonvoice/ui/main_window.py`
- Modify: `tests/ui/test_main_window.py`
- Modify: `tests/ui/test_reading_panel.py`

**Acceptance criteria (runnable assertions)**
- `MainWindow` constructs with five tabs and one is labeled `Reading`.
- Changing away from the Reading tab calls `reading_panel.deactivate()` once.
- Closing the window calls `reading_panel.persist_bookmark()` before the
  existing session close path runs.
- Reopening a fresh `ReadingPanel` instance against the same DB restores the
  saved bookmark.

**Test strategy**
- `tests/ui/test_main_window.py`
  - tab count / label assertion
  - currentChanged hook wiring
  - close-event save ordering
- `tests/ui/test_reading_panel.py`
  - fresh-load restore after persisted close

**Security / edge-case notes**
- Keep `MainWindow` as the single owner of `AudioCapture`; Phase 3 must not
  instantiate a second capture object for Reading.
- Preserve existing milestone/session close ordering when inserting reading
  persistence into `closeEvent()`.
</tasks>

<verification>
## Verification

```bash
cd /home/alice/git/switchedonvoice
pytest tests/storage/test_settings.py tests/content/test_books_repository.py -q
pytest tests/ui/test_book_selector_widget.py tests/ui/test_passage_display_widget.py tests/ui/test_reading_panel.py tests/ui/test_main_window.py -q
pytest -q
```
</verification>

<completion_criteria>
## Completion Criteria

Phase 3 is done only when all of the following are true:

- A Reading tab exists in the real app and can load bundled Phase 2 content.
- The passage text is readable, wrapped, keyboard reachable, and WCAG AA
  contrast compliant.
- The word cursor advances manually and automatically using one shared state
  machine.
- Bookmark persistence survives tab switches, chapter changes, app close,
  and fresh app reopen.
- The full test suite still passes.
</completion_criteria>
