# The Sight-Singing & Ear-Training Curriculum (v2)

> This is the master curriculum design. It supersedes and unifies the earlier
> planning notes (`sight_singing_deck_plan.md`, `MVP_PLAN.md`,
> `FIXED_AUDIO_CURRICULUM.md`, `RHYTHM_CURRICULUM.md`), which remain as
> historical inputs. Where they conflict, this document wins.

The goal is not "a deck of melodies." The goal is a **complete beginner
ear-training system** that builds *tonal audiation* — the ability to hear music
in your head from notation, and to write down music you hear — through two
inverse skills that reinforce each other:

- **Reading → producing** (sight-singing, rhythm reading)
- **Hearing → notating** (melodic dictation, rhythm dictation)

Everything below is designed to be **generated programmatically** from compact
scale-degree data, rendered to **fixed audio** (we learned the hard way that
in-webview synthesis is not reliable across Anki clients), and packaged into
focused, finite, sampled decks.

---

## Part I — Design philosophy

### 1. Function before interval size

The single most important pedagogical decision, and the biggest change from the
old plan. Difficulty in tonal music is **not** ordered by interval size. A leap
within the tonic triad (do→mi, do→sol) is *easier* for a beginner than a step
to an unstable tendency tone (mi→fa, ti→do), because the triad is the harmonic
skeleton the ear already wants to hear. Real methods (Kodály, most collegiate
aural-skills sequences) teach in roughly this order:

1. **so–mi** (the universal first interval)
2. **so–mi–la**
3. **do–mi–so** (the tonic triad — leaps, but *easy* leaps)
4. **do–re–mi** (first true steps)
5. the rest of the scale, then tendency tones, then wider leaps.

So this curriculum is ordered by **tonal function**, not by span. Steps to
`fa` and `ti` are treated as their own skill (tendency tones), *after* triad
leaps, not before them.

### 2. Two inverse skills, cross-reinforcing

Every melodic idea generates (at least) two cards from one piece of data:

- a **Sing** card: see notation → establish tonic → sing it,
- a **Dictate** card: hear it → notate it on the interactive staff (we already
  built the transcription editor for exactly this).

Dictation is the inverse of sight-singing and roughly *doubles the pedagogical
value of every melody at near-zero design cost*. They are separate study paths
(you can do one, the other, or both) that share one melody library.

### 3. Movable-do solfège as the mental model

We teach **movable-do** (the tonal center is always `do` in major, `la` in
minor — "la-based minor"). This is the system that makes relationships
transferable across keys, which is the whole point of ear training. The answer
side always shows solfège; scale-degree numbers and note names are secondary
aids.

| Degree | Major (do-based) | Minor (la-based) |
|--:|:--|:--|
| tonic | do | la |
| 2 | re | ti |
| 3 | mi | do |
| 4 | fa | re |
| 5 | so | mi |
| 6 | la | fa |
| 7 | ti (leading tone) | so (subtonic, natural minor) |

> Chromatic/raised syllables (`di ri fi si li`, `ra me se le te`) are reserved
> for future chromatic and harmonic/melodic-minor material. The generator
> should carry a `solfege_system` flag so a do-based-minor variant can be
> produced later if a learner prefers it.

### 4. Difficulty is a set of independent dials, not one line

A "stage" is a coordinate in a space of independent axes. This is what lets us
generate an enormous, well-organized universe from a small rule set, and lets a
learner combine axes deliberately (leaping melody? keep the rhythm plain).

| Dial | Values (easy → hard) |
|---|---|
| **Pitch vocabulary** | so–mi → triad → diatonic steps → tendency tones → 4ths → 5ths/6ths → free |
| **Rhythm vocabulary** | quarters → +halves/wholes → +rests → +eighth pairs → +offbeats → +dotted → +ties → +triplets → +compound meter |
| **Phrase length** | 4 notes → 6 → 8 → two-bar phrase |
| **Tonal support** | cadence+first note → first note → tonic drone → nothing |
| **Key** | C/Am → G/Em → F/Dm → D/Bm → Bb/Gm → … (one accidental at a time) |
| **Clef** | treble → bass → grand staff → (alto, advanced) |
| **Mode** | major / natural minor → harmonic minor → church modes (advanced) |
| **Skill** | Sing / Dictate / Rhythm-read / Rhythm-dictate / Merge / Diagnostics |

### 5. Finite, curated, sampled — never a raw cross-product

The full cross-product of these dials is astronomically large and mostly bad
music. The generator produces melodies from **named contour families** with
per-stage quotas, filters them through **musicality rules**, deduplicates, and
**samples** a study-sized set. Learners never need to clear a whole stage.

---

## Part II — The paths (deck families)

