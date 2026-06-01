# Rhythm Curriculum For The Sight-Singing Deck

## Goal

Teach rhythm as its own skill before asking the learner to combine it with pitch.

The curriculum should therefore run in three layers:

- a **pitch thread** with little or no rhythmic complexity
- a **rhythm thread** with little or no melodic complexity
- a **merge thread** that combines the two once each side is reasonably stable

This keeps the early cards psychologically simple and prevents the learner from
confusing “I missed the note” with “I missed the rhythm.”

## Product recommendation

Use three related deck families, not one giant mixed deck:

- `Pitch First`
- `Rhythm First`
- `Merged Sight Singing`

The existing fixed-audio melodic curriculum already covers the pitch-first side well.
This document defines the rhythm-first side and the merge strategy.

## Core design choice

For the rhythm-only track, keep pitch boring on purpose.

Recommended default:

- one repeated piano pitch per card
- no cadence
- optional one-beat or two-beat count-in
- one bar per card at first
- visual notation stays normal, but the learner's attention is rhythm, not tonality

Good default repeated pitches:

- treble deck: `B4` or `C5`
- bass deck: `D3` or `F3`

## Advancement philosophy

The learner should not need to clear every card in a stage.

Recommended advancement rule:

- move on after about **10-18 strong cards** in a stage
- keep extra cards in each stage for variety and re-entry
- let later stages become larger and more musical

## Size budget

This proposal targets:

- **408 canonical rhythm cards** in the rhythm-only thread
- **234 canonical merged cards** in the merge thread

That keeps the rhythm side finite while still leaving enough variety that the deck does
not feel solved after a handful of reviews.

## Relationship to the pitch curriculum

The pitch thread should stay rhythm-light until merge.

Recommended rule:

- pitch stages 1-9 remain mostly quarter-note based
- rhythm stages carry the timing burden separately
- merged stages introduce curated combinations rather than a full cross-product

That means the learner first builds:

- melodic contour fluency
- rhythmic decoding fluency
- then integrated audiation

in that order.

## Rhythm-only stage summary

| Stage | Title | Count | Advance After | New thing |
|---|---|---:|---:|---|
| R1 | Pulse and duration | 24 | 10-12 | quarters, halves, wholes |
| R2 | Silence and entry | 30 | 10-14 | quarter rests and delayed starts |
| R3 | First eighth pairs | 36 | 12-14 | subdivision inside one beat |
| R4 | Mixed beat fillings | 42 | 12-16 | free mix of quarter vs paired eighths |
| R5 | Offbeat feel | 48 | 14-16 | eighth rests and weak-beat entries |
| R6 | Dotted patterns | 48 | 14-18 | dotted quarter + eighth language |
| R7 | Ties across beats | 54 | 14-18 | sustain through the barline grid |
| R8 | Triplet pulse | 54 | 14-18 | beat-level triplets |
| R9 | Full v1 rhythm | 72 | 16-18 | mixed beginner rhythm vocabulary |

Total rhythm-only cards: **408**

## Global rhythm rules

- Every card should feel like a plausible musical bar, not a combinatorics artifact.
- Introduce only one genuinely new rhythmic idea per stage.
- Avoid bars where every beat uses the same cell unless the stage specifically needs it.
- Mix attack densities: sparse bars, medium bars, and more active bars.
- Prefer strong beat clarity in early stages.
- Do not overload a single bar with both a new notation idea and a new syncopation idea.
- In dotted, tie, and triplet stages, keep surrounding material plain so the new idea is audible.
- Reject ugly cards even if they are technically legal.

## Stage-by-stage design

### R1: Pulse and duration

Goal: establish that note shape equals time value.

- no rests yet
- durations: `q`, `h`, `w`
- all attacks on beat
- no subdivision

Family mix:

- `four_quarters` x6
- `two_halves` x4
- `whole_note_bar` x2
- `half_then_two_quarters` x6
- `two_quarters_then_half` x6

Desired character:

- maximally legible
- duration is the only problem
- should feel almost impossible to misunderstand once learned

### R2: Silence and entry

Goal: teach that silence is counted, not skipped.

- add quarter rests
- still no eighths
- attacks still happen only on beats

Family mix:

- `quarter_rest_then_motion` x6
- `motion_then_quarter_rest` x6
- `interior_quarter_rest` x6
- `half_rest_equivalent_feel` x6
- `rested_arrival_bar` x6

Desired character:

- the learner starts hearing empty beat space actively
- delayed starts become normal

### R3: First eighth pairs

Goal: subdivide a beat cleanly without syncopation yet.

- add `8 8` as a beat cell
- no isolated offbeat attacks yet
- each beat is still perceptually self-contained

Family mix:

- `single_eighth_pair` x8
- `two_eighth_pairs` x8
- `eighth_pair_opening` x6
- `eighth_pair_closing` x6
- `eighth_pair_between_quarters` x8

