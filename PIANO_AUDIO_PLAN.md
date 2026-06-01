# Piano Audio Plan

## Goals

- Replace the synth-like oscillator audio with piano-rendered files.
- Keep playback reliable on Anki Desktop, AnkiMobile, and AnkiDroid.
- Keep file sizes small enough that staged fixed-audio decks remain practical.
- Preserve a single source of truth for melody data so later deck variants do not fork the
  pedagogy.

## Format choice

Use **mono MP3** for shipped deck audio.

Why:

- it is the safest cross-platform choice for Anki packaging and playback,
- it compresses short piano clips well enough for this project,
- and it avoids tying the deck to Apple-only containers like `.m4a`.

Recommended encoding target for now:

- sample rate: 44.1 kHz
- channels: mono
- bitrate: 64 kbps CBR

This is conservative rather than maximally compressed. If the full deck turns out larger
than desired, we can do a later listening pass at 48 kbps mono MP3 and compare.

## Rendering pipeline

1. melody data stays in Python as scale degrees / note names
2. Python emits simple MIDI files for each support clip and melody clip
3. FluidSynth renders those MIDI files offline through a piano-capable SoundFont
4. temporary WAV output is transcoded to MP3 with `afconvert`
5. the deck packages only the final MP3 assets

Current local renderer choice for the sample deck:

- renderer: FluidSynth
- soundfont: `GeneralUser-GS.sf2`
- instrument: General MIDI Acoustic Grand Piano

I originally tried Apple’s built-in DLS route, but the needed sampler component is not
available in this command-line environment, so the practical implementation path is
FluidSynth plus a local SoundFont. The SoundFont is a build-time asset only and does not
ship inside the Anki deck.

## Clip design

### Melody clips

- one rendered piano clip per melody
- quarter-note grid remains fixed
- slight articulation gap between notes so pitch boundaries stay clear

### Support-note clips

- one piano clip per note name used as tonic or first-note support
- short and direct
- no extra flourish

### Cadence clips

Cadence clips should be **blocked chords**, not single-note arpeggios.

For the C-major sample deck:

- I: C-E-G
- IV: F-A-C
- V: G-B-D
- I: C-E-G

For later minor-mode decks, use separate pre-rendered minor cadences instead of stretching
 the major cadence logic.

## Full-deck topology

The full project should not be shipped as one giant all-variants deck.

Instead, use separate products:

- **Treble-first deck**
- **Bass-first deck**
- optionally a **combined / advanced deck** later if it proves useful

### Treble-first deck

Main path:

- Stages 1-9 in treble clef
- C major and A natural minor throughout

Bridge at the end:

- a short **bass transfer stage**

The bass transfer stage should include:

- a tiny sampler from earlier bass stages
- enough cards to introduce bass clef decoding gently
- then a denser final group using the full version-1 interval vocabulary in bass clef

That means the learner finishes treble, then gets:

- quick orientation to bass,
- a small taste of the earlier bass material,
- and then a meaningful bass stage that feels like transfer, not a full second beginner
  curriculum.

### Bass-first deck

Mirror the same idea in reverse:

- Stages 1-9 in bass clef
- short treble transfer stage at the end

## Recommended clip budgeting

For a learner-facing deck, do not mirror every canonical melody into every release.

Instead:

- define a canonical melody library centrally,
- choose a subset per published deck,
- and keep the transfer stage intentionally small.

This avoids shipping all possible rendered clips to every learner.

## Immediate implementation target

For the current sample deck:

- keep the 10 existing Stage 1 treble / C-major melodies
- swap all support and melody audio to piano MP3
- use a chordal cadence
- measure actual audio footprint

That measured footprint is then the baseline for forecasting:

- stage bundles,
- treble-only deck size,
- bass-only deck size,
- and treble-plus-bass-transfer deck size.
