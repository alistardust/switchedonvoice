# `.sov-book` File Format — Design Spec

**Date:** 2026-05-29
**Status:** Approved
**Author:** alistardust / Sam (Copilot)
**Closes:** https://github.com/alistardust/switchedonvoice/issues/27

---

## Overview

`.sov-book` is the content interchange format for SwitchedOnVoice's reading library. It is a UTF-8 encoded JSON file containing one book's metadata, chapters, and practisable passages. It is the boundary between the offline converter tooling and the runtime application.

The format is **write-once, read-many**: files are produced by the `import_book` CLI converter and consumed by `BookRepository.ingest()`. They are never written by the running application.

---

## Design Goals

1. **Human-readable** — a developer can open the file and understand its structure without tooling.
2. **Stable identity** — passage slugs are deterministic and immutable; re-importing the same source file always produces the same slugs.
3. **Self-describing** — the file carries all metadata needed to display, ingest, and attribute the book without external lookups.
4. **Forward-compatible** — a `schema_version` field allows future fields to be added without breaking existing consumers.

---

## File Structure

A `.sov-book` file is a single JSON object. Filename convention: `<book-slug>.sov-book` (e.g., `alice-wonderland.sov-book`).

```json
{
  "schema_version": 1,
  "slug": "alice-wonderland",
  "title": "Alice's Adventures in Wonderland",
  "author": "Lewis Carroll",
  "language": "en",
  "source": "https://www.gutenberg.org/ebooks/11",
  "licence": "Public domain",
  "version": "1.0",
  "chapters": [
    {
      "number": 1,
      "title": "Down the Rabbit-Hole",
      "passages": [
        {
          "slug": "alice-wonderland-ch01-p001",
          "position": 1,
          "text": "Alice was beginning to get very tired of sitting by her sister on the bank...",
          "word_count": 147,
          "difficulty": "easy",
          "phonemic_density": null,
          "recommended_f0_target": null
        }
      ]
    }
  ]
}
```

---

## Field Reference

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | integer | ✅ | Format version. Currently `1`. Consumers must reject files with unknown versions. |
| `slug` | string | ✅ | Stable URL-safe identifier for the book. Lowercase, hyphenated. Used as the primary deduplication key by `BookRepository`. Must be unique across all books in the library. |
| `title` | string | ✅ | Display title of the book. |
| `author` | string | ✅ | Author's name as it should appear in the UI. |
| `language` | string | ✅ | BCP 47 language tag (e.g. `"en"`). |
| `source` | string | ✅ | Attribution text or URL. For Project Gutenberg books, use the canonical URL (e.g., `"https://www.gutenberg.org/ebooks/11"`). For books without a URL, use descriptive attribution text (e.g., `"Traditional"`). May be empty string `""` if no attribution is available, but the field must be present. |
| `licence` | string | ✅ | Human-readable licence statement. For PG texts: `"Public domain"`. |
| `version` | string | ✅ | Content version string (e.g. `"1.0"`). Increment when passage text is edited. Not the same as `schema_version`. |
| `chapters` | array | ✅ | Ordered array of chapter objects. Must contain at least 1 chapter. |

### Chapter Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `number` | integer | ✅ | 1-based chapter number. Must be unique within the book and contiguous from 1. |
| `title` | string | ✅ | Chapter display title. May be empty string `""` for untitled chapters. |
| `passages` | array | ✅ | Ordered array of passage objects. Must contain at least 1 passage. |

### Passage Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `slug` | string | ✅ | Stable, globally unique passage identifier. See Slug Specification below. |
| `position` | integer | ✅ | 1-based position of the passage within its chapter. |
| `text` | string | ✅ | Full passage text as a single string. Sentences separated by spaces. No embedded newlines. |
| `word_count` | integer | ✅ | Number of whitespace-delimited tokens in `text`. Must match `len(text.split())`. |
| `difficulty` | string | ✅ | One of `"easy"`, `"medium"`, `"hard"`. See Difficulty Assignment below. |
| `phonemic_density` | float \| null | ✅ | Reserved for future editorial annotation. Always `null` in v1. |
| `recommended_f0_target` | float \| null | ✅ | Reserved for future editorial annotation. Always `null` in v1. |

---

## Slug Specification

Passage slugs are the **stable identity** for all downstream references: bookmarks, reading progress, completion records, and audio recordings (Phase 5+). They must be deterministic and immutable.

### Format

```
<book-slug>-ch<chapter_number_zero_padded>-p<position_zero_padded>
```

