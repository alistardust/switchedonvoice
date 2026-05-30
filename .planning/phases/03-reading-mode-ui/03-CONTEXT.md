# Phase 3: Reading Mode UI - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning after Phase 2 contract lock

<domain>
## Phase Boundary

Phase 3 turns the Phase 2 content library into a readable training surface.
By the end of this phase, the user can open a bundled or imported book,
choose a chapter/passage, read in a large high-contrast view, advance a
word-level cursor manually or automatically, and return later to the same
word offset.

This phase is still primarily a reading/navigation phase. It should lay the
lifecycle hooks that Phase 4 needs for live acoustic feedback, but it does
not yet score words, summarise sessions, or record audio.
</domain>

<decisions>
## Key Implementation Decisions

### Reading panel composition
- **D-03-01:** Create a dedicated `ReadingPanel` in `ui/reading_panel.py`
  rather than growing `MainWindow`. `MainWindow` should own app-wide
  concerns (shared `AudioCapture`, `QTabWidget`, session close ordering),
  while `ReadingPanel` owns content selection, passage state, and bookmark
  persistence.
- **D-03-02:** Split the reading UI into focused widgets:
  `BookSelectorWidget` for book/chapter/passage selection and
  `PassageDisplayWidget` for rendering + highlight state. This keeps word
  cursor logic testable without needing the full tab.

### Bookmark identity and persistence
- **D-03-03:** Treat `reading_progress.bookmark_offset` as a **word index**,
  not a character offset. Every persistence path, restore path, and test
  must use the same unit or bookmarks will drift as punctuation/whitespace
  normalisation changes.
- **D-03-04:** Persist bookmarks by **stable `passage_slug`** whenever the
  user leaves a passage, leaves the Reading tab, or closes the app. This is
  the only identity that survives reordering/import and matches the Phase 2
  slug contract (`alice-wonderland-ch01-p001`).

### Rendering approach
- **D-03-05:** Render the passage from a token model (`list[str]` or richer
  token dataclass) and regenerate rich text with a single highlighted span.
  Do not treat the rendered HTML as source-of-truth state.
- **D-03-06:** Use a widget that already supports word wrap, keyboard focus,
  selection, and accessibility metadata (for example `QTextBrowser` backed
  by escaped HTML spans). This is simpler and more accessible than custom
  painting the text layout from scratch.

### Advancement model
- **D-03-07:** Manual advance and auto-timer advance must share a single
  `advance_word()` state transition. The timer should only call the same
  method; it should not have a separate code path.
- **D-03-08:** Store reading preferences in `Settings`: minimum required is
  passage font size and auto-read words-per-minute. This keeps Phase 3
  independent of transient UI state and lets Phase 4/5 reuse the same
  reading configuration.

### Tab lifecycle groundwork
- **D-03-09:** Add explicit Reading-tab lifecycle hooks (`activate()`,
  `deactivate()`, `persist_bookmark()`) even though Phase 3 itself does not
  yet display live acoustic widgets. Phase 4 can then wire shared
  `AudioCapture` delivery onto the same hooks without reworking tab
  ownership again.
</decisions>

<architecture>
## Architecture Fit

- `ui/main_window.py` currently creates four tabs, owns the shared
  `AudioCapture`, polls `results` at ~30 Hz, and persists session data in
  `closeEvent()`. Phase 3 should extend this rather than introducing a new
  top-level window or another capture object.
- `storage/settings.py` already provides atomic JSON persistence via a
  `Settings` dataclass. Reading font size and auto-WPM should follow the
  same pattern instead of ad-hoc widget-only state.
- Phase 2's `BookRepository` is the data seam between storage and UI. The
  Reading tab should depend on repository methods and stable slugs; it must
  not issue raw SQL from UI code.
- Bookmark restore belongs at panel-load time, not inside the render widget.
  `ReadingPanel` should resolve the selected passage, fetch stored progress,
  then tell `PassageDisplayWidget` which word index to highlight.
</architecture>

<dependencies>
## Required Phase 2 Artifacts

Phase 3 planning assumes Phase 2 delivers all of the following before
implementation starts:

- `src/switchedonvoice/storage/books.py` with a `BookRepository` capable of
  listing books, chapters, and passages, plus reading a passage by a stable
  identifier.
- Bundled books already ingested or ingestible with these slugs:
  `alice-wonderland`, `wizard-of-oz`, `anne-of-green-gables`.
- Stable passage slugs in the format `alice-wonderland-ch01-p001`.
- `reading_progress` rows keyed by `profile_id` + `passage_slug` with at
  least: `bookmark_offset`, `completion_count`, `last_attempted_at`.
- Phase 2 tests proving imported/bundled content order is deterministic,
  because Phase 3 depends on stable `(book, chapter, passage)` navigation.

**Important mismatch to resolve:** the current checked-in Phase 2 planning
documents still describe `reading_progress.passage_id` and integer passage
IDs, while the current phase brief requires `passage_slug`. Phase 3 should
not start until that contract is reconciled across Phase 2 docs and code.
</dependencies>

<pitfalls>
## Critical Pitfalls to Avoid

- **Do not persist character offsets.** The requirement is a word cursor;
  character offsets become unstable once text normalisation or punctuation
  presentation changes.
- **Do not let the display widget own persistence.** UI repaint frequency and
  bookmark writes should stay decoupled so highlight changes do not hammer
  SQLite.
- **Do not re-render in `_tick()` at audio frame rate.** Reading highlight
  updates should occur only when the word index changes; otherwise scroll
  position and selection behaviour will become jittery.
- **Do not lose previous chapter state on navigation.** Navigating away from
  chapter N must write that chapter's bookmark before loading chapter N+1.
- **Do not bind the space-bar shortcut globally without focus rules.** Space
  should advance the word only when the Reading tab owns focus, not when the
  user is inside a combo box or dialog.
- **Do not hardcode inaccessible colours.** WCAG AA contrast (4.5:1 minimum)
  applies to default text, highlighted word styling, button labels, and any
  jump-list selection state.
</pitfalls>

<open_questions>
## Open Questions Before Execution

1. **Phase 2 schema contract:** Is `reading_progress` keyed by `passage_slug`
   (current brief) or by integer `passage_id` (older Phase 2 docs)? This must
   be locked before any UI code is written.
2. **Tab count vs replacement:** Should Reading become a fifth tab, or should
   it replace the current placeholder `Exercises` tab until Phase 11 uses
   that slot again? The brief allows either, but tests need one canonical
   expectation.
3. **Auto-read defaults:** What are the default font size and WPM values?
   Sensible assumptions are 22–28 pt and ~140 WPM, but those should be
   explicit before implementation.
4. **Jump-to-chapter affordance:** Is the “Jump-to-chapter list” a persistent
   combo box in the selector, or a modal quick-jump dialog? The accessible,
   low-complexity default is an always-visible combo box.
</open_questions>

---

*Phase: 03-reading-mode-ui*
*Context gathered: 2026-05-30*
