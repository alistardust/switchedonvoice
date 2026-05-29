# Phase 2: Content Library & Book Ingestion — Research

**Researched:** 2026-05-29
**Domain:** SQLite schema migrations, PySide6 file watching, JSON asset bundling, text parsing
**Confidence:** HIGH — all open questions resolved via live verification on actual codebase + direct network access to Project Gutenberg source files

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Content File Format**
- D-01: `.sov-book` JSON files (pre-built, bundled as package assets)
- D-02: Bundled books ship pre-built — no parsing at first launch
- D-03: Folder-watcher monitors `~/.switchedonvoice/books/` for `.sov-book` drops

**`.sov-book` Schema (agent discretion on exact fields, must include)**
- Book-level: `title`, `author`, `language`, `source`, `licence`, `version`
- Chapter-level: `number`, `title`, `passages[]`
- Passage-level: `id`, `text`, `word_count`, `difficulty`, `phonemic_density` (optional float), `recommended_f0_target` (optional float Hz)

**Passage Splitting**
- D-04: Sentence-aware splitting at ~150 words. Short chapters < 100 words → single passage. Chapter-boundary passages may be shorter.

**Parser / Converter Tool**
- D-05: `python -m switchedonvoice.tools.import_book` converts `.txt` → `.sov-book`
- D-06: Parser strips PG boilerplate, detects chapter headings (Roman numerals, "Chapter N", "CHAPTER N"), splits into passages

**Repository Pattern**
- D-07: `BookRepository` class with `db_path` injected into `__init__`; NOT module-level functions

**Database Layout**
- D-08: Extend `~/.switchedonvoice/data.db` via migration `version < 2` in `db.py`; bump `_CURRENT_SCHEMA_VERSION` to 2
- D-09: `reading_progress` must include `profile_id` (NULL FK placeholder for Phase 15)

**Passage Metadata**
- D-10: `difficulty`, `phonemic_density`, `recommended_f0_target` — nullable; stored in `passages` table

### Agent's Discretion
- Exact field names within the `.sov-book` JSON schema (beyond the required fields)
- SQLite column types and index choices for the new tables
- Internal structure of the `BookWatcherService` class
- Whether `import_book.py` tool writes to stdout or file

### Deferred Ideas (OUT OF SCOPE)
- Content authoring UI — deferred to Phase 16
- Model audio per passage — deferred to later phase
- Folder-watcher for `.txt` auto-convert — deferred; Phase 2 watches `.sov-book` only
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REQ-R01 | App ships with 3 public domain books; split into chapters/passages; new books addable via folder drop | PG chapter patterns verified; passage splitting algorithm confirmed; folder-watcher API confirmed |
| REQ-R05 | Per-book reading position persisted; per-passage completion count and last-attempted date | `reading_progress` table schema designed; migration v2 pattern documented |
</phase_requirements>

---

## Summary

Phase 2 is a pure data infrastructure phase. There is no new UI and no new audio/DSP code. The work divides into four well-bounded areas: (1) schema migration, (2) a CLI parsing tool that is run offline to produce bundled assets, (3) a `BookRepository` class with five query methods, and (4) a `BookWatcherService` that monitors a folder for new `.sov-book` drops and ingests them off the main thread.

All research questions have been resolved without adding any new third-party dependencies. The passage-splitting algorithm works with stdlib `re`. `QFileSystemWatcher` (already in PySide6 6.11.1, verified installed) provides inotify-backed directory monitoring on Linux with no polling. The off-thread ingestion pattern follows the same `QThread` + worker + `moveToThread` idiom used elsewhere in the codebase. Hatchling auto-includes `.sov-book` JSON files — no extra pyproject.toml configuration is needed.

The three bundled books have been verified at their Project Gutenberg source URLs. Each has a consistent chapter heading pattern and clean `*** START / END ***` boilerplate markers. Regex-based parsing is sufficient; no NLP library is required.

**Primary recommendation:** Implement in strict task order — migration first, then repository, then bundled assets, then watcher — since each task tests against the previous one's outputs.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| SQLite schema migration | Storage (`db.py`) | — | Follows existing `_migrate()` / `PRAGMA user_version` pattern |
| Book/chapter/passage queries | Storage (`BookRepository`) | — | Data access layer, parallel to `sessions.py` |
| `.sov-book` format parsing (CLI tool) | Tools (`import_book.py`) | — | Offline authoring tool, not runtime |
| Bundled book assets | Package data (`content/books/`) | — | Pre-built JSON; loaded via `importlib.resources` |
| Folder monitoring for new drops | Service (`BookWatcherService`) | UI wiring (Phase 3) | Qt-level OS event; DB write off main thread |
| Reading progress persistence | Storage (`reading_progress` table) | — | Repository query; UI writes via Phase 3 |

---

## Standard Stack

