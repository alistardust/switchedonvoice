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
| `source` | string | ✅ | Attribution URL (Project Gutenberg permalink preferred). May be empty string `""` if no URL is available, but must be present. |
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
- `ch<N>`: chapter number, zero-padded to 2 digits (e.g., `ch01`, `ch12`)
- `p<N>`: passage position, zero-padded to 3 digits (e.g., `p001`, `p042`)

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
- To replace a book's content, the book must first be deleted from the DB, then re-imported.
- Future tooling (Phase 16+) may provide an explicit `update` operation.

The folder-watcher service (`BookWatcherService`) applies the same rule: dropping the same `.sov-book` file twice is a no-op.

---

## Validation Rules

A `.sov-book` file is **valid** if and only if:

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

The `import_book` converter guarantees all of the above. The `BookRepository.ingest()` method validates rules 1–6 and raises `ValueError` on violation; rules 7–10 are asserted in the test suite.

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

This spec requires two updates to the existing Phase 2 plans:

1. **02-01-PLAN.md (schema):** `passages` table gains a `slug TEXT UNIQUE NOT NULL` column. `reading_progress` references `passage_slug TEXT NOT NULL` (in addition to or instead of `passage_id INTEGER`). The schema version bumps to 2.

2. **02-02-PLAN.md (converter):** `build_sov_book()` generates passage slugs using `f"{book_slug}-ch{chapter_number:02d}-p{position:03d}"` before writing the JSON. This is ~3 lines of code.

All other plan steps are unaffected.

---

## Future Compatibility

- New optional fields may be added at any schema level in future `schema_version` values. Consumers must ignore unknown fields.
- New required fields require a `schema_version` bump and a migration in `import_book`.
- The `phonemic_density` and `recommended_f0_target` fields are reserved for Phase 16 (Instructor Mode) editorial tooling.
