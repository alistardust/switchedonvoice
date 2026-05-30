# Phase 5: Recording & Playback History - Context

**Gathered:** 2026-05-30
**Status:** Ready for planning after Phase 4 completion contract is locked

<domain>
## Phase Boundary

Phase 5 gives Reading Mode memory in audio form. The user can opt into
recording a reading attempt, finish the passage, and later return to hear a
timeline of dated recordings for that exact passage. She can also see how
much local storage recordings consume and delete them safely.

This phase is offline-only and local-file based. No recording metadata or
audio leaves the device.
</domain>

<decisions>
## Key Implementation Decisions

### Recording architecture
- **D-05-01:** Put recording logic in a dedicated package (for example
  `recordings/`) instead of embedding WAV I/O into `ReadingPanel` or
  `AudioCapture`. The UI should tell a recorder when to start/stop and which
  passage is active; the recorder owns file writing.
- **D-05-02:** Do **not** write files from the existing
  `AnalysisResult.raw_audio` field as-is. That field currently holds the
  rolling 200 ms analysis window and would duplicate audio badly if appended
  frame-by-frame. Phase 5 needs a non-overlapping audio chunk tap (either a
  new `AnalysisResult.audio_chunk` field or a recorder queue fed from the
  capture callback/thread).
- **D-05-03:** Keep the sounddevice callback minimal. If a recording tap is
  added there, it must remain an append/copy into a queue/deque only; no WAV
  encoding, no file I/O, and no blocking calls in the callback.

### File layout and identity
- **D-05-04:** Store files under
  `~/.switchedonvoice/recordings/<book_slug>/<passage_slug>/<timestamp>.wav`.
  The path must be keyed by `passage_slug`, not `chapter_slug`, because the
  passage is the stable unit of playback history and comparison.
- **D-05-05:** Use a dedicated library/service to enumerate recordings,
  compute sizes, and delete files. The UI should never recurse the filesystem
  directly.

### Playback + thumbnails
- **D-05-06:** Centralise playback in a single controller/state machine so
  only one recording can be playing at once. Starting a new recording should
  stop the previous one first.
- **D-05-07:** Thumbnail generation must happen off the GUI thread and return
  precomputed sample points or a ready `QPixmap`. Do not decode WAVs inside a
  paint event.

### Settings / consent
- **D-05-08:** Add `record_by_default: bool` to `Settings`, and treat the
  per-session reading prompt as a UI choice initialised from that setting.
  The stored default should never override the explicit choice the user makes
  for the current attempt.
</decisions>

<architecture>
## Architecture Fit

- `audio/capture.py` already owns microphone access and the analysis thread.
  Phase 5 should extend that pipeline surgically so recorded audio comes from
  the same source without adding another live input stream.
- `storage/settings.py` remains the right home for the global recording
  default; the actual recordings themselves live on disk under
  `~/.switchedonvoice/recordings/`, not in SQLite blobs.
- Phase 4's Reading completion hook is the natural place to finalise a
  recording and refresh playback history.
- Existing `ui/waveform_widget.py` contains useful rendering knowledge, but
  the static history thumbnail should not reuse the live-widget update loop.
  Extract shared sample-to-geometry logic if helpful, but keep history
  thumbnails asynchronous.
</architecture>

<dependencies>
## Required Upstream Artifacts

Phase 5 assumes all of the following already exist:

- Phase 4 Reading Mode completion flow (so recordings have a clear stop/save
  point and can refresh history after completion).
- Phase 4 passage identity, score persistence, and per-passage comparison UI.
- Phase 3 Reading selector/passage state with stable `book_slug` and
  `passage_slug` available in the panel.
- Phase 1/4 shared `AudioCapture` pipeline, still owning the only live input
  stream.

Additional dependency to add explicitly: `soundfile` is required for WAV
read/write in the brief, but it is not currently present in `pyproject.toml`.
This must be added as a runtime dependency before implementation begins.
</dependencies>

<pitfalls>
## Critical Pitfalls to Avoid

- **Do not append overlapping analysis windows to the recorder.** This would
  create duplicated, stretched audio and make playback unusable.
- **Do not block the GUI thread while loading waveforms.** History views can
  easily contain many recordings for one passage.
- **Do not trust cached storage totals after deletion.** Recompute from disk
  or update the authoritative in-memory model from the actual delete result.
- **Do not allow path traversal through slug values or delete filters.** All
  delete operations must stay rooted under the recordings directory.
- **Do not leave partially written WAV files after cancel/close.** The stop
  path must close files cleanly and either keep a valid WAV or remove the
  incomplete file.
- **Do not let multiple play buttons drive independent sounddevice state.**
  Playback must have one explicit owner.
</pitfalls>

<open_questions>
## Open Questions Before Execution

1. **Audio tap contract:** Will recording use a new non-overlapping field on
   `AnalysisResult`, or a recorder queue fed directly from the callback/
   analysis thread? The requirement should be resolved before implementation
   to avoid accidental double buffering.
2. **Prompt timing:** Should the “Record this session?” prompt appear when the
   user opens a passage, when she presses an explicit start/finish action, or
   automatically at first word advance? Phase 4 completion flow will affect
   the best answer.
3. **Playback lifecycle:** Should playback stop automatically when the user
   switches passages/tabs, or only when she presses Stop? Auto-stop on
   navigation is likely safest for UX and testability.
</open_questions>

---

*Phase: 05-recording-playback*
*Context gathered: 2026-05-30*
