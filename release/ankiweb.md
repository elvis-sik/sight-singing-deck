---
title: "Sight Singing — a function-first ear & reading course"
tags: sight-singing solfege ear-training music music-theory sight-reading notation rhythm dictation singing
support_url: https://github.com/elvis-sik/sight-singing-deck
---

A from-scratch course for learning to **read music by ear** — to look at a
melody and hear it, and to hear a melody and write it down. It's built around
**movable-do solfège** and ordered by **tonal function**, not by interval size:
you start with *sol–mi*, add the tonic triad, fill in stepwise motion, learn how
the tendency tones (*ti→do*, *fa→mi*) pull, and only then take on wider leaps. So
every card sits on ground the earlier ones prepared.

Nothing to configure and nothing to download: the notation engine and all audio
are **bundled in the deck**, so it renders and plays **offline on Anki Desktop,
AnkiMobile (iOS), and AnkiDroid**. Light and dark mode included.

You grade yourself — sing or clap, then flip and check — and you still press
Anki's own answer buttons, so **scheduling stays 100% Anki**.

## In Anki

![A C-major sight-singing prompt in Anki](https://raw.githubusercontent.com/elvis-sik/anki-shared-deck-assets/main/screenshots/sight-singing/sing-front.png)

![The revealed answer to the sight-singing prompt in Anki](https://raw.githubusercontent.com/elvis-sik/anki-shared-deck-assets/main/screenshots/sight-singing/sing-back.png)

## Card types

- **Sing** — read the notated melody, sing it in solfège, then flip to check
  your pitches and see each note's scale degree.
- **Take dictation** — hear a melody and **place the notes on a staff** (a
  built-in pointer editor: preview, drag-to-aim, erase, undo), then flip to see
  your answer compared note-by-note against the original.
- **Find the wrong note** — hear a performance with exactly one in-key wrong
  note and **tap the note that sounds off**; the card grades your tap and reveals
  the culprit. A fresh wrong note is chosen each review, so it stays an ear test,
  never a memory of "it's always the third one."
- **Rhythm** — read and clap a one-bar rhythm on a single pitch, so the only
  challenge is timing: pulse, rests, eighth pairs, dotted figures, syncopation
  (ties), and triplets.

Each melodic card gives you the support you choose: a **cadence** to establish
the key, the **first note**, the **tonic**, and a sustained **drone** you can
hold under your voice.

## How it's organised

Seven tracks, numbered in study order, each with a short "how to use me" note on
its deck screen:

- **1 · Core: Major** and **2 · Core: Minor** — the melodic spine (natural and
  harmonic minor, including the raised leading tone). Work these top to bottom.
- **3 · Drill: Rhythm** and **4 · Drill: Intervals** — run these alongside the
  core from day one. Intervals are isolated two-note drills, seconds through the
  octave, up and down.
- **5 · Skill: Error Detection** — the listening game above, once you can read a
  short phrase confidently.
- **6 · Transfer: Other Keys** (G and F major) and **7 · Transfer: Bass Clef**
  (C major and A minor) — the same movable-do skills in new keys and on the
  lower staff, for once C major feels fluent. Cards show the correct key
  signature and a cadence transposed to match.

Every note is **tagged by phase, stage, track, and key**, so you can carve out
your own mixed-review checkpoints with saved searches and filtered decks — see
the GitHub README for ready-made recipes.

## Source & issues

GitHub: [https://github.com/elvis-sik/sight-singing-deck](https://github.com/elvis-sik/sight-singing-deck)

The whole deck — melodies, audio, and notation — is produced by the open-source
generator in the repository above.

**One harmless note for AnkiDroid users:** Android may briefly show a *"Card
Content Error: Failed to load '…'"* message when a card opens. **You can ignore
it** — the card, notation, and audio all work. It's a known false positive in
AnkiDroid's own reviewer (Anki-Android issues #16510 and #10033), not a problem
with this deck: these cards load no external files at all. It never appears on
Desktop or iOS.