Ship each as its own deck so no single deck is overwhelming, and so a learner
can pick a lane. They share the melody/rhythm library underneath.

| Path | Card type | What it trains |
|---|---|---|
| **A. Melody — Sing** | Sing | see notation → sing in tune, tonally oriented |
| **B. Melody — Dictate** | Transcribe | hear melody → notate pitches + rhythm |
| **C. Rhythm — Read** | Sing (rhythm) | read/clap/tap a rhythm on one pitch |
| **D. Rhythm — Dictate** | Transcribe (rhythm) | hear rhythm → notate it |
| **E. Merge — Sing** | Sing | pitch + rhythm together |
| **F. Merge — Dictate** | Transcribe | full melodic dictation (pitch + rhythm) |
| **G. Keys & Clefs** | Sing/Transcribe | transposition + bass clef + grand staff |
| **H. Diagnostics** | mixed | interval isolation, tendency-tone drills, error-detection, checkpoints |

Recommended learner journeys are documented in Part VIII.

---

## Part III — The melodic ladder (major, C major first)

Reordered around tonal function. Each stage lists pitch vocabulary, launch/land
constraints, and its headline families. Counts are canonical melodies (before
mirroring to minor/keys/clef); "advance after" is a study guideline, not a gate.

### Phase 0 — Tonal foundation (the triad core)

| Stage | Name | Pitch set | Idea |
|---|---|---|---|
| **M0.1** | So–Mi | 3,5 | the first interval; up/down, hold, return |
| **M0.2** | So–Mi–La | 3,5,6 | add la above so; the "children's chant" set |
| **M0.3** | The Triad Anchors | 1,3,5 | do–mi–so as leaps — *easy leaps*, the skeleton |
| **M0.4** | Lower Tetrachord | 1,2,3 | first true steps, do–re–mi |

Families: `so_mi_call`, `so_mi_la_turn`, `triad_ascend`, `triad_descend`,
`triad_arpeggio_return`, `do_re_mi_climb`, `mi_re_do_settle`.

### Phase 1 — Diatonic steps, triad-anchored

| Stage | Name | Pitch set | Launch/land | Idea |
|---|---|---|---|---|
| **M1** | Stepwise around anchors | 1–5 stepwise | start/end 1,3,5 | fill the low pentachord by step |
| **M2** | The Whole Scale | 1–7 stepwise | start/end 1,3,5 | 6 and 7 appear as passing tones |
| **M3** | Ti Wants Do / Fa Wants Mi | 1–7 stepwise | must resolve tendency tones | **tendency tones as the lesson** |
| **M4** | Free Stepwise | 1–7 stepwise | any start/end | unfinished endings; break cadence dependence |

`M3` is new and important: melodies deliberately place `ti→do`, `fa→mi`, and
`re→do`/`re→mi` resolutions so the learner *feels* the pull of unstable degrees.

### Phase 2 — Leaps by function

| Stage | Name | Adds | Launch/land | Idea |
|---|---|---|---|---|
| **M5** | Triad Leaps Everywhere | 3rds within triad | any | do–mi–so leaps as ordinary vocabulary |
| **M6** | Leaps to Color Tones | 3rds to/from 2,4,6,7 | 1,3,5 | the *harder* thirds (e.g. 5→7, 2→4) |
| **M7** | Perfect Fourths | 4ths | prefer 1/5 ends | so→do, do→fa; the frame of tonal space |
| **M8** | Fifths & Sixths | 5ths, 6ths | prefer 1/5 ends | do→so, do→la; widest v1 leaps, strong recovery |
| **M9** | Free Diatonic Melodies | all diatonic | any, 6–8 notes | real beginner melodies, longer phrases |

Musicality rules (recovery after leaps, ≤2 direction changes early, no
interval-drill nonsense, contour variety) apply throughout — carry over the good
rules already written in `fixed_audio_curriculum.py`.

### Phase 3 — Beyond v1 (roadmap, not for first release)

Chromatic tendency tones (`fi`, `si`, `ta`), secondary-dominant color,
modulation, compound-meter melodies, two-phrase periods, sequences.

---

## Part IV — The minor path (its own ladder, not a mirror)

Minor is **not** a free 2× mirror of major — its tonal gravity is different and
that difference is the whole point. Give it a parallel-but-distinct ladder in
**A natural minor** (la-based), then extend to harmonic minor.

- Stages **m0–m9** mirror the *structure* of M0–M9 (triad first, steps, leaps)
  but center on **la**, and the "tendency tone" stage is genuinely different:
  natural minor has **no leading tone** — `so` is a subtonic a whole step below
  `la`. So `so→la` is a soft, modal resolution, and the strong `fa→mi` pull of
  major is replaced by the minor's own `ti→la`/`fa→mi` (`re→do` in la-based
  numbering) behaviors.
