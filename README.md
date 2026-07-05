# Sight-Singing Deck

Code-generated Anki deck experiments for beginner sight singing.

The project started as a 10-card MVP that validates the full pipeline:

- Python generates structured melody card data.
- A slim, Bravura-only VexFlow build renders notation inside Anki cards. It and
  all card scripts are **inlined into the note-type templates** (the deck ships
  no external `.js` media), so cards render offline on Desktop, iOS, and
  AnkiDroid without depending on any platform's media server.
- Shared media assets provide playback and rendering helpers.
- `genanki` packages the result into `.apkg` files.

See [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) for the one harmless, AnkiDroid-side
"Failed to load" message and platform-support notes (share this with users when
publishing).

Current work also includes fixed-audio curriculum planning, rhythm curriculum notes, and a transcription minigame/debug harness.

## Key Files

- [`CURRICULUM.md`](CURRICULUM.md): **master curriculum design (v2)** — the
  function-first melodic ladder, parallel sing/dictation paths, minor and
  keys/clefs ladders, rhythm + merge, support system, and generation plan.
  Supersedes the older planning notes below.
- [`MVP_PLAN.md`](MVP_PLAN.md): original 10-card pipeline plan (historical)
- [`sight_singing_deck_plan.md`](sight_singing_deck_plan.md): broader deck plan (historical)
- [`FIXED_AUDIO_CURRICULUM.md`](FIXED_AUDIO_CURRICULUM.md): fixed-audio curriculum notes
- [`RHYTHM_CURRICULUM.md`](RHYTHM_CURRICULUM.md): rhythm-card curriculum notes
- [`TRANSCRIPTION_MINIGAME_DESIGN.md`](TRANSCRIPTION_MINIGAME_DESIGN.md): transcription interaction design
- [`scripts/build_deck.py`](scripts/build_deck.py): main APKG builder
- [`assets/card_styles.css`](assets/card_styles.css): single source of truth for card CSS (design tokens, Anki night-mode support); embedded into the note type at build time and linked by the debug harnesses
- [`assets/_renderer.js`](assets/_renderer.js): theme-aware VexFlow renderer (meta chips, degree chips, beaming, per-note styling)
- [`assets/_transcription.js`](assets/_transcription.js): transcription editor — VexFlow-engraved staff with a pointer overlay (ghost-note preview, drag-to-aim, erase, undo, beat progress) plus the back-side answer comparison
- [`debug/transcription-harness.html`](debug/transcription-harness.html), [`debug/review-harness.html`](debug/review-harness.html), [`debug/sing-harness.html`](debug/sing-harness.html): browser harnesses (with night-mode toggles) that reuse the deck CSS/JS directly
- [`tests/transcription-harness.spec.js`](tests/transcription-harness.spec.js): Playwright coverage for the transcription editor and review comparison

## Python Setup

```sh
uv sync --extra deck --extra dev
```

Build the main deck (the original 10-card MVP):

```sh
.venv/bin/python scripts/build_deck.py
```

Build the full generated curriculum:

```sh
.venv/bin/python scripts/build_curriculum_deck.py
# fast smoke build (first N melodies per track):
.venv/bin/python scripts/build_curriculum_deck.py --limit 5
```

Generated APKG files are written under `out/`.

## Generated Curriculum

`scripts/build_curriculum_deck.py` generates the full function-first curriculum
from constraint specs (no hand-authored melodies). The pipeline lives under
`src/sight_singing/`:

- `theory/scales.py` — diatonic-index realization (0 = tonic), keys/modes,
  movable-do solfège, fixed per-(key, clef) tonic-octave anchoring.
- `curriculum/stages.py` — stages as constraint specs. `MAJOR_STAGES`,
  `MINOR_STAGES` (natural + a harmonic-minor leading-tone stage), and
  `INTERVAL_STAGES` (isolated two-note interval drills).
- `generate/melody_gen.py` — enumerate → hard-rule filter → musicality quality
  score → contour-signature diverse sampling.
- `build/library.py` — realize stages into card-ready melody records.

The deck ships several tracks as subdecks, each split into per-stage subdecks in
curriculum order:

- **Major** (C) and **Minor** (A, the relative minor) — the melodic ladder.
  Every melody yields a **Sing** card and a **Transcribe** (dictation) card.
- **Intervals** — isolated two-note interval drills (IV2–IV8).
- **Errors** — error-detection (see below).
- **Keys · G major / F major** and **Clef · Bass (C major / A minor)** — bounded
  movable-do transfer tracks (a curated stage spread in other keys and bass clef,
  capped per stage). The renderer draws the right **key signature** and only
  marks accidentals that deviate from it; cadences are transposed per key/mode
  (a real i-iv-**V**-i in minor, with the raised leading tone).
- **Rhythm / Rhythm · Bass** — rhythm-first cards (`generate/rhythm.py`,
  `make_rhythm_model`): one bar on a single repeated pitch so the interest is
  pure timing. Stages R1–R6 cover quarters/halves/wholes, rests, beamed eighth
  pairs, mixed fillings, offbeat eighth rests, and dotted-quarter patterns.
  (Ties/triplets, R7–R9, need StaveTie/Tuplet support — a later step.)

The **Errors** track is a separate note type (`make_error_model`): you see the
written score and hear a performance with exactly one in-key wrong note, and tap
the note that sounds wrong. `generate/errors.py` alters one note of a base
melody; the back reveals the wrong note in red and grades your tap. The tap +
reveal live in `assets/_errordetect.js` (both drive the renderer's per-note
`styles` option; a defensive dep-poll bootstrap keeps it robust on iOS/Android).

**Audio clues** (buttons on the card, plus a per-side autoplay config block in
the templates): Cadence, First note, Tonic, and a sustained **Drone** (an organ
tonic held under the singing, doubled at the octave below). Melody/note/cadence/
drone clips are content-hashed so Anki's importer always picks up changes.

**Phase checkpoints / custom study:** every note is tagged `phase::<phase>`,
`stage::<id>`, `track::<track>`, and `key::<key>_<mode>`, so mixed-review
checkpoints are just saved searches, e.g.
`deck:"Sight Singing::Major" tag:phase::steps` or `tag:stage::M5 OR tag:stage::M6`.

## Transcription Debug Harness

Install JavaScript debug dependencies through Socket Firewall:

```sh
sfw npm install
```

Run the debug server from the repository root:

```sh
npm run debug:server
```

Run the Playwright transcription check:

```sh
npm run test:transcription
```

## Audio Clues

Both card templates autoplay a configurable sequence of clues. The defaults
are `["tonic"]` on the Sing front (cadence and first-note stay available as
buttons) and `["tonic", "melody"]` on the Transcribe front. To change them,
edit the clearly-marked "Audio clue configuration" script block at the top of
the card templates (available keys: `cadence`, `first`, `tonic`, `melody`).

Audio clip filenames embed a content hash (see `AUDIO_RENDER_VERSION` in
[`src/sight_singing/audio_assets.py`](src/sight_singing/audio_assets.py)):
Anki's importer never overwrites an existing media file with the same name,
so any change to a melody or to render parameters must produce a new
filename. After re-importing an updated deck, run Tools → Check Media in
Anki to delete the orphaned older clips.

## Notes

- `node_modules/`, `test-results/`, `out/`, rendered audio, and local render caches are intentionally ignored.
- The project uses `uv`'s `exclude-newer = "7 days"` policy and an npm `.npmrc` minimum release-age policy for dependency safety.