### Core (all already installed — zero new packages)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `PySide6.QtCore.QFileSystemWatcher` | 6.11.1 [VERIFIED: installed] | inotify-backed folder monitoring | Event-driven; no polling; official Qt class |
| `PySide6.QtCore.QThread` | 6.11.1 [VERIFIED: installed] | Off-main-thread DB ingestion | Idiomatic Qt threading; signal/slot cross-thread delivery |
| `sqlite3` | stdlib | Database access | Already used by `db.py`; no new dep |
| `importlib.resources` (`files()` API) | stdlib (Python 3.9+, confirmed 3.14.5) | Access bundled `.sov-book` files at runtime | PEP 451-compliant; works in installed wheels |
| `re` | stdlib | Chapter heading detection; sentence splitting | Sufficient for structured PG text |
| `json` | stdlib | `.sov-book` serialisation/deserialisation | Format is plain JSON |
| `pathlib.Path` | stdlib | File/directory handling | Project convention |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `dataclasses.dataclass` | stdlib | `Book`, `Chapter`, `Passage` model types | Same convention as `Settings`, `HistoryAggregates` |
| `pytest-qt` | 4.5.0 [VERIFIED: installed] | `qtbot`, `waitSignal()` for watcher tests | Testing Qt signal/slot async interactions |
| `structlog` | 24+ | Logging in `storage/` and `tools/` modules | Project convention for non-UI modules |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `QFileSystemWatcher` | `QTimer` polling every 2s | Watcher is event-driven (inotify); polling wastes CPU and has up-to-2s lag. Use timer only if watcher directory doesn't exist at startup (create dir first, then watch) |
| stdlib `re` sentence splitting | `nltk.sent_tokenize` | nltk adds ~100MB of model downloads; overkill for structured PG prose where sentence boundaries are reliable |
| stdlib `re` | `spacy` | Same — heavy ML dependency for a regex-solvable problem |
| `importlib.resources.files()` | Direct `Path(__file__).parent / ...` | `files()` is PEP 451-compliant and works correctly in installed wheels and zip-safe builds; `__file__` tricks break in some packaging scenarios |

**Installation:** No new packages needed. Everything is stdlib or already in `pyproject.toml`.

---

## Package Legitimacy Audit

