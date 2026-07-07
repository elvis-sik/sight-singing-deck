# Dictation Curriculum (design of record)

A curriculum for **melodic dictation** (hear it → notate it) as a skill in its
**own right**, with its own difficulty ordering and its own melody pool — not the
sight-singing melodies run backwards.

This supersedes the "dictation reuses the sight-singing material" stance in
[`CURRICULUM.md`](CURRICULUM.md). Sight-singing stays as designed; this document
covers only the parallel dictation path.

> Status: **draft for review.** Nothing here is built yet. The stage ladder below
> is a proposal to react to before it is encoded into `curriculum/stages.py`.

## Why a separate curriculum

Dictation and sight-singing are the two directions of one skill (audiation), but
they are **gated by different things**, so the optimal ordering diverges:

| Axis | Sight-singing difficulty | Dictation difficulty |
|---|---|---|
| Vocal production / pitching a leap | **primary** | irrelevant (you're not singing) |
| Range / tessitura | matters | irrelevant |
| **Phrase length / working memory** | minor | **primary** — the core dictation skill |
| **Rhythmic complexity** | a separate track; melodies stay even | **primary**, and best *isolated* first |
| Interval **audibility** (is it easy to *hear*?) | secondary | **primary** — consonant/triadic first |
| Tonal function (which degrees) | primary early | primary early (**shared** — the one axis both agree on) |

Two consequences:

1. **Length and rhythm are first-class ramps** for dictation (they barely move in
   the early sight-singing ladder). A 6-note stepwise phrase is trivial to sing
   but taxes dictation memory; a short leapy phrase is the reverse.
2. **Reusing the same tunes degrades dictation into recall.** Once you've
   sight-sung a melody a dozen times, "taking dictation" of it is remembering, not
   hearing — and sibling-burying only prevents *same-day* collisions, not
   long-term familiarity. So dictation needs its **own melody pool**.

## Structural approach

- **One note type** (the existing Sing + Transcribe templates). No new model.
- **Conditional card generation** (not suspension): each note carries a role
  marker (e.g. `SingEnabled` / `DictateEnabled` fields). The Sing template renders
  only when sing is enabled; the Transcribe template only when dictation is
  enabled. A melody used in one curriculum generates exactly one card — Anki never
  creates the other. (Literal suspension is available as a live-collection
  AnkiConnect step if reversibility is ever wanted; conditional generation is the
  default for the built/shipped deck. See [[ankiconnect-live-deck-update]].)
- **Two deck trees.** The Sing cards live under the existing `Sight Singing::…`
  study-path tracks; the Transcribe cards live under a parallel `Dictation::…`
  tree with its **own** numbered tracks. Independent scheduling and daily volume.
- **Mostly-disjoint melody pools.** Dictation draws its own generated melodies
  (same engine, different tunes) so it stays genuine ear-work. **Deliberate
  overlap is allowed** — a melody you want both ways generates both cards, which
  are siblings (spoiler-protected by burying); those few notes file into one tree
  (or get a post-build card move). Expect overlap to be small.

All of this reuses the existing `Stage` constraint-spec engine
(`curriculum/stages.py`): `pool` / `start_pool` / `end_pool`, `max_step` /
`min_step`, `length`, `require_present_any`, `require_leap_min`,
`forbid_tritone_leap`, `mode`, etc. A dictation stage is just a different point in
the same parameter space, ordered differently.

## The melodic ladder (major)

Diatonic indices: `0`=do, `1`=re, `2`=mi, `3`=fa, `4`=so, `5`=la, `6`=ti,
`7`=do′. Tonic triad = `{0,2,4}`. Every card primes the key firmly (cadence +
tonic + replayable audio); the tritone is excluded as a bare leap, same rule as
sight-singing.

**Phase D0 — Tonal anchoring (hear where you are).** Very short, high repetition.
- **DD1 · Tonic & the Triad Skeleton** — pool `{0,2,4}`, length 2–3, even rhythm.
  Identify the stable pitches against a firm tonal center.
- **DD2 · The Triad, Both Directions** — pool `{0,2,4,7}`, length 3–4, even.
  Arpeggio shapes up and down.

**Phase D1 — Steps enter (memory begins).**
- **DD3 · Stepwise Neighbors** — pool `{0,1,2,3,4}`, length 3–4, conjunct, even.
  The task becomes hearing *step vs. skip*.
- **DD4 · The Pentachord** — pool `{0..4}`, length 4, even, scalar.
- **DD5 · Into the Upper Scale** — pool `{0..7}` (adds 5,6), length 4, even.

**Phase D2 — Rhythm, isolated then combined.**
- **DD6 · Rhythm Alone** *(rhythm dictation)* — single repeated pitch; notate the
  **rhythm** (quarters, halves, rests, eighth pairs). Pitch is trivial so rhythm
  is the whole task. Uses the editor's existing duration toolbar + rest mode.
- **DD7 · Pitch + Simple Rhythm** — pool `{0..4}`, length 3–4, one non-even value
  (a half, an eighth pair). Combine the two now-separately-trained skills.

**Phase D3 — Length grows (chunking).**
- **DD8 · Longer Phrases, Even Rhythm** — pool `{0..7}`, length 5–6, even. Pure
  memory/chunking. (Length does the work a limited number of hearings would do in
  a classroom, since a card can always be replayed.)
- **DD9 · Longer + Rhythm** — pool `{0..7}`, length 5–6, mixed rhythm.

**Phase D4 — Hearing leaps (ordered by *audibility*, not vocal difficulty).**
- **DD10 · Thirds & the Triad** — feature 3rds/triad leaps (consonant, easiest to
  hear), length 4–5.
- **DD11 · Fourths & Fifths** — feature P4/P5 (tonal, recognizable), length 4–5.

**Phase D5 — Tendency tones by ear.**
- **DD12 · Ti Wants Do / Fa Wants Mi** — foreground the pulls; hearing resolution,
  length 4–5.
- **DD13 · Free Diatonic Dictation** — mixed intervals/rhythm, length 6.

**Minor (ND-series).** Mirror the above in la-based minor (natural minor
structural stages + a harmonic-minor leading-tone stage), exactly as the
sight-singing ladder mirrors major → minor.

## Parallel sub-tracks

- **Interval dictation** (`IVD2…IVD8`) — hear two notes, notate the interval; the
  dictation counterpart to the interval-singing drills. Cheap: reuse the interval
  stage specs, dictation card only.
- **Rhythm dictation** (`RD1…RD9`) — DD6 expanded into a full ladder paralleling
  the sight-singing Rhythm track. *(Editor dependency.)*
- **Transfer** (other keys, bass clef) — later, same as sight-singing; dictation
  in a new key/clef is a distinct and worthwhile skill.

## Editor capability (verified 2026-07-07)

The Transcribe editor **already accepts duration input**: it has a duration
toolbar (`ss-durbar`) with **whole / half / quarter / eighth** values and a
**rest** mode (`assets/_transcription.js`: `DURATION_ORDER`, `DURATION_LABELS`,
`mode: note|rest|erase`). So basic rhythm dictation — **DD6, DD7, DD9** and the
basic Rhythm-Dictation stages — is buildable **now**, no editor changes.

What the editor does **not** yet input is the *advanced* rhythmic values:
**dotted notes, ties/syncopation, and triplets** (`DURATION_ORDER` is only
`["w","h","q","8"]`). Those are needed only for the advanced Rhythm-Dictation
stages (the RD equivalents of the sight-singing R6–R9). Add them to the editor
before those specific stages; everything else is unblocked.

## Phasing

1. **Phase 1 — melodic spine, major** (DD1–DD13, incl. the basic-rhythm DD6/DD7/DD9):
   all buildable now (editor already does pitch + basic durations + rests). The
   bulk of the value.
2. **Phase 2 — minor** (ND-series).
3. **Phase 3 — interval dictation + basic rhythm dictation ladder**.
4. **Phase 4 — advanced rhythm dictation** (dotted / ties / triplets): after the
   editor's duration palette gains those values.
5. **Phase 5 — transfer** (other keys, bass clef).

## Open decisions (for review)

1. **Card-off mechanism** — conditional generation (recommended) vs. suspension.
2. **Overlap policy** — how much, if any, deliberate melody overlap with the
   sight-singing pool (default: near-zero; overlap only where you explicitly want
   a tune both ways).
3. **Tree layout** — two branches under one `Sight Singing` umbrella
   (`::Read` / `::Dictation`) vs. two separate top-level decks. Low stakes.
4. **Length-ramp aggressiveness** — how fast DD8/DD9 push to 6+ notes (this is the
   main dial that makes dictation hard; worth calibrating against your own ear in
   the study pilot).
5. **Advanced-rhythm editor work** — extend the duration palette with dotted /
   tie / triplet input now (unlocks Phase 4) or defer; Phases 1–3 don't need it.
