# Phase 2: Content Library & Book Ingestion - Context

**Gathered:** 2026-05-29
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase gives the app books to work with. By the end, three public domain
books (Alice's Adventures in Wonderland, The Wonderful Wizard of Oz, Anne of
Green Gables) are available as browsable content: chapters, passages (~150
words each), and passage metadata. Reading progress is tracked per passage.
The app uses its own `.sov-book` JSON format. A CLI converter tool handles
`.txt` → `.sov-book` conversion for future content additions.

Phase 2 is purely data infrastructure — no UI, no real-time feedback.
That comes in Phases 3 and 4.

</domain>

<decisions>
## Implementation Decisions

### Content File Format
- **D-01:** The app's content format is `.sov-book` — a JSON file containing
  book metadata, chapters, passages, and per-passage annotations. Human-readable
  and straightforward to extend.
- **D-02:** Bundled books ship **pre-built** as `.sov-book` files in the package
  assets — no parsing overhead at first launch.
- **D-03:** The folder-watcher monitors `~/.switchedonvoice/books/` for new
  `.sov-book` files (not raw `.txt`). Users drop pre-built book files, not raw text.

### `.sov-book` Schema (agent's discretion on exact fields, but must include)
- Book-level: `title`, `author`, `language`, `source` (e.g. Project Gutenberg),
  `licence` (public domain note), `version`
- Chapter-level: `number`, `title`, `passages[]`
- Passage-level: `id`, `text`, `word_count`, `difficulty` (easy/medium/hard),
  `phonemic_density` (optional float — fraction of phonemically rich vowels),
  `recommended_f0_target` (optional float Hz — editorial annotation for Phase 4 scoring)

### Passage Splitting
- **D-04:** Sentence-aware splitting at ~150 words — never cut mid-sentence.
  Passages at chapter boundaries may be shorter than 150 words (acceptable).
  Very short chapters (< 100 words) become a single passage.

### Book Parser / Converter Tool
- **D-05:** A CLI script (`python -m switchedonvoice.tools.import_book`) converts
  a Project Gutenberg `.txt` file to `.sov-book` format. This tool is used to
  produce the bundled assets (not run by end users at runtime).
- **D-06:** The parser strips PG boilerplate (before "*** START OF" and after
  "*** END OF" markers), splits into chapters by detecting chapter headings
  (Roman numerals, "Chapter N", "CHAPTER N"), then splits chapters into passages.

### Repository Pattern
- **D-07 (agent's discretion):** Use a `BookRepository` class (not module-level
  functions). Phase 2 has 5+ query methods; a class is cleaner and more
  extensible for instructor mode. Follow the same `db_path` injection pattern
  as `sessions.py` — pass `db_path` to `__init__`, not to each method.

### Database Layout
- **D-08 (agent's discretion):** Extend the existing sessions database
  (`~/.switchedonvoice/sessions.db` or equivalent). Add a new schema migration
  block (`version < 2`) in `db.py`. Keeps all app data in one file; simpler
  backup and deletion for users. New tables: `books`, `chapters`, `passages`,
  `reading_progress`.
- **D-09:** The `reading_progress` table must include `profile_id` (NULL for
  now — Phase 15 will add multi-profile). This FK placeholder avoids a painful
  migration later.

### Passage Metadata for Phase 4 Scoring
- **D-10:** Store `difficulty`, `phonemic_density`, and `recommended_f0_target`
  in the `passages` table so Phase 4 (acoustic overlay) can score against
  passage-level targets rather than only user baselines. These fields are
  nullable — not every passage requires editorial annotation.

### Deferred — Content Authoring UI
- A full content creation/authoring UI — where instructors or users write
  original passages, preview them, QA — is deferred to Phase 16 (Instructor
  Mode: curriculum authoring) or a future content studio feature.
  Not in scope for Phase 2.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Requirements
- `.planning/REQUIREMENTS.md` — REQ-R01 (content library), REQ-R05 (progress
  persistence schema); reading the full REQ-R01 and REQ-R05 sections is mandatory

### Roadmap & Phase Scope
- `.planning/ROADMAP.md` §Phase 2 — Canonical task list and success criteria
  for this phase; tasks 1–7 define all deliverables

### Existing Storage Layer (must read before writing new migrations)
- `src/switchedonvoice/storage/db.py` — Migration pattern (`_CURRENT_SCHEMA_VERSION`,
  `_migrate()`, `PRAGMA user_version`); new tables MUST follow this pattern
- `src/switchedonvoice/storage/sessions.py` — Repository function style and
  `get_connection()` usage; `BookRepository` must be consistent

### Project Constraints
- `.planning/PROJECT.md` §Constraints — No GPL deps; all data local;
  `~/.switchedonvoice/` as data root; aubio excluded permanently

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/switchedonvoice/storage/db.py` — `init_db()`, `get_connection()`, and
  the `_migrate()` versioned migration block. New `books`/`chapters`/`passages`/
  `reading_progress` tables should be added as `version < 2` in `_migrate()`,
  bumping `_CURRENT_SCHEMA_VERSION` to 2.
- `src/switchedonvoice/storage/sessions.py` — `get_connection()` usage pattern,
  `@dataclass` models, error handling conventions (`ValueError` on missing rows).
- `pyproject.toml` `[tool.pytest.ini_options]` — test configuration; new tests
  go in `tests/content/` following the existing `tests/storage/` layout.

### Established Patterns
- Data root: `Path.home() / ".switchedonvoice"` — used in `settings.py` and
  presumably `db.py`. Book files go in `~/.switchedonvoice/books/`.
- `@dataclass` for data models (see `Settings`, `SessionSummary`).
- `ValueError` for missing/invalid rows; no silent failures.
- WAL mode + foreign keys enabled on every connection (in `get_connection()`).
- Package assets: `src/switchedonvoice/` — bundled `.sov-book` files go in
  `src/switchedonvoice/content/books/`.

### Integration Points for Later Phases
- Phase 3 (Reading UI): will call `BookRepository.list_books()`,
  `get_chapters()`, `get_passages()`, `get_passage()`
- Phase 4 (Acoustic Overlay): will read `passage.recommended_f0_target` and
  `passage.difficulty` for per-passage scoring targets
- Phase 15 (Multi-profile): `reading_progress.profile_id` FK will be activated

</code_context>

<specifics>
## Specific References

- **Alice's Adventures in Wonderland** — Project Gutenberg #11
  (https://www.gutenberg.org/ebooks/11). Preferred for its thematic resonance
  with trans audiences (transformation, identity). Primary bundled book.
- **The Wonderful Wizard of Oz** — Project Gutenberg #55.
- **Anne of Green Gables** — Project Gutenberg #45.
- Rainbow Passage (gender-neutralised) is already in `onboarding/wizard.py` as
  `_RAINBOW_PASSAGE` — not a book, but relevant context for passage length/format.
</specifics>

<deferred>
## Deferred Ideas

- **Content authoring UI** — Full tool for instructors/users to write original
  content, preview it, QA it, add phonemic annotations. Deferred to Phase 16
  (Instructor Mode) or a standalone content studio.
- **Model audio per passage** — Attach a reference TTS or human recording for
  "listen and repeat" mode. Deferred to a later phase.
- **Folder-watcher for .txt files** — User dropping raw Gutenberg `.txt` into
  the books folder and having it auto-convert. Deferred; Phase 2 watches for
  `.sov-book` drops only.
</deferred>

---

*Phase: 02-content-library*
*Context gathered: 2026-05-29 via /gsd-discuss-phase 2*