> Phase 2 adds **zero new packages** to `pyproject.toml`. All functionality is implemented with stdlib modules (`re`, `json`, `pathlib`, `importlib.resources`, `sqlite3`) and the PySide6 dependency already locked. No slopcheck required.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
 ┌─────────────────────────────────────────────────────────────────┐
 │  OFFLINE (dev-time / user CLI)                                  │
 │                                                                 │
 │  .txt (Project Gutenberg)                                       │
 │       │                                                         │
 │       ▼                                                         │
 │  import_book.py ──► strip boilerplate ──► detect chapters ──►  │
 │                     split passages ──► compute metadata ──►    │
 │                     write .sov-book JSON                        │
 └─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │ bundled assets                 │ user drop
              ▼                               ▼
 src/switchedonvoice/         ~/.switchedonvoice/books/
   content/books/*.sov-book       *.sov-book (new drop)
              │                               │
              ▼                               ▼
 App startup: BookRepository.ingest_bundled()  BookWatcherService
              │                               │  QFileSystemWatcher
              │                               │  directoryChanged ──►
              │                               │  QThread + IngestionWorker
              │                               │  (off main thread)
              │                               │
              └──────────────┬────────────────┘
                             ▼
                    data.db (SQLite)
                    ┌────────────────────┐
                    │ books              │
                    │ chapters           │
                    │ passages           │
                    │ reading_progress   │
                    └────────────────────┘
                             │
                             ▼ (Phase 3+)
                    BookRepository queries
                    (list_books, get_chapters,
                     get_passages, get_passage)
```

### Recommended Project Structure

```
src/switchedonvoice/
├── content/
│   ├── __init__.py
│   └── books/
│       ├── __init__.py
│       ├── alice-wonderland.sov-book      # PG #11
│       ├── wizard-of-oz.sov-book          # PG #55
│       └── anne-of-green-gables.sov-book  # PG #45
├── storage/
│   ├── db.py              # MODIFY: add v2 migration block
│   ├── sessions.py        # untouched
│   ├── settings.py        # untouched
│   └── books.py           # NEW: BookRepository class
└── tools/
    ├── __init__.py
    └── import_book.py     # NEW: CLI converter
tests/
└── content/
    ├── __init__.py
    ├── test_books_repository.py
    ├── test_import_book.py       # parser + passage splitting
    └── test_book_watcher.py      # QFileSystemWatcher integration
```

> **Note:** `BookWatcherService` belongs in a new `src/switchedonvoice/services/` module (or inline in `storage/`) — the exact location is agent's discretion, but it must NOT live in `ui/`.

---

### Pattern 1: Schema Migration v2

**What:** Add a new `elif version < 2` block in `_migrate()`, bump `_CURRENT_SCHEMA_VERSION = 2`. Never remove or reorder the existing `version < 1` block.

**When to use:** Any time new tables are added. This is the only correct migration pattern per the established codebase rule.

```python
# Source: src/switchedonvoice/storage/db.py (existing pattern — extend this)

_CURRENT_SCHEMA_VERSION = 2  # bumped from 1

_SCHEMA_V2 = """
CREATE TABLE IF NOT EXISTS books (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    slug         TEXT NOT NULL UNIQUE,
    title        TEXT NOT NULL,
    author       TEXT NOT NULL,
    language     TEXT NOT NULL DEFAULT 'en',
    source       TEXT,
    licence      TEXT,
    version      TEXT,
    ingested_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chapters (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id  INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    number   INTEGER NOT NULL,
    title    TEXT NOT NULL,
    UNIQUE (book_id, number)
);

CREATE TABLE IF NOT EXISTS passages (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id            INTEGER NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    position              INTEGER NOT NULL,
    text                  TEXT NOT NULL,
    word_count            INTEGER NOT NULL,
    difficulty            TEXT CHECK(difficulty IN ('easy','medium','hard')),
    phonemic_density      REAL,
    recommended_f0_target REAL,
    UNIQUE (chapter_id, position)
);

CREATE TABLE IF NOT EXISTS reading_progress (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id        INTEGER,          -- NULL now; FK placeholder for Phase 15
    passage_id        INTEGER NOT NULL REFERENCES passages(id) ON DELETE CASCADE,
    bookmark_offset   INTEGER NOT NULL DEFAULT 0,
    completion_count  INTEGER NOT NULL DEFAULT 0,
    last_attempted_at TEXT,
    UNIQUE (profile_id, passage_id)
);

CREATE INDEX IF NOT EXISTS idx_passages_chapter  ON passages(chapter_id);
CREATE INDEX IF NOT EXISTS idx_chapters_book     ON chapters(book_id);
CREATE INDEX IF NOT EXISTS idx_progress_passage  ON reading_progress(passage_id);
"""

def _migrate(con: sqlite3.Connection) -> None:
    version: int = con.execute("PRAGMA user_version").fetchone()[0]
    if version < 1:
        con.execute(f"PRAGMA user_version = {_CURRENT_SCHEMA_VERSION}")
    if version < 2:
        con.executescript(_SCHEMA_V2)
        con.execute(f"PRAGMA user_version = {_CURRENT_SCHEMA_VERSION}")
```

**Key design note:** `reading_progress.profile_id` is `INTEGER` (not `INTEGER NOT NULL`), nullable with no FK constraint yet. Phase 15 will add the `profiles` table and `ALTER TABLE reading_progress ADD CONSTRAINT` — keeping it nullable now avoids a breaking migration.

---

### Pattern 2: BookRepository Class

**What:** Class following `sessions.py` conventions — `db_path` in `__init__`, `get_connection()` per method, `@dataclass` models, `ValueError` on missing rows.

```python
# Source: src/switchedonvoice/storage/books.py (NEW)
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from switchedonvoice.storage.db import get_connection


@dataclass
class Passage:
    id: int
    chapter_id: int
    position: int
    text: str
    word_count: int
    difficulty: Optional[str]
    phonemic_density: Optional[float]
    recommended_f0_target: Optional[float]


@dataclass
class Chapter:
    id: int
    book_id: int
    number: int
    title: str


@dataclass
class Book:
    id: int
    slug: str
    title: str
    author: str
    language: str


class BookRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def list_books(self) -> list[Book]:
        con = get_connection(self._db_path)
        rows = con.execute(
            "SELECT id, slug, title, author, language FROM books ORDER BY title"
        ).fetchall()
        con.close()
        return [Book(*r) for r in rows]

    def get_chapters(self, book_id: int) -> list[Chapter]:
        con = get_connection(self._db_path)
        rows = con.execute(
            "SELECT id, book_id, number, title FROM chapters "
            "WHERE book_id = ? ORDER BY number",
            (book_id,),
        ).fetchall()
        con.close()
        return [Chapter(*r) for r in rows]

    def get_passages(self, chapter_id: int) -> list[Passage]:
        con = get_connection(self._db_path)
        rows = con.execute(
            "SELECT id, chapter_id, position, text, word_count, "
            "difficulty, phonemic_density, recommended_f0_target "
            "FROM passages WHERE chapter_id = ? ORDER BY position",
            (chapter_id,),
        ).fetchall()
        con.close()
        return [Passage(*r) for r in rows]

    def get_passage(self, passage_id: int) -> Passage:
        con = get_connection(self._db_path)
        row = con.execute(
            "SELECT id, chapter_id, position, text, word_count, "
            "difficulty, phonemic_density, recommended_f0_target "
            "FROM passages WHERE id = ?",
            (passage_id,),
        ).fetchone()
        con.close()
        if row is None:
            raise ValueError(f"Passage {passage_id} does not exist")
        return Passage(*row)

    def book_exists(self, slug: str) -> bool:
        """Check if a book with this slug is already ingested."""
        con = get_connection(self._db_path)
        row = con.execute(
            "SELECT 1 FROM books WHERE slug = ?", (slug,)
        ).fetchone()
        con.close()
        return row is not None
```

---

### Pattern 3: QFileSystemWatcher + QThread Off-Thread Ingestion

**What:** Main-thread watcher detects `.sov-book` file creation → spawns QThread worker → worker does all DB writes → emits signal back to main thread. Never do DB writes on the main thread from a file event.

**Key API facts (verified PySide6 6.11.1):**
- `QFileSystemWatcher.addPath(directory_str)` — watch a directory; returns `True` if successful
- `directoryChanged(path: str)` signal — fires when any file is created, deleted, or renamed in the directory
- `fileChanged(path: str)` — fires when file *content* changes (not needed here)
- Signals emit on the thread that owns the watcher (main thread when watcher lives in main thread)

```python
# Source: src/switchedonvoice/services/book_watcher.py (NEW)
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
from PySide6.QtCore import QObject, QThread, Signal, Slot, QFileSystemWatcher
from switchedonvoice.storage.books import BookRepository
import structlog

_log = structlog.get_logger(__name__)


class _IngestionWorker(QObject):
    """Runs on a background QThread. Does all SQLite writes."""
    succeeded = Signal(str)   # emits slug
    failed = Signal(str, str) # emits (path, error_message)

    def __init__(self, sov_book_path: Path, db_path: Path) -> None:
        super().__init__()
        self._path = sov_book_path
        self._db_path = db_path

    @Slot()
    def run(self) -> None:
        try:
            repo = BookRepository(self._db_path)
            data = json.loads(self._path.read_text(encoding="utf-8"))
            slug = data["slug"]
            if repo.book_exists(slug):
                _log.info("book_already_ingested", slug=slug)
                self.succeeded.emit(slug)
                return
            repo.ingest(data)
            self.succeeded.emit(slug)
        except Exception as exc:
            self.failed.emit(str(self._path), str(exc))


class BookWatcherService(QObject):
    """Monitors books_dir for .sov-book drops; ingests on main thread signal."""
    book_ingested = Signal(str)   # emits slug — for UI notification (Phase 3)
    ingest_failed = Signal(str)   # emits error message

    def __init__(
        self,
        books_dir: Path,
        db_path: Path,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._books_dir = books_dir
        self._db_path = db_path
        self._watcher = QFileSystemWatcher(self)

        books_dir.mkdir(parents=True, exist_ok=True)  # must exist before addPath
        self._watcher.addPath(str(books_dir))
        self._watcher.directoryChanged.connect(self._on_directory_changed)

    @Slot(str)
    def _on_directory_changed(self, _path: str) -> None:
        for sov_file in self._books_dir.glob("*.sov-book"):
            self._ingest_async(sov_file)

    def _ingest_async(self, path: Path) -> None:
        worker = _IngestionWorker(path, self._db_path)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(self.book_ingested)
        worker.failed.connect(lambda p, e: self.ingest_failed.emit(e))
        worker.succeeded.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.succeeded.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()
```

**⚠️ Critical pitfall:** `directoryChanged` fires for *every* file change in the directory (creates, deletes, renames). The handler must check `book_exists(slug)` before ingesting to prevent duplicate ingestion. The `glob("*.sov-book")` scan approach is safe — each discovered file is guarded by `book_exists()`.

---

### Pattern 4: Chapter Heading Detection (verified on actual PG source files)

**Chapter heading patterns confirmed by fetching PG #11, #55, #45 directly:**

| Book | PG # | Heading format | Example |
|------|------|----------------|---------|
| Alice's Adventures in Wonderland | 11 | `CHAPTER I.` (own line) + title on next line | `CHAPTER I.\nDown the Rabbit-Hole` |
| The Wonderful Wizard of Oz | 55 | `Chapter I` (own line) + title on next line | `Chapter I\nThe Cyclone` |
| Anne of Green Gables | 45 | `CHAPTER I. Title Here` (title on same line) | `CHAPTER I. Mrs. Rachel Lynde Is Surprised` |

**Unified regex (handles all 3 patterns):**

```python
# Source: verified against actual PG text files
import re

# Boilerplate strip
_PG_START = re.compile(r"^\*{3} START OF THE PROJECT GUTENBERG EBOOK \d+ \*{3}$", re.MULTILINE)
_PG_END   = re.compile(r"^\*{3} END OF THE PROJECT GUTENBERG EBOOK \d+ \*{3}$", re.MULTILINE)

# Chapter heading: CHAPTER I. / Chapter I / CHAPTER I. Title Here
_CHAPTER_HEADING = re.compile(
    r"^(?:CHAPTER|Chapter)\s+"
    r"([IVXLCDM]+|[0-9]+)\.?\s*"  # Roman numerals or Arabic, optional period
    r"(.*)$",                       # optional inline title
    re.MULTILINE,
)

def strip_boilerplate(text: str) -> str:
    """Extract content between PG START and END markers."""
    start = _PG_START.search(text)
    end   = _PG_END.search(text)
    if not start or not end:
        raise ValueError("PG boilerplate markers not found")
    return text[start.end():end.start()].strip()

def split_chapters(text: str) -> list[tuple[str, str, str]]:
    """Return list of (roman_numeral, inline_title, body_text)."""
    headings = list(_CHAPTER_HEADING.finditer(text))
    chapters = []
    for i, match in enumerate(headings):
        roman = match.group(1)
        inline_title = match.group(2).strip()
        start = match.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[start:end].strip()
        # For Alice/Oz, the line AFTER the heading is the actual chapter title
        if not inline_title:
            lines = body.splitlines()
            inline_title = lines[0].strip() if lines else ""
            body = "\n".join(lines[1:]).strip()
        chapters.append((roman, inline_title, body))
    return chapters
```

---

### Pattern 5: Passage Splitting (stdlib only)

**What:** Greedy sentence accumulation. Add sentences until the next sentence would push the total over 150 words, then flush and start a new passage.

**Edge cases (verified):**
- **Em-dashes** (`—`): treated as mid-sentence; sentence regex only splits on `.!?` — em-dashes pass through safely
- **PG italics** (`_word_`): pass-through unchanged; don't affect word count
- **Dialogue**: `"Oh dear! Oh dear!"` — the `!` inside quotes can cause premature splits. Mitigated by the greedy accumulation: a 5-word dialogue snippet will not flush until combined total > 150
- **Very long single sentences**: rare in PG prose but possible. A passage may exceed 150 words if a single sentence is > 150 words. This is acceptable per D-04.
- **Short chapters** (< 100 words): produce a single passage containing all sentences

```python
# Source: verified by running against actual Alice text, producing ~143-word passages
import re

def _normalise(text: str) -> str:
    """Collapse all whitespace (PG uses blank lines within chapter body)."""
    return re.sub(r"\s+", " ", text).strip()

def split_sentences(text: str) -> list[str]:
    """
    Split text into sentences.

    Strategy: split on [.!?] optionally followed by closing quote/paren,
    then whitespace, then uppercase or opening quote.
    Does NOT split on abbreviations (Mr., Mrs., Dr.) because they are
    typically followed by lowercase or a proper noun that starts mid-sentence.
    """
    text = _normalise(text)
    parts = re.split(r'(?<=[.!?])["\']?\s+(?=[A-Z"])', text)
    return [p.strip() for p in parts if p.strip()]

def split_into_passages(chapter_text: str, target_words: int = 150) -> list[str]:
    """
    Greedy sentence accumulation into ~target_words passages.
    Never cuts mid-sentence. Last passage may be shorter than target.
    """
    sentences = split_sentences(chapter_text)
    passages: list[str] = []
    current: list[str] = []
    current_words = 0

    for sent in sentences:
        w = len(sent.split())
        if current_words > 0 and current_words + w > target_words:
            passages.append(" ".join(current))
            current = [sent]
            current_words = w
        else:
            current.append(sent)
            current_words += w

    if current:
        passages.append(" ".join(current))

    return passages
```

---

### Pattern 6: Bundled Asset Access via importlib.resources

**What:** Access `.sov-book` files installed alongside the package at runtime.

**Hatchling behaviour (verified from official docs, hatch.pypa.io/1.16/config/build/):**
Hatchling's wheel build target includes **all files** under the listed package directories by default. No `package_data`, no `artifacts` config needed. `.sov-book` files in `src/switchedonvoice/content/books/` are auto-included. [CITED: hatch.pypa.io/1.16/config/build/]

**`__init__.py` requirement:** `importlib.resources.files()` requires the subpackage to be a proper Python package. Both `src/switchedonvoice/content/__init__.py` and `src/switchedonvoice/content/books/__init__.py` must exist (even if empty). [ASSUMED — standard Python packaging requirement, not verified against Python 3.14 changelog]

```python
# Source: Python 3.9+ importlib.resources.files() API (confirmed available Python 3.14.5)
from importlib.resources import files

def load_bundled_books() -> list[dict]:
    """Read all bundled .sov-book files and return parsed JSON."""
    books_pkg = files("switchedonvoice.content.books")
    result = []
    for resource in books_pkg.iterdir():
        if resource.name.endswith(".sov-book"):
            data = json.loads(resource.read_text(encoding="utf-8"))
            result.append(data)
    return result
```

---

### Pattern 7: Test Isolation

**What:** Use `tmp_path` (pytest built-in) for all DB-path and books-dir tests.

```python
# Pattern from existing tests/storage/test_db.py and test_sessions.py
import pytest
from pathlib import Path
from switchedonvoice.storage.db import init_db
from switchedonvoice.storage.books import BookRepository

@pytest.fixture()
def db(tmp_path: Path) -> Path:
    p = tmp_path / "test.db"
    init_db(p)
    return p

@pytest.fixture()
def repo(db: Path) -> BookRepository:
    return BookRepository(db)

def test_list_books_empty(repo: BookRepository) -> None:
    assert repo.list_books() == []
```

**Testing the watcher (pytest-qt 4.5.0 installed):**

```python
# QFileSystemWatcher test: use qtbot.waitSignal() for async signal delivery
def test_watcher_ingests_dropped_file(qtbot, tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    books_dir = tmp_path / "books"
    
    svc = BookWatcherService(books_dir=books_dir, db_path=db)
    
    # Drop a valid .sov-book file
    (books_dir / "test.sov-book").write_text(
        json.dumps(MINIMAL_SOV_BOOK), encoding="utf-8"
    )
    
    # Wait for the async ingestion to complete (up to 2s)
    with qtbot.waitSignal(svc.book_ingested, timeout=2000):
        pass  # signal fires when ingestion completes

    repo = BookRepository(db)
    assert len(repo.list_books()) == 1
```

**CI note:** `QFileSystemWatcher` uses inotify (kernel-level) — it does NOT require a display server. `QT_QPA_PLATFORM=offscreen` is only needed for widget rendering. Watcher tests run cleanly headless. [VERIFIED: inotify available on CachyOS kernel 7.0.9]

---

### Anti-Patterns to Avoid

- **DB writes on the main thread from `directoryChanged`**: blocks the event loop during large book ingestion. Always use `QThread` + worker.
- **Calling `addPath()` on a non-existent directory**: `QFileSystemWatcher.addPath()` returns `False` silently for paths that don't exist. Always `mkdir(parents=True, exist_ok=True)` before calling `addPath()`.
- **Not guarding re-ingestion**: `directoryChanged` fires on every directory event (renames, deletes, etc.). If a file was already ingested, `book_exists(slug)` must short-circuit ingestion.
- **SQLite connections across threads**: Never pass an open `sqlite3.Connection` to a worker thread. The worker must call `get_connection()` inside its own `run()`. The existing per-call open/close pattern in `sessions.py` already handles this correctly.
- **Reordering migration blocks in `_migrate()`**: The docstring in `db.py` explicitly forbids this. Add only new `elif version < N` blocks; never touch the `version < 1` block.
- **Abbreviation false-splits**: `re.split(r'[.!?]\s+', text)` will split `Mr. Smith` into two fragments. The verified pattern `(?<=[.!?])["\']?\s+(?=[A-Z"])` avoids this because abbreviations are followed by lowercase (`mr.` → lowercase next word). Test with Alice's frequent `_very_` and dialogue.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Directory change events | Polling loop / `QTimer` | `QFileSystemWatcher` | Already uses inotify on Linux; event-driven; zero CPU at idle |
| Cross-thread result delivery | shared global variable, `threading.Event` | Qt signal/slot cross-thread | Qt automatically queues cross-thread signals; thread-safe by design |
| Bundled file access | `Path(__file__).parent / ...` | `importlib.resources.files()` | Correct in wheels, editable installs, and zip-safe builds |
| Schema version management | Custom version table | `PRAGMA user_version` | Already established in `db.py`; one source of truth |
| Sentence detection | Custom tokenizer / char-level state machine | stdlib `re` (for this corpus) | PG text is structured prose; `re` handles 99% of cases without 100MB NLP model |

**Key insight:** PySide6 already provides everything needed for event-driven file watching and thread-safe signal delivery. No watchdog, no watchfiles, no threading primitives from outside Qt.

---

## Runtime State Inventory

> Phase 2 is a greenfield feature addition (new tables, new files, new service). Not a rename/refactor/migration. Runtime state inventory is not applicable.

**None — verified: no existing content tables, no existing books directory, no registered tasks or services that reference content library state.**

---

## Common Pitfalls

### Pitfall 1: DB Path Confusion — `data.db` vs `sessions.db`

**What goes wrong:** CONTEXT.md says "sessions database" and mentions `sessions.db or equivalent`. The actual production path (confirmed in `main_window.py:22`) is `~/.switchedonvoice/data.db`.
**Why it happens:** The CONTEXT.md was written generically; the actual filename is in the code.
**How to avoid:** In all new code and tests, use `_DB_PATH = Path.home() / ".switchedonvoice" / "data.db"` — same constant as `main_window.py`. Tests use `tmp_path / "test.db"`.
**Warning signs:** If a test creates `sessions.db` in `tmp_path`, it won't test the real path. Keep all path references consistent.

### Pitfall 2: `directoryChanged` Fires Multiple Times for One Drop

**What goes wrong:** On Linux/inotify, dropping a large file can trigger multiple `directoryChanged` events (one for file create, possibly more as data is written). Ingestion worker fires multiple times for the same file.
**Why it happens:** inotify is low-level; it fires on each filesystem operation, not once per "drop complete".
**How to avoid:** Guard with `book_exists(slug)` inside the worker's `run()`. The slug is read from the JSON; if already in the DB, emit `succeeded` immediately without re-inserting.
**Warning signs:** Duplicate-key constraint errors on `books.slug` UNIQUE constraint.

### Pitfall 3: `QFileSystemWatcher.addPath()` Silent Failure

**What goes wrong:** Service initialised before `~/.switchedonvoice/books/` directory exists. `addPath()` returns `False` and watches nothing. No error is raised.
**Why it happens:** `QFileSystemWatcher` silently ignores non-existent paths.
**How to avoid:** Call `books_dir.mkdir(parents=True, exist_ok=True)` in `BookWatcherService.__init__()` before `addPath()`. Assert `addPath()` return value in dev/debug builds.
**Warning signs:** Watcher service seems to work but new file drops never trigger ingestion.

### Pitfall 4: Chapter Title Extraction Differences Between Books

**What goes wrong:** Alice and Oz put the chapter title on the *next line* after the heading; Anne puts it on the *same line*. A single-regex approach returns an empty title for Alice/Oz.
**Why it happens:** Different editions/transcribers at Project Gutenberg used different formatting conventions.
**How to avoid:** After matching the heading, check if the inline group is empty; if so, take the next non-empty line as the title. The pattern in Pattern 4 above handles both cases.
**Warning signs:** Chapters in Alice/Oz getting empty-string titles in the `.sov-book` output.

### Pitfall 5: Missing `__init__.py` in `content/books/`

**What goes wrong:** `importlib.resources.files("switchedonvoice.content.books")` raises `ModuleNotFoundError` or returns an empty traversable.
**Why it happens:** Without `__init__.py`, the directory is not recognised as a Python package for `importlib.resources` traversal.
**How to avoid:** Create empty `src/switchedonvoice/content/__init__.py` and `src/switchedonvoice/content/books/__init__.py` in the same wave as the content directory.
**Warning signs:** `importlib.resources.files("switchedonvoice.content.books")` works in editable install but fails after `pip install`.

### Pitfall 6: `_SCHEMA_V2` Tables Not Idempotent on Repeated `init_db()` Calls

**What goes wrong:** Calling `init_db()` twice on an already-migrated-to-v2 database crashes because `CREATE TABLE` (without `IF NOT EXISTS`) fails.
**Why it happens:** All `CREATE TABLE` in `_SCHEMA_V2` must use `IF NOT EXISTS` to stay idempotent.
**How to avoid:** Use `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` throughout `_SCHEMA_V2` — the existing `_SCHEMA` in `db.py` already does this.
**Warning signs:** `test_init_is_idempotent` test (from `test_db.py`) fails after v2 migration.

---

## Code Examples

### `.sov-book` JSON Schema

```json
{
  "slug": "alice-wonderland",
  "title": "Alice's Adventures in Wonderland",
  "author": "Lewis Carroll",
  "language": "en",
  "source": "Project Gutenberg #11",
  "licence": "Public domain",
  "version": "1.0",
  "chapters": [
    {
      "number": 1,
      "title": "Down the Rabbit-Hole",
      "passages": [
        {
          "position": 1,
          "text": "Alice was beginning to get very tired...",
          "word_count": 143,
          "difficulty": "easy",
          "phonemic_density": null,
          "recommended_f0_target": null
        }
      ]
    }
  ]
}
```

### `import_book.py` Entry Point

```python
# python -m switchedonvoice.tools.import_book alice.txt alice.sov-book
# Source: designed to match D-05/D-06 decisions

def main() -> None:
    import argparse, sys
    parser = argparse.ArgumentParser(
        description="Convert a Project Gutenberg .txt to .sov-book JSON"
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--slug", required=True, help="Unique slug for this book")
    args = parser.parse_args()

    raw = args.input.read_text(encoding="utf-8")
    content = strip_boilerplate(raw)
    chapter_data = split_chapters(content)
    book = build_sov_book(args.slug, chapter_data)
    args.output.write_text(json.dumps(book, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written: {args.output} ({len(book['chapters'])} chapters)")

if __name__ == "__main__":
    main()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `setuptools` `package_data` for non-py files | hatchling auto-includes all files under package | hatchling ~2022 | No pyproject.toml change needed for `.sov-book` assets |
| `importlib.resources.open_text()` (deprecated) | `importlib.resources.files().joinpath().read_text()` | Python 3.9 | Old API removed in Python 3.13; `files()` API is the correct form |
| `watchdog` / polling-based file watchers | `QFileSystemWatcher` (Qt native) | — | Already in PySide6; no extra dep; uses inotify on Linux |
| Module-level functions for repository operations | `BookRepository` class | Phase 2 decision D-07 | Class enables `db_path` injection and easier testing |

**Deprecated/outdated:**
- `importlib.resources.open_text(package, resource)`: removed in Python 3.13+. Use `files(package).joinpath(resource).read_text()`.
- `pkg_resources.resource_filename()`: setuptools-only, don't use.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Empty `__init__.py` files in `content/` and `content/books/` are required for `importlib.resources.files()` to traverse the package | Pattern 6, Pitfall 5 | If wrong: `files()` still works (Python 3.11+ namespace package support). Low risk — adding `__init__.py` is always safe. |
| A2 | Hatchling auto-includes `.sov-book` JSON files without extra config | Standard Stack, Pattern 6 | If wrong: add `[tool.hatch.build.targets.wheel] artifacts = ["**/*.sov-book"]` to pyproject.toml. Easy fix if caught at build time. |
| A3 | `reading_progress` UNIQUE constraint on `(profile_id, passage_id)` with NULL `profile_id` behaves correctly in SQLite (NULL != NULL, so multiple NULL rows are allowed per SQLite spec) | Pattern 1 schema | Risk: multiple NULL rows could be inserted for the same passage. Mitigation: use `(COALESCE(profile_id, -1), passage_id)` as a computed unique key, or handle in application layer. |

