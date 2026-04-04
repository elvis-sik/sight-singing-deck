# Sight-Singing Anki Deck Project Plan

## 1. Overview

This project aims to create a code-generated Anki deck for beginner sight singing.

The deck is designed to train a learner to look at a very simple notated melody, establish the tonal center, and sing the melody accurately relative to that tonal center. The project is intentionally narrow in scope at first. It does **not** attempt to teach rhythm, chromaticism, modulation, harmonic minor, melodic minor, or advanced notation. Instead, it focuses on a single core skill:

> reading very simple diatonic melodies and singing them accurately in a stable tonal context.

The deck will be generated programmatically rather than built card by card. This makes it possible to:

- produce a large universe of cards cheaply,
- organize them into pedagogically meaningful stages,
- mirror the same curriculum across treble and bass clefs,
- avoid storing per-card media files,
- and eventually support more advanced extensions without redesigning the entire system.

The current design assumes that notation and audio will ideally be rendered dynamically on the Anki card using JavaScript and shared assets, rather than by storing one image and one audio file for every note sequence.

---

## 2. Project goals

### 2.1 Immediate goal

Build a first-pass curriculum that covers:

- **C major** and **A natural minor** only,
- **no chromatics**,
- **no ledger lines**,
- **no rhythmic complexity**,
- **4 quarter notes in 4/4**,
- **short melodies only**,
- **diatonic sight singing with tonal support**.

### 2.2 What the learner should practice

For each card, the learner should be able to:

1. identify the tonal center,
2. orient themselves from a provided auditory reference,
3. decode the notes on the staff,
4. sing the melody using scale-degree awareness,
5. gradually rely less on support as fluency improves.

### 2.3 What this project is **not** doing yet

The first version deliberately excludes:

- harmonic minor,
- melodic minor,
- chromatic notes,
- rhythm drills,
- rests,
- dotted rhythms,
- ties,
- syncopation,
- melodies longer than four notes,
- ledger lines,
- multi-voice or harmonic tasks.

This is a pitch-reading and tonal-orientation deck first.

---

## 3. High-level pedagogical decisions

### 3.1 Tonal support

Each card should expose **three auditory support options**:

- **Cadence**
- **First note**
- **Tonic**

The learner should be able to play any of these manually as many times as desired.

In addition, there should be a deck- or template-level setting controlling what plays by default when the card is shown. A likely early configuration is:

- early stages: default = cadence + first note,
- intermediate stages: default = first note,
- later stages: default = nothing.

The tonic should remain available as a manual support button even when it is not part of the default playback.

### 3.2 Clefs

The full curriculum should be generated in **both treble and bass clefs**.

However, the learner does **not** need to study both clefs in parallel. The deck should be organized so that:

- a learner can start with treble only,
- later add bass,
- or study both in parallel if desired.

Treble should be treated as the default first path for most learners, but the generated deck should support both equally.

### 3.3 Scope of difficulty

Even with the narrow scope above, difficulty is not determined only by interval size. Important dimensions include:

- allowed intervals,
- starting degree,
- ending degree,
- contour,
- number and placement of skips,
- recovery after larger leaps,
- note repetition,
- clef decoding.

This means the generator must do more than randomly sample note sequences from a scale.

---

## 4. Fixed global constraints for version 1

These constraints apply throughout the first full pass of the curriculum.

- **Keys / modes**: C major and A natural minor only
- **Clefs**: treble and bass
- **Range**: no ledger lines
- **Rhythm**: 4 quarter notes in 4/4
- **Melody length**: 4 notes
- **Accidentals**: none
- **Chromaticism**: none
- **Minor type**: natural minor only
- **Audio supports**: cadence, first note, tonic
- **Goal**: sing accurately in scale degrees relative to the tonal center

---

## 5. Curriculum structure

The curriculum should be organized primarily by **stage**. Each stage defines a constrained melody-generation problem. The same stage can then be mirrored across:

- treble clef,
- bass clef,
- C major,
- A natural minor.

That means the curriculum is conceptually one track, but implementation-wise it expands into multiple mirrored subdecks or tag groups.

### 5.1 Stage design philosophy

The stages should move from:

- easier interval vocabularies,
- more stable starting/ending degrees,
- more predictable contours,
- fewer or smaller skips,

into:

- broader interval vocabularies,
- freer launching and landing points,
- more varied contours,
- wider but still controlled diatonic motion.

The goal is **not** to enumerate all mathematical combinations of allowed intervals. Instead, the goal is to define stages that make musical and pedagogical sense.

---

## 6. Core curriculum stages

## Stage 1 — Neighbor patterns

**Purpose:** establish tonal orientation and staff decoding with minimal melodic movement.

**Allowed adjacent intervals:**
- unison
- second

