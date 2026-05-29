# SwitchedOnVoice — Product Vision

> **Last updated:** 2026-05-29
> **Status:** APPROVED
> **Mode:** Builder → Open Source (personal first, community later)

---

## The North Star

**Help trans people become themselves through voice training.**

Not just "get better at voice." Become the person they know they are. SwitchedOnVoice is
the tool that makes that journey approachable, measurable, joyful, and real.

---

## The Emotional Core

Six months into training, a user opens SwitchedOnVoice and listens to themselves reading
the same passage on day one, then month three, then today. They hear their F0 rise. They
see the waveforms shift. They hear themselves sound more confident, more like themselves.

**That moment is the product.**

Everything else — the gamification, the arcade, the curriculum, the books — exists to
get the user to that moment, and to make sure they show up every day until they get there.

---

## Design Principles

### 1. Inviting, Not Scary
Voice training can feel clinical, overwhelming, and anxiety-inducing. SwitchedOnVoice
is the opposite. Every screen, every prompt, every interaction should feel like a warm
welcome, not a test.

- No "you failed" language. Only "you grew" and "you're getting there."
- Low floor, high ceiling. A first-time user can open the app and do something meaningful
  in under five minutes.
- Never punish absence. Streaks celebrate showing up; they don't shame gaps.

### 2. Fun and Affirming
The app should feel **cute** and have **personality**. It is not a clinical tool.
It is a companion on a personal journey.

- Rewarding microinteractions (XP, level-ups, arcade scores)
- Character and warmth in every empty state, prompt, and celebration
- Reading mode uses books the user actually wants to read

### 3. Science-Backed, Not Science-Gatekept
The acoustic analysis is grounded in real vocal science: fundamental frequency (F0),
formant resonance (F1/F2), cepstral peak prominence (CPP), vocal health metrics.
But none of that complexity leaks into the user experience unless the user wants it.

- Default view: simple, clear feedback ("you're in your target range")
- Advanced view available: full spectral analysis, CPP trends, formant plots
- Every metric has plain-language explanations

### 4. Progress Is Personal
Users are measured only against themselves. No comparisons to "female average."
No external benchmark that implies a binary goal. The target is **the user's own goal**,
calibrated during onboarding, adjustable over time.

### 5. Works Alone or With a Coach
The app is a full standalone tool. It is also the best tool a trans vocal coach could
use with their students. Both paths are first-class.

---

## The Virtual Coach

SwitchedOnVoice will have a **built-in virtual coaching companion** — a cute, named
character with animations and a voice of her own. She is:

- **Rules-based, not LLM-based.** She reads the user's progress data, the curriculum,
  and the science, then tells the user what to practice next. Deterministic, offline,
  privacy-preserving. No API calls.
- **Affirming, not nagging.** She celebrates wins enthusiastically. She suggests
  next steps gently. She never makes the user feel behind.
- **Scientifically grounded.** Her guidance is derived from real vocal pedagogy:
  warm-ups before exercises, resonance work after pitch work, rest recommendations.
- **Visually designed separately.** The avatar design, animations, and voice will be
  commissioned from a designer/artist. The app provides the infrastructure; the
  character is a creative collaboration.

Think: Clippy and BonziBuddy if they were cute, affirming, and actually helpful.

---

## The Milestone Comparison Feature

The feature that delivers the emotional core:

1. At designated milestones (or on demand), the user records the same standard passage.
2. The app stores these recordings tagged with date and acoustic analysis.
3. The user can open a **Milestone View** that shows:
   - Side-by-side or sequential audio playback of the same passage across dates
   - Waveform overlay: visual before/after
   - Acoustic analysis overlay: F0 contour, resonance, CPP across time
   - A timeline of their journey with notes and badges

This is the "hearing yourself become yourself" moment. It should be beautiful,
emotional, and shareable (with consent controls).

---

## User Journeys

### Solo Trainee (Primary)
1. Opens app → meets the virtual coach → completes onboarding (baseline calibration)
2. Gets a suggested first practice: a warm-up + a short passage
3. Reads aloud, gets real-time F0/resonance overlay, sees their score
4. Earns XP, finishes the session, sees streak count
5. Over weeks: skill tree unlocks, arcade games appear, curriculum advances
6. At 3-month milestone: hears their own journey. Shares it (optionally).

### Student with Coach (Secondary)
1. Coach opens app → creates student profile → assigns exercises
2. Student practices independently with the virtual coach between sessions
3. Coach reviews session data, progress charts, F0/resonance trends
4. Coach exports session report to share or discuss
5. Together they track progress toward the student's personal goals

### Returning User (Retention)
1. Opens app → virtual coach greets them (affirming, not shaming if absent)
2. "Today's goal" is already set; can start practice in one tap
3. Arcade mode available for low-stakes fun on a hard day
4. Singing mode available when they're ready to explore

---

## Long-Term Vision (v3.0+)

After the core singing mode (v2.0), the product's next frontier:

- **Milestone Comparison Mode** — the emotional heart feature described above
- **Virtual Coach + Avatar** — rules-based coaching system with commissioned character
- **Community features** (optional, privacy-first) — share passages, share milestones,
  find community in the journey without being compared to others
- **Mobile companion app** (deferred) — would require significant platform work;
  desktop remains primary

---

## What This Is Not

- Not a medical device or substitute for professional voice therapy
- Not a judgment of how "passing" someone's voice is
- Not a comparison tool ("you sound more/less feminine than average")
- Not an LLM chatbot — the virtual coach is data-driven, not generative
- Not cloud-dependent — everything runs locally; no account required

---

## Platform Philosophy

**Local-first. Privacy-first. Open source eventually.**

- All audio processing happens on-device. No recordings leave the machine by default.
- The database is a local SQLite file the user owns completely.
- When the app is ready and the community asks, it will be open source.
- If it helps even one person, it was worth building.
