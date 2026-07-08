# Fossilized constants — assumptions the code didn't know it was making

A running note on a specific failure mode this project keeps producing, the ones
we've excavated so far, and (below) the ones an audit turned up that are still
buried. Kept because the *pattern* is more useful than any single fix.

## The pattern

A **fossilized constant** is a hardcoded value or default that silently encodes a
single-case assumption — a claim about the world the code was written for — which
was correct then and quietly wrong later. They form honestly: you write
`BAR_UNITS = 8` because today every melody *is* one bar. The number isn't a bug;
it's the shape of the only world you'd needed yet. It becomes a fossil the moment
the project supports a case that world never imagined, and the constant keeps
enforcing the old world without anyone deciding to.

Two things make them nasty:

1. **They read as facts, not decisions.** `"treble"`, `4/4`, `["C4".."C5"]` look
   like descriptions of reality, so nobody re-examines them. A decision gets
   revisited; a fact doesn't.
2. **The trigger is always downstream and looks unrelated.** The single-bar gate
   didn't fail when written — it failed months later when a *dictation* feature
   generated a 6-note phrase, three subsystems away.

**How to smell one:** any bare constant or default is a claim. Ask *"what world
does this number believe in?"* and *"do we still only live there?"* When the
answer to the second is no, you've found a fossil — usually right before it bites.

## The fossils we've dug up

### 1. `cursor === BAR_UNITS` — "every melody is exactly one 4/4 bar"
`assets/_transcription.js`, `targetEventsFromData`. The transcription editor
accepted a melody only if its events summed to precisely one bar. What it
believed: melodies are one bar. What broke it: the dictation ladder's whole point
is a *variable length ramp* (2–6 notes), and — quietly — the sight-singing deck's
own length-5/6 Transcribe cards (M2/M6/M8/M9) had been shipping un-answerable
("outside scope") the entire time. Generalized to a dynamic `capacity` = the
target melody's full length; a 4-quarter melody keeps `capacity === 8`, so the
old world is a special case of the new one.

### 2. `PITCHES = ["C4".."C5"]` + treble-only `supportedData` — "treble, one octave, C-major-ish, no accidentals"
`assets/_transcription.js`. The editor placed notes in a fixed one-octave treble
window. Four assumptions in one array: treble clef, exactly one octave, centered
on middle C, and (because the pitches are bare letters) no accidentals. What broke
it: minor melodies climb to A5, bass drops to B2 — and again quietly, C-major
dictation itself uses `ti,` = **B3**, one step *below* the C4 floor, so DD7–DD9
had un-enterable notes the day they shipped. Generalized to a melody-driven,
clef-aware **staff-position** window (letters, with the key signature supplying
accidentals). The last piece — the "no accidentals" belief — is **resolved in
Phase C**: the editor now has an accidental palette (shown for harmonic minor) and
draws the key signature, so harmonic minor's G♯ and G/F major's F♯/B♭ are
enterable and graded by effective chromatic pitch.

### 3. VexFlow's `space_above_staff` (~40px) — "the staff sits at a fixed, comfortable place"
`assets/_transcription.js`, `renderScore`. Not our constant — VexFlow's. It
reserves ~40px above the top staff line (`getYForLine(0) = staveY + 40`). The
single-octave editor never noticed, because its notes never strayed far from the
staff. The moment the canvas height was computed *tightly* around a wide range,
the unaccounted-for 40px pushed low notes off the bottom of the canvas — and
because the overlay is where pointer events land, real taps on those notes silently
missed (synthetic dispatch masked it; only a real-mouse Playwright test caught it).
The assumption was inherited, not written, which is the sneakiest kind.

### 4. Two cards per note — "if you can transcribe it, you should"
`src/sight_singing/anki_model.py`, `make_model`. Every melody generated a Sing
*and* a Transcribe card. A *pedagogical* fossil, not a numeric one: it silently
asserted "dictation practice = transcribing the tunes you sight-sing," which is
exactly the recall-not-hearing trap the separate dictation curriculum exists to
avoid. Exposed only when we asked "why does Sight Singing have 854 Transcribe
cards?" Resolved by making the sight-singing model Sing-only; dictation is its own
note type and pool.