**Start degree:**
- 1, 3, or 5 only

**End degree:**
- 1, 3, or 5 only

**Contour bias:**
- mostly neighbor motion
- small returns
- local motion around stable tones

**Musical character:**
- highly stable
- almost no launch ambiguity
- suitable for the first contact with the deck

**Notes:**
A limited number of highly repetitive melodies may be acceptable here if they are pedagogically useful.

---

## Stage 2 — Stepwise melodies with stable launch

**Purpose:** introduce all scale degrees while preserving stepwise motion.

**Allowed adjacent intervals:**
- unison
- second

**Start degree:**
- 1, 3, or 5 only

**End degree:**
- 1, 3, or 5 only

**Internal notes:**
- any scale degree in the mode

**Musical character:**
- all seven degrees can now appear
- still no skips
- learner gets used to 2, 4, 6, and 7 as destinations and passing tones

---

## Stage 3 — Fully stepwise

**Purpose:** remove the stable-start training wheels while keeping the pitch vocabulary stepwise.

**Allowed adjacent intervals:**
- unison
- second

**Start degree:**
- any degree

**End degree:**
- any degree, but still somewhat biased toward stable degrees for card quality

**Musical character:**
- stepwise melodies across the full allowed no-ledger-line range
- full practice of all scale degrees without skips

---

## Stage 4 — First skips

**Purpose:** introduce thirds in a highly controlled way.

**Allowed adjacent intervals:**
- unison
- second
- third

**Start degree:**
- 1, 3, or 5 only

**End degree:**
- 1, 3, or 5 only

**Restrictions:**
- at most one third per melody
- the rest of the melody should remain mostly stepwise

**Musical character:**
- first real leap
- small increase in difficulty
- still strongly tonally anchored

---

## Stage 5 — Thirds integrated

**Purpose:** make thirds part of the ordinary melodic vocabulary.

**Allowed adjacent intervals:**
- unison
- second
- third

**Start degree:**
- any degree

**End degree:**
- any degree

**Restrictions:**
- avoid multiple skips in immediate succession unless there is strong musical justification
- no leap-heavy nonsense

**Musical character:**
- small skips become normal
- melodies should still feel singable and beginner-friendly

---

## Stage 6 — Fourths introduced

**Purpose:** add larger structural leaps in a controlled way.

**Allowed adjacent intervals:**
- unison
- second
- third
- fourth

**Start degree:**
- 1, 3, or 5 only

**End degree:**
- 1 or 5 preferred

**Restrictions:**
- at most one fourth per melody
- after a fourth, prefer stepwise recovery in the opposite direction

**Musical character:**
- larger leap vocabulary begins
- stability still preserved through start/end constraints

---

## Stage 7 — Fourths integrated

**Purpose:** make fourths part of the normal melodic vocabulary.

**Allowed adjacent intervals:**
- unison
- second
- third
- fourth

**Start degree:**
- any degree

**End degree:**
- any degree

**Restrictions:**
- keep leap-recovery rules
- continue excluding awkward leap sequences

**Musical character:**
- broader interval fluency
- still clearly beginner material

---

## Stage 8 — Fifths introduced

**Purpose:** introduce the widest leap allowed in version 1.

**Allowed adjacent intervals:**
- unison
- second
- third
- fourth
- fifth

**Start degree:**
- 1, 3, or 5 only

**End degree:**
- 1 or 5 preferred

**Restrictions:**
- at most one fifth per melody
- after a fifth, strongly prefer recovery by step in the opposite direction

**Musical character:**
- most structurally demanding stage so far
- should still feel like controlled beginner melodies, not random interval drills

---

## Stage 9 — Full version 1 vocabulary

**Purpose:** allow unrestricted diatonic beginner melodies within the version 1 envelope.

**Allowed adjacent intervals:**
- unison
- second
- third
- fourth
- fifth

**Start degree:**
- any degree

**End degree:**
- any degree

**Restrictions:**
- continue enforcing musicality rules
- forbid ugly or arbitrary sequences that are technically legal but pedagogically poor

**Musical character:**
- free beginner-level diatonic melodies
- final stage before any future expansion into rhythm, ledger lines, or chromatic material

---

## 7. Optional side decks / diagnostic decks

These are not part of the core path, but may be useful.

### 7.1 Thirds-only diagnostic

**Allowed intervals:**
- unison
- third

**Purpose:**
check whether the learner has actually internalized thirds without relying on stepwise scaffolding.

### 7.2 Wide-skip diagnostic

**Allowed intervals:**
- unison
- fourth
- fifth

or possibly a more conservative variation such as:

- unison
- second
- fourth
- fifth

**Purpose:**
isolate larger skips for reinforcement without making them part of the core progression.

---

