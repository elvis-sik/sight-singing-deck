# Transcription Mini-Game Design

## Goal

Build a transcription exercise on top of the existing sight-singing deck:

- audio plays on the front
- the learner enters the melody on a clickable staff
- the back reveals the target notation
- the same note content can power both sight-singing and transcription cards

The design should support a useful v1 quickly, while leaving room for:

- ties
- triplets
- rests
- dotted rhythms
- major and minor
- treble and bass clef

## Recommendation

Use the same note type and source content model, but add a second card template:

- `Sing`
- `Transcribe`

This keeps:

- one audio pipeline
- one melody source of truth
- one rendering engine
- one media packaging system

## Product Shape

### Front of transcription card

Show:

- autoplay controls
- a blank editable staff
- a small rhythm/pitch toolbar
- measure progress
- clear/reset buttons
- optional hint area

Do not show:

- the answer notation
- scale degrees by default

### Back of transcription card

Show:

- the learner's entered answer, if we persist it locally in page state
- the target notation
- a simple comparison summary
- replay buttons

## Scope Recommendation

### V1

Support:

- single voice only
- treble clef first
- 4/4 only
- quarter, half, whole, eighth notes
- quarter and half rests
- stepwise and skip melodies within the current melodic range
- explicit measure boundaries
- front autoplay
- note entry by selecting duration, then tapping staff position
- erase and replace

Do not support yet:

- tuplets
- ties
- dotted rhythms
- multiple voices
- chords
- drag editing
- freehand note placement

### V2

Add:

- dotted notes
- ties
- minor mode
- bass clef
- better mobile editing affordances

### V3

Add:

- triplets
- mixed rhythmic cells
- pickup measures if needed
- richer validation and partial credit

## Why This Scope

The hardest part is not notation rendering. It is mobile-friendly editing.

If we support ties and triplets too early, we risk spending most of the effort on input UX instead of getting a playable exercise. A constrained v1 gives us:

- a usable learning tool sooner
- data about what is frustrating
- a stable internal model for advanced rhythm later

## Core Technical Idea

Treat notation as structured musical events first, and rendering as a view of those events.

The editor should never manipulate SVG directly. It should manipulate JSON state.

That gives us:

- consistent rendering
- reliable validation
- support for normalization
- a clean path to ties and tuplets

## Proposed Melody Data Model

The current `MelodyJSON` is display-oriented. We should evolve toward an event-based model.

### Current shape

```json
{
  "clef": "treble",
  "key": "C",
  "mode": "major",
  "timeSig": "4/4",
  "notes": ["C4", "D4", "E4", "F4"],
  "durations": ["q", "q", "q", "q"],
  "degrees": [1, 2, 3, 4]
}
```

### Proposed richer shape

```json
{
  "version": 2,
  "clef": "treble",
  "key": "C",
  "mode": "major",
  "timeSig": "4/4",
  "bars": [
    {
      "events": [
        {
          "kind": "note",
          "pitch": "C4",
          "duration": "q"
        },
        {
          "kind": "note",
          "pitch": "D4",
          "duration": "q"
        },
        {
          "kind": "note",
          "pitch": "E4",
          "duration": "q"
        },
        {
          "kind": "note",
          "pitch": "F4",
          "duration": "q"
        }
      ]
    }
  ],
  "degrees": [1, 2, 3, 4],
  "supports": {
    "tonic": "C4",
    "firstNote": "C4",
    "cadenceKey": "C"
  }
}
```

## Event Model

Each event should be one of:

- `note`
- `rest`

Each event can later carry richer attributes:

```json
{
  "kind": "note",
  "pitch": "E4",
  "duration": "8",
  "dots": 0,
  "accidental": null,
  "beamGroup": 1,
  "tuplet": {
    "id": "t1",
    "count": 3,
    "inSpaceOf": 2
  },
  "tieStart": false,
  "tieEnd": false
}
```

For v1 we only need:

- `kind`
- `pitch`
- `duration`

## Canonical Duration Tokens

Use explicit symbolic durations instead of relying on VexFlow-only strings.

Recommended tokens:

- `w`
- `h`
- `q`
- `8`
- `16`

Later extensions:

- `q.`
- `8.`
- triplet flags via `tuplet`

## Why Ties And Triplets Are Still Doable

### Ties

Ties are manageable if represented as event metadata, not as a drawing trick.

Example:

```json
[
  { "kind": "note", "pitch": "C4", "duration": "q", "tieStart": true },
  { "kind": "note", "pitch": "C4", "duration": "q", "tieEnd": true }
]
```

### Triplets

Triplets are manageable if events belong to a tuplet group.

Example:

```json
[
  { "kind": "note", "pitch": "C4", "duration": "8", "tuplet": { "id": "t1", "count": 3, "inSpaceOf": 2 } },
  { "kind": "note", "pitch": "D4", "duration": "8", "tuplet": { "id": "t1", "count": 3, "inSpaceOf": 2 } },
  { "kind": "note", "pitch": "E4", "duration": "8", "tuplet": { "id": "t1", "count": 3, "inSpaceOf": 2 } }
]
```

The complexity is mostly in editor UX, not data representation.

## Editor UX

### Mobile-first interaction model

The safest input model is:

1. choose a duration from the toolbar
2. tap a staff line/space to place a note
3. use an accidental toggle if needed
4. tap an existing note to replace or delete it

This is much safer on mobile than:

- dragging notes
- dragging stems
- resizing durations directly on the staff

### Toolbar

Recommended v1 toolbar:

- quarter note
- half note
- whole note
- eighth note
- quarter rest
- half rest
- erase
- clear bar
- reset all

Recommended v2 additions:

- dot
- tie
- triplet
- accidental selector

## Staff Interaction

### Placement

Each bar exposes discrete slots derived from the meter grid.

In 4/4 v1:

- whole note takes 4 beats
- half note takes 2 beats
- quarter note takes 1 beat
- eighth note takes 1/2 beat

The editor should snap to valid positions rather than allow arbitrary x-placement.

### Pitch targeting

We should map taps to discrete pitches in the allowed exercise range.

For early stages, the visible and tappable range can be intentionally narrow:

- `C4` to `A4` in treble

This improves usability and reduces accidental mis-entry.

## Validation Model

Do not compare rendered SVG or screen positions.

Instead:

1. normalize user answer into canonical event JSON
2. normalize target melody into canonical event JSON
3. compare event-by-event

### V1 validation

Check:

- number of bars
- number of events
- pitch of each note
- duration of each event

### Later validation

Check:

- tie structure
- tuplet grouping
- enharmonic policy if we support accidentals more broadly

## Suggested Normalization Rules

- strip UI-only fields
- sort bar metadata deterministically
- compare canonical pitch strings
- compare canonical duration strings
- compare tuplet group structure by logical order, not by arbitrary generated ids

## Rendering Architecture

Split rendering into three layers:

### 1. Content parser

Reads `MelodyJSON` and editor state.

### 2. Notation model

Produces canonical bars/events.

### 3. VexFlow renderer

Draws either:

- target notation
- editable learner notation

The current renderer in [assets/_renderer.js](./assets/_renderer.js) can become the seed of the read-only side, but it will need refactoring.

## Proposed JS Modules

Eventually, split into:

- `_notation_model.js`
- `_notation_render.js`
- `_transcription_editor.js`
- `_transcription_compare.js`

For now, a single file is fine while we prove the concept.

## Card Template Strategy

Add a second template to the same note type:

- `Sing`
- `Transcribe`

### `Transcribe` front

- autoplay sequence
- blank editor staff
- toolbar
- hidden serialized target melody

### `Transcribe` back

- target notation
- optional user-entered notation snapshot if available
- replay controls

## Persistence Strategy

Short version: do not try to save a persistent answer into the note.

Inside Anki card templates, the realistic v1 is:

- editor state lives in page JS memory
- front interaction is self-contained
- back shows the correct answer

If we later want answer persistence per review, that is a bigger system problem and should be treated separately.

## Curriculum Compatibility

This mini-game fits the fixed-audio curriculum well.

Why:

- same finite melody library
- same audio assets
- same major/minor and clef stages
- same cards can power multiple exercise types

This makes the finite-audio approach more valuable, not less.

## Risks

### Biggest risk

Touch UX becomes fiddly if we make editing too freeform.

### Medium risks

- VexFlow layout edge cases for longer or more complex bars
- triplet input complexity
- keeping toolbar state understandable

### Low risks

- data modeling for ties/triplets
- reusing the current note type

## Recommended Build Order

1. Upgrade `MelodyJSON` toward bar/event structure while keeping backward compatibility.
2. Add a second `Transcribe` card template.
3. Build a read-only blank staff renderer with bar slots.
4. Add note placement for quarter notes only.
5. Add erase/reset.
6. Add half, whole, eighth, and rests.
7. Add validation against target events.
8. Add dotted rhythms.
9. Add ties.
10. Add triplets.

## Concrete V1 Success Criteria

V1 is successful if a learner can:

- hear a short melody
- enter a four-beat answer on a staff
- correct mistakes easily
- reveal the correct notation
- do this comfortably on mobile

## Immediate Next Step

Implement a tiny vertical slice:

- one `Transcribe` card template
- quarter notes only
- one bar of 4/4
- tap-to-place notes on treble staff
- reset button
- answer shown on back

If that feels good on Anki Mobile, the rest becomes much more believable.