### 5. Reference-by-name — "the model I mean is the one named X"
`scripts/apply_live_template_update.py` and the live collection. Code addressed the
note type by its name, `Sight Singing (MVP v24 inline engine)`. But an earlier
import had collided and Anki had renamed the *actual* live model to
`…-9613b`, so the name pointed at an empty impostor. The assumption: a name is a
stable identity. It isn't, across an import boundary. Fixed by resolving the model
the cards *actually use* (`notesInfo`) before touching anything.

## Two "choices" that were actually arithmetic

Not fossils — the opposite. Places where something that looked like a taste
decision turned out to be forced by structure, which is worth remembering because
it means you can stop arguing about it.

- **Parity.** A no-immediate-repeat, purely stepwise phrase *cannot* begin and end
  on the tonic triad. Each step flips the parity of the staff position; triad
  tones (do/mi/so) are all the same parity; a length-4 phrase makes an odd number
  of flips. So `DD3` allowing non-triad endings isn't a fudge — it's a theorem
  wearing a nice coat. (See the note in `curriculum/stages.py`.)
- **Dictation ≠ singing.** "Steps before leaps" is a *production* heuristic (about
  controlling a voice), not a *perception* one. Run the skill backwards — hearing
  instead of singing — and triads are the *easy* case (the stable pillars) while
  the mi–fa half-step is hard. The two curricula diverge for a reason that's about
  which sense is involved, not preference.

## Still latent (audit, 2026-07-07)

_From a sweep of the editor/renderer and the generation/build layers (2026-07-07).
The happy surprise: **almost nothing bites today**, and almost everything latent
bites at a phase we've already planned — so this is really a pre-flight checklist
for B (rhythm) and C (accidentals/keys). Grouped by when it cracks._

> **Fixed 2026-07-07 (an "audit-fixes" pass before Phase B):** both *bites-now*
> items (ghost-preview geometry, renderer fixed height); and, as prep, **position-
> based grading** (`eventsMatch` now compares staff position — a no-op for the
> all-natural cards today, correct for accidental keys), **answer-staff key/meter
> threading**, **`_melody_id` harmonic-minor distinctness** (zero churn to existing
> ids), the dead **`is_tendency_tone`**, and the **localStorage fallback**. Still
> open: editor accidental *input* + key-sig display + the G/F keys track (Phase C);
> the tritone-mode for minor interval drills (with C). Items below are marked ✅
> where done.
>
> **Phase B (2026-07-07):** the **sounded-rhythm grader is now wired** (rhythm
> cards grade pitch-agnostic + rest-spelling-equivalent — a half rest == two
> quarter rests; verified end to end) and the RD track (R1–R5) ships. Still open:
> dotted/tie/triplet editor *input* (R6–R9) and the triplet unit-math + compound
> meter — deferred to the advanced-rhythm work. Also caught + fixed a new fossil
> while here: **`renderMeta` mislabelled minor cards as "major"** (`data.mode ===
> "minor"` never matched our `natural_minor`/`harmonic_minor`), and the rhythm
> badge now comes from `gradeMode`.
>
> **Phase C (2026-07-08):** the whole accidentals/keys cluster below is **closed**.
> The editor now (1) draws the **key signature** on its stave, (2) offers an
> **accidental palette** (shown only for harmonic minor), and (3) grades by
> **effective chromatic pitch** — `pitchChroma(pitch, explicitAcc, keyAcc)` folds
> the key-signature default in, so a bare F on the F line matches an F♯ target in G
> major, while the harmonic-minor `si` demands an explicit ♯ (a bare G is a miss).
> `buildAnswerData` threads key/mode/keyAcc to the answer staff. The generator's
> **tritone check now takes the realization mode** (`passes_hard_rules(mel, stage,
> mode)`, threaded from `build_library`), so a minor interval drill would strip the
> minor tritone, not the major one (locked by a test). Shipped: harmonic-minor
> `ND9h` and the `6 · Other Keys` G/F transfer track.

**Cleared (checked, provably fine):** deck-id collisions — every id computed, no
overlap within the dictation tree or against sight-singing (91-id gap); model ids
distinct. The hardcoded `4/4` is load-bearing single-meter, not a crammed-bar bug.
`quality_score`'s tonic test (`mel[-1] % 7 in (0,2,4)`) is mode-agnostic and
correct (la-minor shares triad indices with major). Legacy MVP audio constants are
a dead path. `tonic_octave_for` raises loudly on an unknown clef, not silently.