- **Harmonic-minor extension (m10+):** introduce the **raised 7 (`si`)** — the
  real leading tone — as a distinct new sound, including the characteristic
  augmented second `fa→si` (`le→si`). This is one of the most satisfying
  "new color" moments in ear training and deserves its own short arc.
- **Relative vs parallel framing:** offer both entry points as optional
  transfer decks — "A minor is the same notes as C major, different home"
  (relative) and "C minor vs C major" (parallel) — because learners hear these
  two relationships very differently.

---

## Part V — The rhythm ladder

Keep the strong R1–R9 design already written, with two upgrades:

1. **Rhythm dictation is a first-class path** (path D): hear a one-pitch rhythm,
   notate it with the transcription editor's rhythm mode. Rhythm dictation is
   often *easier to build correct intuitions* than rhythm reading, and the
   Transcribe template already supports rests + durations.
2. **Extend the ceiling** past v1: **compound meter (6/8)**, **anacrusis /
   pickups**, and **two-bar phrases** as an advanced rhythm arc (R10+).

| Stage | Adds |
|---|---|
| R1 | quarters, halves, wholes |
| R2 | quarter rests, delayed entries |
| R3 | eighth pairs (subdivision) |
| R4 | free mix of quarters / eighth pairs |
| R5 | eighth rests, offbeat entries |
| R6 | dotted quarter + eighth |
| R7 | ties across the beat |
| R8 | beat-level triplets |
| R9 | mixed beginner vocabulary |
| **R10+** | 6/8 compound, pickups, two-bar phrases (advanced) |

Rhythm reading uses a fixed repeated pitch (treble `B4`/`C5`, bass `D3`/`F3`);
add an optional **count-in click** so the pulse is externally given at first.

---

## Part VI — Merge, keys, clefs (the integration & transfer axes)

### Merge (paths E/F)

Curated combinations of a mastered pitch stage with a mastered rhythm stage —
**never** a full cross-product. One new difficulty axis at a time: if the melody
leaps, the rhythm stays plain, and vice versa. Both Sing and Dictate variants.
(Merge dictation = full melodic dictation, the capstone skill.)

| Merge stage | Pitch × Rhythm |
|---|---|
| ME1 | steps (M1–M4) × pulse (R1–R3) |
| ME2 | triad/thirds (M5–M6) × subdivision (R3–R4) |
| ME3 | fourths (M7) × offbeats (R5–R6) |
| ME4 | fifths (M8) × ties (R7) |
| ME5 | free (M9) × mixed (R9) — real short pieces |

### Keys & clefs (path G) — the transfer engine

Because we use movable-do, **the singing never changes when the key changes —
only the reading does.** That makes transposition a pure notation-reading skill
worth its own ladder:

- **Key ladder:** C → G → F → D → Bb → A → Eb → … , adding **one accidental at a
  time**. Each new key re-runs the learner through a compact set of melodies
  they already know how to *sing*, so all the new load is on reading the key
  signature and staff positions.
- **Transfer cards:** "here is a melody in C; now the same melody in G" —
  explicitly training the invariance that is the soul of movable-do.
- **Clef ladder:** treble → bass (full mirror) → **grand staff** (read across
  both) → alto (advanced). Bass isn't harder music, just relocated reading, so
  it can reuse the whole major/minor library.

---

## Part VII — Support, answer design, and new challenge types

### Tonal support (with a new option: the drone)

Per-stage default playback fades: `cadence + first note` → `first note` →
**`tonic drone`** → `nothing`. All supports stay available as manual buttons
always. The **tonic drone** (a sustained tonic under the melody) is a new,
cheap, and pedagogically powerful addition — singing against a drone is one of
the fastest ways to build stable intonation and functional hearing.

Support buttons available on every card: **Cadence**, **First note**,
**Tonic**, **Drone**, **Play melody** (answer side / dictation).

### Answer-side design (make the "aha" rich)

On reveal, show — layered, most-useful first:

1. **Solfège syllables** under each note (primary),
2. scale-degree numbers + note names (secondary),
3. a **function tag** per note (stable ● / tendency ○ / leap ↗),
4. the **contour glyph** and interval pattern,
5. replay + drone.

For dictation, additionally: **your answer vs the target**, per-note
green/red (already built), and a one-line verdict.

### New challenge card types ("going crazy," tastefully)

All buildable on the existing render + audio + transcription machinery:

- **Error-detection:** hear the correct melody, see notation with exactly one
  wrong note — tap the wrong note. Superb ear-training; trivial to generate
  (take a good melody, perturb one degree).
- **Interval singing:** "from this note, sing a rising perfect fourth" — pure
  interval production, a diagnostic side deck.