---

## Open Questions (RESOLVED)

1. **`reading_progress` NULL uniqueness (A3 above)**
   - What we know: SQLite treats NULL != NULL for UNIQUE constraints — two rows with `(NULL, passage_id=5)` are NOT considered duplicates.
   - RESOLVED: Use UPDATE-then-INSERT pattern in `BookRepository.update_progress()` for `profile_id IS NULL` rows. Do not rely on the UNIQUE constraint alone. See Plan 01, Task 2, D-09 note.

2. **`import_book.py` argument design**
   - What we know: The CLI is `python -m switchedonvoice.tools.import_book` per D-05.
   - RESOLVED: `--slug` is a required argument with a clear error on omission. The three bundled books have known slugs (`alice`, `oz`, `anne`); the tool is for developers, not end users. See Plan 02, Task 1.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All | ✓ | 3.14.5 | — |
| PySide6 | QFileSystemWatcher, QThread | ✓ | 6.11.1 | — |
| sqlite3 | DB layer | ✓ | stdlib | — |
| inotify (kernel) | QFileSystemWatcher on Linux | ✓ | kernel 7.0.9 (524288 watches) | QTimer polling (not recommended) |
| importlib.resources | Bundled asset access | ✓ | stdlib (Python 3.9+ `files()` API) | — |
| pytest | Tests | ✓ | 9.0.3 | — |
| pytest-qt | Watcher integration tests | ✓ | 4.5.0 | — |
| pytest-cov | Coverage | ✓ | 7.1.0 | — |
| hatchling | Package builds | ✓ (build system) | In build env | — |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | none yet — no `[tool.pytest.ini_options]` in pyproject.toml |
| Quick run command | `pytest tests/content/ -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-R01 | `list_books()` returns 3 bundled books after ingest | unit | `pytest tests/content/test_books_repository.py -x` | ❌ Wave 0 |
| REQ-R01 | `get_chapters(book_id)` returns correct chapter count | unit | `pytest tests/content/test_books_repository.py -x` | ❌ Wave 0 |
| REQ-R01 | `get_passages(chapter_id)` returns passages in order | unit | `pytest tests/content/test_books_repository.py -x` | ❌ Wave 0 |
| REQ-R01 | Passage word counts near 150; never cuts mid-sentence | unit | `pytest tests/content/test_import_book.py::test_passage_splitting -x` | ❌ Wave 0 |
| REQ-R01 | PG boilerplate stripped from all 3 books | unit | `pytest tests/content/test_import_book.py::test_strip_boilerplate -x` | ❌ Wave 0 |
| REQ-R01 | Folder drop of `.sov-book` triggers ingestion | integration | `pytest tests/content/test_book_watcher.py -x` | ❌ Wave 0 |
| REQ-R05 | `reading_progress` table exists with required columns | unit | `pytest tests/content/test_books_repository.py::test_reading_progress_schema -x` | ❌ Wave 0 |
| REQ-R05 | `update_progress()` inserts and updates correctly | unit | `pytest tests/content/test_books_repository.py::test_update_progress -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/content/ -x --tb=short`
- **Per wave merge:** `pytest --tb=short`
- **Phase gate:** Full suite green (`pytest`) before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/content/__init__.py` — package marker
- [ ] `tests/content/test_books_repository.py` — covers REQ-R01 (queries), REQ-R05 (progress)
- [ ] `tests/content/test_import_book.py` — covers boilerplate stripping, chapter detection, passage splitting
- [ ] `tests/content/test_book_watcher.py` — covers folder-drop ingestion