### Bites now (real today, small) — ✅ both fixed
- **Ghost hover-preview geometry** — `_transcription.js` ~1138/1165/1200. The
  ledger-line and stem-direction of the *hover preview* still use fixed `PITCHES`
  indices (index 0 = C4, index 6 = middle line) from the old one-octave window; now
  that the window is melody-driven they're wrong on bass/wide ranges. **Cosmetic,
  and a regression from the range generalization** — the *committed* note draws
  correctly via VexFlow. Fix: derive from `ordinalOf(pitch)` vs the clef reference.
- **Display renderer fixed height** — `_renderer.js:425`, `drawStaff` uses a fixed
  134px canvas. The *same fossil* we fixed in the editor, still living in the
  read-only notation/target/answer staves; a high treble or low bass note can clip.
  Fix: size height from the pitch span (mirror the editor's `aboveTop/belowBot`).

### Bites at Phase B/D (rhythm input)
- ✅ **Editor rejected dotted durations** — fixed in **Phase D**. `durationUnits`
  now honours a trailing "d" (×1.5), a `DURATION_ALIGN` table replaces the
  `startUnit % units` check (dotted values align to the *beat*, not their own
  length — a dotted quarter is 3 units yet may start on beat 3), and a dot modifier
  on the duration bar (rhythm cards) enters `qd`/`hd`. Unblocked rung **R6**.
- **Editor still rejects ties/triplets** — `_transcription.js`. Ties/syncopation
  (R7) need off-beat note starts (relax quarter alignment, or a tie tool); triplets
  (R8/R9) need a 1/3 sub-beat grid the integer eighth-unit model can't express. The
  renderer already draws both. Deferred to the next advanced-rhythm pass.
- **Triplet unit math double-counts** in the measure-split — `_renderer.js`.
  A triplet eighth returns 1 unit but sounds 2/3; multi-bar melodies with triplets
  get spurious barlines/rest padding. Track *sounded* ticks separately. (Only bites
  once triplet input ships.)
- **`capacityForData` assumes a 2-unit (quarter) beat** — `_transcription.js`.
  Fine for x/4, wrong for compound meters (6/8's beat is a dotted quarter). (Only
  bites once compound-meter content ships.)

### Bites at Phase C (accidentals / keys) — the main cluster — ✅ all closed in Phase C
- ✅ **Grading compares exact pitch strings, but the editor only speaks diatonic
  staff positions** — `eventsMatch` now requires same staff position AND same
  effective chromatic pitch (`pitchChroma`), so a bare F matches an F♯ target under
  a G-major key sig while the harmonic-minor `si` needs an explicit ♯.
- ✅ **Editor hardcodes 4/4 + C major** — the editor stave draws `curKeySig` and
  `buildAnswerData` threads clef/timeSig/key/mode/keyAcc to the answer staff.
- ✅ **`_melody_id` collapses natural vs harmonic minor** — already fixed in the
  audit-fixes pass (`harm` tag); ND9h now ships and its ids are distinct from ND9.
- ✅ **`forbid_tritone_leap` uses the major tritone position for mode-less stages**
  — `passes_hard_rules(mel, stage, mode)` takes the realization mode, threaded from
  `build_library`; a minor interval drill strips the minor tritone (test-locked).

### Dead / trivial
- **`is_tendency_tone` flags the wrong degrees in minor** — `theory/scales.py:176`
  (major degree numbers in la-minor: flags re, not fa/ti). But nothing reads the
  field it feeds (`melody_gen` uses `stage.tendency_*_from`). Delete or reimplement.
- **`melodyId()` → `"unknown"`** — `_transcription.js:99`. Two id-less cards share
  one localStorage answer key. Shielded by the front's clear-on-init. Hash fallback.

## The checklist

When you add a constant or a default, or when you're about to support a new case,
run the smell test on the values already in the path:

- Every bare literal (`"treble"`, `4/4`, `C4`, `8`) is a **claim** — write down
  what world it assumes.
- A **default argument** is a fossil-in-waiting: it's the old world made invisible.
- **Exact equality** where an *equivalence* is meant (same pitch vs same staff
  position; same glyphs vs same sounded rhythm) is a fossil that hasn't cracked yet.
- **Names and ids** are not identities across import/dedup boundaries.
- When a value "just works," ask whether it works or whether you only ever tested
  the world it assumes.