- **"Sing the next note":** show/hear the first N notes, predict note N+1 — trains
  melodic/tonal expectation.
- **Solfège-only vs notation-only variants:** some cards hide the staff and show
  only solfège letters (and vice versa), decoupling the two representations.
- **Checkpoints ("boss" cards):** at each phase boundary, a slightly harder
  curated melody that certifies readiness to advance.
- **Placement test:** a short adaptive set that suggests where to start.
- **Modes (advanced, "wow" factor):** the same seven notes with the tonal center
  moved — Dorian, Mixolydian, etc. — as a late exploratory deck.

---

## Part VIII — Recommended learner journeys

- **Complete beginner:** Rhythm-Read R1–R3 ∥ Melody-Sing M0–M2, then interleave
  Dictation of the same stages, then Merge ME1.
- **"I can already read a bit":** Placement test → Melody-Sing from your stage,
  add Dictation for reinforcement.
- **Ear-focused:** lead with Dictation paths; sing paths as confirmation.
- **Instrumentalist adding a second clef:** run the Keys & Clefs path over
  material you've already mastered in treble.

---

## Part IX — Card-type inventory (maps to existing templates)

| Curriculum card | Template | Status |
|---|---|---|
| Melody — Sing | `Sing` | built ✅ |
| Melody / Rhythm — Dictate | `Transcribe` | built ✅ (add rhythm-only mode framing) |
| Tonic drone support | audio asset + button | **new asset** (sustained tonic) |
| Error-detection | `Sing` variant (tap-wrong-note) | new template, reuses render+overlay |
| Interval singing | `Sing` variant | new, minimal |
| Transfer (same melody, new key) | `Sing`/`Transcribe` | data-only (reuse templates) |

The two core templates already carry most of the system. The drone is one new
audio render; the diagnostic types are small template variants.

---

## Part X — How this gets generated (build plan)

The design maps cleanly onto the pipeline the old plan sketched but never built.
Proposed module layout under `src/sight_singing/`:

```
curriculum/            # machine-readable stages (extend the existing configs)
  major.py  minor.py  rhythm.py  merge.py  keys.py  diagnostics.py
theory/
  scales.py            # degree ↔ pitch, per key/mode/clef, no-ledger ranges
  intervals.py         # interval logic in degrees and staff steps
  solfege.py           # degree → syllable (do-based major, la-based minor)
generate/
  contours.py          # named contour families → degree-sequence templates
  melody_gen.py        # instantiate families under stage constraints
  quality.py           # musicality filters + ranking (port existing rules)
  sampler.py           # dedup + representative sampling to study size
render/
  realize.py           # degrees → concrete notes for a key/mode/clef
  audio.py             # notes → mp3 (reuse existing fluidsynth/LAME pipeline)
build/
  serialize.py         # melody → card fields (MelodyJSON etc.)
  build_decks.py       # assemble per-path .apkg files
```

**Generation pipeline:** pick stage → generate degree sequences from its family
templates → filter by quality → dedup/cluster → sample → realize into
mode/key/clef → serialize → (render audio) → package. Generate and **review by
ear** before rendering thousands of clips — that ordering keeps the expensive
step behind a checked curriculum.

---

## Part XI — Phased release plan

Ship value early; validate before scaling audio.

- **Phase 1 (first real deck):** Treble, C major, **M0–M4**, both **Sing** and
  **Dictate**, tonic-drone support. Small audio footprint, exercises the whole
  system end to end. Study it for real.
- **Phase 2:** add **M5–M9** and the **rhythm** path (R1–R6) + rhythm dictation.
- **Phase 3:** **A minor** ladder (its own stages) + **Merge** ME1–ME3.
- **Phase 4:** **Keys** ladder (G, F, D…) + **bass clef** transfer + harmonic
  minor.
- **Phase 5:** diagnostics (error-detection, interval singing), checkpoints,
  placement test, and the advanced roadmap (modes, compound meter, chromatic).

Every phase is a self-contained, shippable deck family. Nothing here requires
finishing the whole thing before a learner gets something excellent.

---

## Part XII — Why this is better than v1

- Orders difficulty by **tonal function**, matching how hearing actually
  develops (triad-first), instead of by raw interval size.
- Makes **dictation a first-class, parallel skill**, doubling value per melody
  and building the inverse ability that most self-teachers never train.
- Treats **minor as its own musical world** (incl. harmonic minor's leading
  tone), not a mechanical mirror.
- Adds a **transfer engine** (keys + clefs) that turns movable-do's
  key-independence into an explicit, teachable skill.
- Introduces the **tonic drone** and **tendency-tone** work — two of the
  highest-leverage tools in real ear training.
- Keeps everything **finite, curated, sampled, and phased**, so it stays a
  great *product*, not a combinatorial data dump.