## 8. Melody-quality rules for the generator

These rules are crucial. Without them, a random generator will create many sequences that are technically legal but musically poor, repetitive, awkward, or pedagogically useless.

### 8.1 General rules

Suggested default rules:

- avoid three identical notes in a row,
- avoid excessive local zig-zagging unless the stage is explicitly practicing neighbor motion,
- avoid large interval sequences with no recovery,
- prefer melodies that begin and end on more stable tones in earlier stages,
- cap the number of skips depending on stage,
- require recovery after larger skips,
- avoid contours that feel like random walk noise,
- keep the overall ambitus musically reasonable.

### 8.2 Early-stage rules

In earlier stages:

- bias starting notes toward 1, 3, or 5,
- bias ending notes toward 1, 3, or 5,
- strongly limit leaps,
- prefer neighbor patterns and short arches,
- allow a small amount of repetition only if it is clearly useful.

### 8.3 Later-stage rules

In later stages:

- relax start/end constraints,
- allow more contour variety,
- allow more skips,
- still enforce recovery after fourths and fifths,
- still avoid ugly sequences that are formally valid but musically poor.

### 8.4 Example contour families

The generator may benefit from explicitly modeling simple contour families such as:

- neighbor return: up, down
- small arch: up, up, down
- descent with recovery
- tonic departure and return
- stepwise line with one embedded skip

This may produce better decks than pure random filtering.

---

## 9. Sampling strategy

The generator may be able to produce very large numbers of melodies within a stage, but the learner does **not** need to study them all.

The intended use is:

- generate a large universe,
- partition it into meaningful buckets,
- sample a relatively small number from each bucket,
- move on once fluency is established.

This suggests supporting both:

- **exhaustive generation**, for analysis and debugging,
- **sampled generation**, for real deck building.

For example, a learner might study only 10–20 cards from a stage variant before proceeding.

---

## 10. Counting and combinatorics

The raw combinatorics can become large even under strict constraints. But because this project does not require storing per-card media, that is not a major storage problem.

The real bottleneck is not file size; it is:

- pedagogical quality,
- redundancy,
- and meaningful stage organization.

That means the generator should prioritize **good card selection**, not mere completeness.

---

## 11. Implementation concept

## 11.1 Core idea

The Python package should generate **structured card data**, not rendered media.

Each card should store compact information such as:

- clef,
- key,
- mode,
- stage,
- note sequence,
- durations,
- scale degrees,
- support settings,
- and any tags or metadata needed for Anki organization.

The card template should then use JavaScript to:

- render the staff notation dynamically,
- and synthesize the audio dynamically.

This avoids storing one image and one audio file per card.

### 11.2 Why this is attractive

Benefits include:

- small deck size,
- one source of truth for notation and audio,
- easier iteration,
- easier curriculum expansion,
- and support for future card-side interaction tricks.

---

## 12. Tentative front-end rendering approach inside Anki

A plausible design is:

- use a JavaScript notation library such as **VexFlow** for drawing notation,
- use **Web Audio API** directly or a light wrapper such as **Tone.js** for playback,
- bundle the required JS files as shared media assets in the note type or deck package.

The exact card template would parse a JSON payload stored in a field, then:

1. draw the melody staff,
2. expose playback buttons,
3. optionally honor deck-level or note-level settings for default support playback.

This remains a design hypothesis until tested across Anki clients.

### 12.1 Caution

JavaScript on Anki cards is possible, but behavior can vary across Anki clients. Audio autoplay may also be limited by browser or webview restrictions. Therefore, this part of the implementation should be treated as experimental until validated on the target clients.

The safest assumption is:

- manual playback buttons are necessary,
- automatic playback may or may not be reliable everywhere,
- iteration and testing will be required.

---

## 13. Proposed card payload schema

A compact JSON payload might look like this:

```json
{
  "stage_id": "treble_stage_4_c_major",
  "clef": "treble",
  "key": "C",
  "mode": "major",
  "time_sig": "4/4",
  "notes": ["C4", "D4", "F4", "E4"],
  "durations": ["q", "q", "q", "q"],
  "degrees": [1, 2, 4, 3],
  "supports": {
    "tonic": "C4",
    "first_note": "C4",
    "cadence": ["I", "IV", "V", "I"]
  },
  "tags": ["stage4", "treble", "major"]
}
```

This is only illustrative. The exact representation may change.

---

## 14. Proposed Python package structure

A first rough package layout could be:

```text
sight_singing_deck/
  curriculum.py
  ranges.py
  intervals.py
  melody_generator.py
  quality_rules.py
  sampler.py
  serialize.py
  anki_model.py
  build_deck.py
  assets/
    _vexflow.js
    _renderer.js
    _player.js
    _tone.js
```