- `<book-slug>`: the top-level `slug` field of the book
- `ch<N>`: chapter number, formatted with `{n:02d}` — minimum 2 digits, no truncation. Chapter 1 → `ch01`; chapter 12 → `ch12`; chapter 100 → `ch100`.
- `p<N>`: passage position, formatted with `{n:03d}` — minimum 3 digits, no truncation. Position 1 → `p001`; position 42 → `p042`; position 1000 → `p1000`.

**Examples:**
- `alice-wonderland-ch01-p001` — Alice, chapter 1, passage 1
- `alice-wonderland-ch12-p003` — Alice, chapter 12, passage 3
- `wizard-of-oz-ch07-p002` — Oz, chapter 7, passage 2

### Immutability Guarantee

Once a `.sov-book` file is published (committed to the package or released), its passage slugs **must never change**. The `import_book` converter generates slugs deterministically from `(book_slug, chapter_number, passage_position)` — re-running the converter on the same source file must always produce the same slugs.

If passage text is corrected, increment `version` but **do not change slugs**. Existing progress records remain valid; they will reflect the old text's scores, which is acceptable.

If a chapter is restructured (split or merged), this is a **breaking change** that requires a new book slug (e.g., `alice-wonderland-v2`) and treating the restructured book as a new book. Existing progress is not migrated automatically.

---

## Difficulty Assignment

The `difficulty` field is assigned by the converter based on average sentence length:

| Average words per sentence | Difficulty |
|---------------------------|------------|
| < 15 | `"easy"` |
| 15–19 | `"medium"` |
| ≥ 20 | `"hard"` |

Computed as: `total_words / max(sentence_count, 1)` where sentences are split on `.`, `!`, `?` boundaries.

---

## Passage Splitting Rules

These rules govern how the `import_book` converter produces passages from chapter text:

1. **Target length:** ~150 words per passage.
2. **Short chapters:** A chapter with fewer than 100 total words becomes a single passage (no splitting).
3. **Sentence boundary rule:** Passages never split mid-sentence. The greedy accumulator flushes when the next sentence would exceed the target; the flush point is always after a sentence-terminal punctuation character (`.`, `!`, `?`).
4. **Tolerance:** A passage may exceed 150 words if a single sentence exceeds 150 words (no sentence is split).
5. **Final passage:** The last passage in a chapter may be shorter than 150 words.

---

## Duplicate Detection and Re-import Behaviour

`BookRepository.ingest(data)` uses the top-level `slug` as its deduplication key:

- If `book_exists(slug)` returns `True`, the ingest is **skipped silently** (no update, no error).
- To replace a book's content, call `BookRepository.delete_book(slug)` first, then re-import.
- Future tooling (Phase 16+) may provide an explicit `update` operation.

The folder-watcher service (`BookWatcherService`) applies the same rule: dropping the same `.sov-book` file twice is a no-op.

### Delete Workflow and Cascade Warning

`BookRepository.delete_book(slug)` deletes the `books` row. Because `chapters` and `passages` use `ON DELETE CASCADE`, all chapters and passages for the book are also deleted. Because `reading_progress` references `passages.slug` (TEXT FK with `ON DELETE CASCADE`), all reading progress for those passages is also deleted.

**This is intentional and irreversible.** The application must:
1. Show a confirmation dialog before deletion (Phase 3 UI).
2. Warn the user that progress records for this book will be deleted.
3. Consider offering an export before deletion (Phase 18+).

Recordings (Phase 5+) are **not** auto-deleted by the cascade (they are files, not DB rows). Phase 5 must handle orphaned recordings on book deletion.

---

## Validation Rules

A `.sov-book` file is **valid** if and only if all of the following hold:

1. It is valid UTF-8 encoded JSON.
2. All required fields are present at every level (book, chapter, passage).
3. `schema_version` equals `1` (or a version the consumer supports).
4. `slug` matches the pattern `^[a-z0-9][a-z0-9-]*[a-z0-9]$`.
5. Passage `slug` values are unique within the file and match the format `<book-slug>-ch<NN>-p<NNN>`.
6. `chapters` is non-empty; each chapter's `passages` is non-empty.
7. Chapter `number` values are unique within the book and form a contiguous sequence starting at 1.
8. Passage `position` values within each chapter are unique and contiguous starting at 1.
9. `difficulty` is one of `"easy"`, `"medium"`, `"hard"`.
10. `word_count` equals `len(passage["text"].split())`.
11. `title`, `author`, and `language` are non-empty strings (whitespace-only strings are rejected).
12. `passage.text` is a non-empty string containing no embedded newline characters (`\n`, `\r`).
13. `phonemic_density` and `recommended_f0_target` are `null` in schema version 1.