Desired character:

- the learner feels “two inside one beat”
- subdivision becomes visible and audible without being destabilizing

### R4: Mixed beat fillings

Goal: make quarter and paired-eighth choices feel interchangeable.

- any beat may be `q` or `8 8`
- use `h` sparingly as contrast
- still avoid dotted figures and ties

Family mix:

- `quarter_vs_pair_contrast` x10
- `paired_center` x8
- `paired_edges` x8
- `half_plus_subdivision` x8
- `three_density_levels` x8

Desired character:

- genuine one-bar rhythm reading
- still strongly beat-based

### R5: Offbeat feel

Goal: introduce weak-beat attack without yet introducing ties.

- add eighth rests
- allow `8r + 8` style cells
- keep bars short and readable

Family mix:

- `eighth_rest_pickup` x10
- `offbeat_answer` x10
- `quarter_then_offbeat` x10
- `offbeat_then_quarter` x8
- `mixed_onbeat_offbeat` x10

Desired character:

- first real syncopation feeling
- enough repetition that offbeat placement stops feeling shocking

### R6: Dotted patterns

Goal: introduce unequal beat subdivision as a stable new idea.

- add dotted quarter + eighth
- keep the reverse shape rare at first
- avoid combining dotted rhythm with multiple other hard cells

Family mix:

- `single_dotted_figure` x12
- `dotted_opening` x8
- `dotted_closing` x8
- `dotted_between_plain_beats` x10
- `two_dotted_figures_separated` x10

Desired character:

- dotted rhythm is clearly the lesson
- surrounding beats explain the shape

### R7: Ties across beats

Goal: teach duration continuity across the beat grid.

- add ties over beat boundaries
- start with same-pitch visual clarity in the rhythm-only deck
- keep the untied context plain

Family mix:

- `quarter_tied_to_quarter` x10
- `quarter_tied_to_eighth` x10
- `eighth_tied_across_beat` x10
- `single_tie_in_plain_bar` x12
- `tie_with_rest_context` x12

Desired character:

- sustained sound divorced from attack count
- learner stops equating “new beat” with “new note”

### R8: Triplet pulse

Goal: teach three-in-the-space-of-two as a beat event.

- add beat-level eighth-note triplets only
- no nested tuplets
- keep the rest of the bar plain

Family mix:

- `single_triplet_beat` x12
- `triplet_opening` x10
- `triplet_closing` x10
- `triplet_between_plain_beats` x10
- `two_triplet_beats` x12

Desired character:

- triplet beat is heard as one gesture
- the learner feels the pulse underneath the three notes

### R9: Full v1 rhythm

Goal: integrate the beginner rhythm vocabulary into real short bars.

- allow quarters, halves, wholes, rests, eighth pairs, offbeat entries, dotted figures,
  ties, and beat-level triplets
- cap difficulty by allowing at most one “hard” event family to dominate a bar

Family mix:

- `plain_with_one_spice` x16
- `syncopated_answer_bar` x12
- `dotted_or_tied_center` x12
- `triplet_contrast_bar` x12
- `dense_vs_sparse_pairing` x10
- `phrase_like_beginner_bar` x10

Desired character:

- should feel like music, not an exam
- broad enough that later merge cards do not feel like a shock

## Merge strategy

The merge curriculum should not be a full cross-product of the pitch and rhythm threads.
That would explode the media count and produce many bad cards.

Instead, use curated merge stages.

## Merge stage summary

| Stage | Title | Count | Source idea |
|---|---|---:|---|
| M1 | Stepwise + pulse rhythms | 36 | pitch stages 1-3 with rhythm stages R1-R3 |
| M2 | Thirds + subdivision | 42 | pitch stages 4-5 with rhythm stages R3-R4 |
| M3 | Fourths + offbeat feel | 48 | pitch stages 6-7 with rhythm stages R5-R6 |
| M4 | Fifths + sustained rhythm | 48 | pitch stages 8-9 with rhythm stage R7 |
| M5 | Full v1 merge | 60 | curated mix from mature pitch + rhythm vocab |

Total merged cards: **234**

## Merge rules

- In M1, keep melodies stepwise and rhythm mostly beat-based.
- Introduce one new difficulty axis at a time: if the melody leaps, the rhythm should usually simplify.
- Use the learner's previously mastered rhythm cells, not novel ones.
- Keep phrase shape musical; do not stitch together arbitrary pitch cards and arbitrary rhythm cards.
- Prefer a finite hand-curated library over generator output in early releases.

## Practical deck recommendation

Publishable deck family:

- `Treble Pitch First`
- `Treble Rhythm First`
- `Treble Merge`
- later the same for bass

Transfer stages can then bridge:

- treble pitch -> treble merge
- treble merge -> bass pitch
- bass pitch -> bass merge

This keeps each individual deck smaller than one giant everything-deck while still
giving the learner a coherent path.