### 14.1 Responsibilities

- `curriculum.py`  
  Define stages and stage-specific constraints.

- `ranges.py`  
  Represent allowed note ranges for treble and bass without ledger lines.

- `intervals.py`  
  Encode interval logic in scale degrees and staff pitches.

- `melody_generator.py`  
  Generate candidate melodies subject to stage constraints.

- `quality_rules.py`  
  Apply musicality filters and ranking heuristics.

- `sampler.py`  
  Sample representative melodies from a large candidate pool.

- `serialize.py`  
  Convert internal melody objects into JSON/card payloads.

- `anki_model.py`  
  Define note fields, templates, styling, and embedded assets.

- `build_deck.py`  
  Assemble the final deck package.

---

## 15. Proposed generation pipeline

A clean generation pipeline might look like this:

1. **Select a stage**  
   Load the stage constraints.

2. **Select clef + mode**  
   Example: treble + C major.

3. **Generate candidate degree sequences**  
   Respect stage interval rules, start/end rules, and other hard constraints.

4. **Map degrees to actual staff notes**  
   Ensure the melody fits inside the no-ledger-line range.

5. **Filter for quality**  
   Remove ugly, redundant, or unhelpful sequences.

6. **Deduplicate or cluster**  
   Avoid near-identical cards.

7. **Sample final cards**  
   Keep only a small representative set if desired.

8. **Serialize payloads**  
   Build compact JSON/text fields for Anki.

9. **Package the deck**  
   Include the note type, templates, CSS, and shared JS assets.

---

## 16. Card template behavior

A likely front-side experience:

- show the notated melody,
- show playback controls,
- optionally trigger default support playback,
- ask the learner to sing the melody.

A likely back-side experience:

- optionally replay the melody,
- show scale degrees,
- optionally show note names,
- optionally show interval pattern,
- possibly show self-check hints or expected contour.

The exact answer-side design is still open and should be decided after seeing the first prototype.

---

## 17. Open implementation questions

These questions remain unresolved until prototyping begins.

### 17.1 Anki client compatibility

- Does the chosen JS rendering approach work reliably on desktop?
- Does it also work on AnkiMobile and AnkiDroid?
- Is default playback reliable, or should playback remain fully manual?

### 17.2 Audio representation

- Should support audio be synthesized entirely in-browser?
- Should the cadence be encoded as symbolic harmonic information or literal pitches?
- Should the first note and tonic be rendered using the same synthesis path as the melody?

### 17.3 Melody selection

- Should melodies be generated by random search plus filtering?
- Or should the generator explicitly enumerate contour archetypes first?
- How aggressive should deduplication be?

### 17.4 Range definition

- What exactly counts as “no ledger lines” in each clef for the final implementation?
- Should the allowed range be the full staff or a slightly narrower staff-only region in early stages?

### 17.5 Stage card counts

- How many cards should each stage actually include?
- Should there be a fixed number per stage or per mode-clef-stage combination?

---

## 18. Reasonable first implementation target

A pragmatic first milestone would be:

- implement **one note type**,
- implement **one clef** first (likely treble),
- implement **one or two early stages**,
- use **C major only** at first for smoke testing,
- render notation dynamically,
- provide manual playback buttons,
- confirm that the deck works in the target Anki environment.

Then expand in this order:

1. add A natural minor,
2. add more stages,
3. add bass clef,
4. improve default playback logic,
5. improve melody selection quality,
6. package the first real usable deck.

This is likely better than trying to implement the entire curriculum at once.

---

## 19. Recommended development strategy

### Step 1
Define the curriculum as machine-readable stage configs.

### Step 2
Implement melody generation in scale degrees only.

### Step 3
Map scale degrees to notes on staff.

### Step 4
Create a minimal Anki note type with a JSON field.

### Step 5
Test dynamic rendering and manual playback in Anki.

### Step 6
Iterate on UI, filtering rules, and stage quality.

### Step 7
Generate a first small deck and study with it.

### Step 8
Refine based on actual learner friction.

---

## 20. Summary

This project now has a coherent first-pass design.

### The core idea
A code-generated Anki deck for beginner sight singing that focuses on:

- C major and A natural minor,
- no chromatics,
- no ledger lines,
- no rhythm complexity,
- 4-note diatonic melodies,
- tonal support through cadence, first note, and tonic.

### The curriculum
A 9-stage progression that expands interval vocabulary and loosens start/end constraints while preserving musicality.

### The implementation idea
Store structured text/JSON only; render notation and audio dynamically with shared JavaScript assets inside Anki.

### The main risk
The curriculum itself is clear, but the dynamic card implementation must be validated experimentally across Anki clients.

### The likely next concrete step
Write the stage definitions as code and prototype a minimal end-to-end card.