**Runtime vs. converter enforcement:**

The `import_book` converter guarantees all rules. `BookRepository.ingest()` validates rules 1–9, 11–13 at runtime and raises `ValueError` on any violation; rules 10 (word count parity) is verified by the test suite rather than at runtime ingest (computing `len(text.split())` for every passage at ingest is acceptable cost, but the check can be deferred to converter output validation). Runtime validation is required for user-dropped files (folder-watcher path) where the converter may not have been used.

---

## SQLite Mapping

The `.sov-book` structure maps to the Phase 2 SQLite schema as follows:

| `.sov-book` field | SQLite table | Column |
|-------------------|--------------|--------|
| `slug` | `books` | `slug TEXT UNIQUE NOT NULL` |
| `title` | `books` | `title TEXT NOT NULL` |
| `author` | `books` | `author TEXT NOT NULL` |
| `language` | `books` | `language TEXT NOT NULL DEFAULT 'en'` |
| `source` | `books` | `source TEXT NOT NULL DEFAULT ''` |
| `licence` | `books` | `licence TEXT NOT NULL DEFAULT 'Public domain'` |
| `version` | `books` | `version TEXT NOT NULL DEFAULT '1.0'` |
| `chapter.number` | `chapters` | `number INTEGER NOT NULL` |
| `chapter.title` | `chapters` | `title TEXT NOT NULL` |
| `passage.slug` | `passages` | `slug TEXT UNIQUE NOT NULL` |
| `passage.position` | `passages` | `position INTEGER NOT NULL` |
| `passage.text` | `passages` | `text TEXT NOT NULL` |
| `passage.word_count` | `passages` | `word_count INTEGER NOT NULL` |
| `passage.difficulty` | `passages` | `difficulty TEXT CHECK(...)` |
| `passage.phonemic_density` | `passages` | `phonemic_density REAL` |
| `passage.recommended_f0_target` | `passages` | `recommended_f0_target REAL` |

`reading_progress` and all downstream progress/recording tables reference `passages.slug` (TEXT) rather than `passages.id` (INTEGER) as their stable foreign key.

---

## Impact on Phase 2 Plans

This spec requires updates to four Phase 2 plan files:

### 02-01-PLAN.md (schema + BookRepository)
- `passages` table gains `slug TEXT UNIQUE NOT NULL` column (before `position`).
- `reading_progress` uses `passage_slug TEXT NOT NULL REFERENCES passages(slug) ON DELETE CASCADE` instead of `passage_id INTEGER NOT NULL REFERENCES passages(id)`. The UNIQUE constraint becomes `UNIQUE(profile_id, passage_slug)`. The index becomes `idx_progress_passage ON reading_progress(passage_slug)`.
- `Passage` dataclass gains `slug: str` field.
- `BookRepository` gains `get_passage_by_slug(slug: str) → Passage` method; `get_passage(passage_id)` remains for numeric lookups but downstream code (Phase 3+) should prefer `get_passage_by_slug`.
- `update_progress()` parameter changes from `passage_id: int` to `passage_slug: str`.
- `BookRepository.delete_book(slug: str) → None` method added (deletes book row; cascades to chapters/passages/reading_progress).
- Test `test_v2_tables_have_expected_columns` must check that `slug` column is present in `passages`.

### 02-02-PLAN.md (converter)
- `build_sov_book()` signature gains `slug: str` as its first required parameter (the book slug).
- `build_sov_book()` generates passage slugs: `f"{slug}-ch{chapter_number:02d}-p{position:03d}"`.
- Output dict includes `"schema_version": 1` as the first key.
- Each passage dict includes `"slug": passage_slug`.
- Interfaces section must add `slug` to the passage required fields list.
- Acceptance criteria: `build_sov_book` returns dict with `schema_version` key; each passage has `slug` key.

### 02-03-PLAN.md (bundled book assets)
- `must_haves.truths`: add "Every passage in every bundled book has a `slug` field matching `<book-slug>-ch<NN>-p<NNN>`" and "`schema_version` equals 1 in all bundled books".

### 02-05-PLAN.md (tests)
- Minimal valid `.sov-book` fixture: add `"schema_version": 1` at top level; add `"slug": "test-book-ch01-p001"` to the passage object.

---

## Future Compatibility

- New optional fields may be added at any schema level in future `schema_version` values. Consumers must ignore unknown fields.
- New required fields require a `schema_version` bump and a migration in `import_book`.
- The `phonemic_density` and `recommended_f0_target` fields are reserved for Phase 16 (Instructor Mode) editorial tooling.
