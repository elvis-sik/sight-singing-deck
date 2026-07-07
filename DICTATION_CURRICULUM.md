# Dictation Curriculum (design of record)

A curriculum for **melodic dictation** (hear it → notate it) as a skill in its
**own right**, with its own difficulty ordering and its own melody pool — not the
sight-singing melodies run backwards.

This supersedes the "dictation reuses the sight-singing material" stance in
[`CURRICULUM.md`](CURRICULUM.md). Sight-singing stays as designed; this document
covers only the parallel dictation path.

> Status: **draft for review** (rev. 2 — incorporates the design-review pass: a
> listen-count grading mechanic, a compressed D0, and pure rhythm moved out of the
> melodic spine into the RD sub-track). Nothing here is built yet; the ladder is a
> proposal to react to before it is encoded into `curriculum/stages.py`.

## Why a separate curriculum

Dictation and sight-singing are the two directions of one skill (audiation), but
they are **gated by different things**, so the optimal ordering diverges:

| Axis | Sight-singing difficulty | Dictation difficulty |
|---|---|---|
| Vocal production / pitching a leap | **primary** | irrelevant (you're not singing) |
| Range / tessitura | matters | irrelevant |
| **Phrase length / working memory** | minor | **primary** — the core dictation skill |
| **Rhythmic complexity** | a separate track; melodies stay even | **primary**; isolated in its own RD track, then integrated |
| **Hearings available** | n/a (you read at your own pace) | **the hidden axis** — free replay must be countered (see below) |
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

## The listen-count mechanic

Free replay is the trap of self-study dictation: a 6-note phrase you can replay
forever stops being a memory test — you peck it out two notes at a time across
five hearings. Real dictation skill is extracting *more per hearing*, which is
exactly why classroom dictation caps you at 3–4 playings. So the dictation card
**counts plays and shows the count** ("Listens: 3"), and the **self-grade rubric
is built around the count**, not around whether you eventually assembled the right
notes:

- correct in **≤2 listens → Good / Easy**
- needed **3–4 listens → Hard**
- **more than 4, or wrong → Again**

This restores the scarcity that gives the length ramp (DD6–DD7) its meaning;
without it the ramp measures patience, not audiation. Implementation is small: a
play counter on the Transcribe front's melody button plus a rubric reminder on the
back — no editor change. It applies to every dictation stage.

## The melodic ladder (major)

Diatonic indices: `0`=do, `1`=re, `2`=mi, `3`=fa, `4`=so, `5`=la, `6`=ti,
`7`=do′. Tonic triad = `{0,2,4}`. Every card primes the key firmly (cadence +
tonic + replayable audio); the tritone is excluded as a bare leap, same rule as
sight-singing.

**Phase D0 — Tonal anchoring (one short stage).** With cadence + tonic priming and
free replay this is nearly free in-medium, so it's deliberately brief — a few days,
not a runway. (Singing needed a long on-ramp for production nerves; dictation
doesn't.)
- **DD1 · The Triad Skeleton** — pool `{0,2,4,7}`, length 2–4, both directions,
  even rhythm. Identify the stable pitches against a firm tonal center.

**Phase D1 — Steps enter (the real start: step-vs-skip discrimination).**
- **DD2 · Stepwise Neighbors** — pool `{0,1,2,3,4}`, length 3–4, conjunct, even.
- **DD3 · The Pentachord** — pool `{0..4}`, length 4, even, scalar.
- **DD4 · Into the Upper Scale** — pool `{0..7}` (adds 5,6), length 4, even.

**Phase D2 — Pitch + rhythm, integrated.** (Pure rhythm-alone dictation lives in
the RD sub-track, not here — see *Parallel sub-tracks*.)
- **DD5 · Pitch + Simple Rhythm** — pool `{0..4}`, length 3–4, one non-even value
  (a half, an eighth pair). Integrate pitch with rhythm trained separately in RD.

**Phase D3 — Length grows (chunking — the core dictation skill).**
- **DD6 · Longer Phrases, Even Rhythm** — pool `{0..7}`, length 5–6, even. Pure
  memory/chunking; the listen-count mechanic above is what keeps this honest.
- **DD7 · Longer + Rhythm** — pool `{0..7}`, length 5–6, mixed rhythm.

**Phase D4 — Hearing leaps (ordered by *audibility*, not vocal difficulty).**
- **DD8 · Thirds & the Triad** — feature 3rds/triad leaps, length 4–5.
- **DD9 · Fourths & Fifths** — feature P4/P5 (no tritone), length 4–5.

  *Why triads before 4ths/5ths here:* every card is cadence-primed, so this is a
  *functional* judgement — in a movable-do context do–mi–so leaps are the easiest
  to identify by function, even though as bare isolated intervals P4/P5 are the
  more recognizable anchors. The priming makes the triadic-first order correct for
  this deck specifically.

**Phase D5 — Tendency tones, then free.**
- **DD10 · Ti Wants Do / Fa Wants Mi** — foreground the pulls; hearing resolution,
  length 4–5.
- **DD11 · Free Diatonic Dictation** — mixed intervals/rhythm, length 6.

**Minor (ND-series).** Mirror the above in la-based minor (natural minor
structural stages + a harmonic-minor leading-tone stage), exactly as the
sight-singing ladder mirrors major → minor.

## Producing the exercises (generation, not hand-authoring)

Each stage's melodies are **generated** from its spec by the existing engine
(`generate/melody_gen.py`: enumerate under the pool / step / required-tone rules →
hard-rule filter → musicality score → diversity sample), exactly as the
sight-singing stages are. So "designing a stage" means writing and **tuning its
`Stage` spec**, then generating and curating the output — not authoring melodies by
hand. This still involves real design work in two places:

- **Per-stage tuning.** Specs routinely need adjustment for *yield* (a too-tight
  spec collapses to a handful — the sight-singing M0_2 / M6 / M8 stages all needed
  this) and for *quality* (a loose stepwise spec produces dull repeated-note
  noodling — a draft DD2 gave `do-do-re-do`, `do-re-do-do`). Expect a tune pass per
  stage, likely including a dictation-appropriate **diversity rule** (penalise
  excessive repeated notes; reward scale coverage). This is the bulk of the
  encoding effort.
- **New generation logic for the rhythmic stages.** The current melodic generator
  produces **even** (all-quarter) melodies only; rhythm lives solely in the
  single-pitch Rhythm generator. DD5 and DD7 ("pitch + rhythm") require *combining*
  a pitched contour with a rhythmic pattern — new code (pair a generated contour
  with a generated rhythm bar, or teach the melodic generator to assign durations).
  Until it exists, DD5 / DD7 can't be generated; DD1–DD4, DD6, DD8–DD11 can today.

## Parallel sub-tracks

- **Interval dictation** (`IVD2…IVD8`) — hear two notes, notate the interval. **The
  first note is shown on the staff; you place only the second**, so the task is
  "hear the interval," not "guess the starting position." Dictation counterpart to
  the interval-singing drills; reuse the interval stage specs, dictation card only.
- **Rhythm dictation** (`RD1…RD9`) — the **sole home** for pure rhythm-on-one-pitch
  dictation (kept out of the melodic spine to avoid duplication): single repeated
  pitch, notate the rhythm. A full ladder paralleling the sight-singing Rhythm
  track. Start it **in parallel** with the melodic spine (around DD5) so rhythm is
  trained on its own before DD5/DD7 ask you to integrate it. Basic values use the
  editor's existing duration toolbar + rest mode; the advanced values need editor
  work (see below).
- **Transfer** (other keys, bass clef) — later, same as sight-singing; dictation
  in a new key/clef is a distinct and worthwhile skill.

## Editor capability (verified 2026-07-07)

The Transcribe editor **already accepts duration input**: it has a duration
toolbar (`ss-durbar`) with **whole / half / quarter / eighth** values and a
**rest** mode (`assets/_transcription.js`: `DURATION_ORDER`, `DURATION_LABELS`,
`mode: note|rest|erase`). So basic rhythm dictation — the integrated **DD5 / DD7**
and the basic **RD** stages — is buildable **now**, no editor changes.

What the editor does **not** yet input is the *advanced* rhythmic values:
**dotted notes, ties/syncopation, and triplets** (`DURATION_ORDER` is only
`["w","h","q","8"]`). Those are needed only for the advanced Rhythm-Dictation
stages (the RD equivalents of the sight-singing R6–R9). Add them to the editor
before those specific stages; everything else is unblocked.

## Phasing

1. **Phase 1 — melodic spine, major** (DD1–DD11) **plus the listen-count mechanic**
   on the Transcribe card. All buildable now (editor already does pitch + basic
   durations + rests). The bulk of the value.
2. **Phase 2 — minor** (ND-series).
3. **Phase 3 — interval dictation + the basic Rhythm-Dictation ladder** (RD, basic
   values). RD is independent and can be practised earlier, but this is when it's
   built out.
4. **Phase 4 — advanced rhythm dictation** (dotted / ties / triplets): after the
   editor's duration palette gains those values.
5. **Phase 5 — transfer** (other keys, bass clef).

## Open decisions (for review)

1. **Card-off mechanism** — conditional generation (recommended) vs. suspension.
2. **Overlap policy** — how much, if any, deliberate melody overlap with the
   sight-singing pool (default: near-zero; overlap only where you explicitly want
   a tune both ways).
3. **Tree layout** — **Decided (2026-07-07): `Dictation` is its own top-level
   tree**, parallel to `Sight Singing`, with its own numbered tracks.
4. **Difficulty dials** — how fast DD6/DD7 push toward 6+ notes, and the
   **listen-count rubric thresholds** (≤2 / 3–4 / >4 proposed). These are the two
   main knobs that set dictation difficulty; both worth calibrating against your
   own ear in the study pilot.
5. **Advanced-rhythm editor work** — extend the duration palette with dotted /
   tie / triplet input now (unlocks Phase 4) or defer; Phases 1–3 don't need it.