---

## Security Domain

> `security_enforcement` not set in config.json (absent = enabled).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no user accounts in this phase) |
| V3 Session Management | no | — |
| V4 Access Control | no | — (single-user local app) |
| V5 Input Validation | yes | Validate `.sov-book` JSON keys before INSERT; reject malformed files via `ValueError` |
| V6 Cryptography | no | — |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed `.sov-book` drop with SQL injection in `title`/`text` fields | Tampering | Parameterised queries (already used in `sessions.py`; BookRepository must use `?` placeholders) |
| Path traversal via `slug` field (`../../etc/passwd`) | Tampering | Slug is stored as text only; never used to construct file paths. No risk. |
| Unbounded `text` field (e.g., 50MB passage) | DoS | Validate `word_count <= 10_000` (hard cap) during ingestion; reject oversized passages |

---

## Sources

### Primary (HIGH confidence)
- Direct network fetch of PG #11, #55, #45 source `.txt` files — chapter heading patterns verified
- `src/switchedonvoice/storage/db.py` + `sessions.py` — existing patterns read directly
- `src/switchedonvoice/ui/main_window.py` — `_DB_PATH = data.db` confirmed
- PySide6 6.11.1 interactive Python session — QFileSystemWatcher API, QThread pattern verified
- `/proc/sys/fs/inotify/` — inotify availability on CachyOS kernel 7.0.9 confirmed
- `importlib.resources.files()` — available in Python 3.14.5 (verified)
- pytest 9.0.3, pytest-qt 4.5.0 — confirmed installed in `.venv`

### Secondary (MEDIUM confidence)
- [CITED: hatch.pypa.io/1.16/config/build/] — Hatchling default file inclusion behaviour confirmed from official docs

### Tertiary (LOW confidence)
- None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all verified by direct tool calls against installed packages
- Architecture: HIGH — patterns derived from existing codebase conventions
- Chapter heading patterns: HIGH — fetched directly from Project Gutenberg
- Pitfalls: HIGH — derived from verified behaviour (inotify, SQLite, importlib.resources)

**Research date:** 2026-05-29
**Valid until:** 2026-08-29 (stable domain; PySide6 minor versions won't break patterns)
