# Fixed-Audio Curriculum For The Sight-Singing Deck

## Why this exists

The original plan assumed that the card could synthesize melody audio on demand in
JavaScript. With AnkiMobile, that appears too timing-sensitive to trust for rhythm. A
fixed-audio approach changes the design problem:

- each melody needs a pre-rendered audio file,
- the melody library must therefore be finite,
- and the curriculum has to be designed as a staged collection of strong melodies, not
  as an open-ended generator.

This document is the first-pass curriculum for that new approach.

## Design assumptions

- The canonical curriculum unit is a **4-note scale-degree melody**.
- Counts below are **canonical melodies before mirroring** across clef and mode.
- The learner does **not** need to clear every melody in a stage.
- Each stage should contain noticeably more cards than the learner needs.
- The stage library exists to make review feel varied while still staying finite.

Recommended advancement rule:

- move on after roughly **12-20 solid melodies** in a stage,
- keep a few stretch melodies per stage for replay and re-entry,
- and let later stages contain more variety than earlier ones.

## Size budget

This proposal targets **576 canonical melodies**:

- Stage 1: 24
- Stage 2: 36
- Stage 3: 48
- Stage 4: 60
- Stage 5: 72
- Stage 6: 72
- Stage 7: 84
- Stage 8: 84
- Stage 9: 96

If later mirrored across:

- C major
- A natural minor
- treble clef
- bass clef

that becomes **2,304 rendered melody clips**.

That is still finite and workable, but it is a strong argument for either:

- releasing the curriculum in phases, or
- moving away from uncompressed `.wav` for the full mirrored library.

## Support fade plan

The pitch-reading curriculum should also fade support gradually.

| Stages | Default support | Rationale |
|---|---|---|
| 1-2 | cadence + first note | maximize orientation and reduce launch anxiety |
| 3-4 | first note | remove full tonal spoon-feeding, keep launch help |
| 5-6 | optional first note | learner should increasingly self-locate |
| 7-9 | nothing autoplayed | support stays available, but not defaulted |

The tonic button should remain available in all stages.

## Stage summary

| Stage | Title | Count | Advance After | New thing |
|---|---|---:|---:|---|
| 1 | Neighbor patterns | 24 | 12-16 | local motion around 1, 3, 5 |
| 2 | Stable stepwise transfer | 36 | 12-16 | all seven degrees appear, still no skips |
| 3 | Fully stepwise | 48 | 14-18 | any launch, any arrival, still stepwise |
| 4 | First thirds | 60 | 14-18 | one third per melody |
| 5 | Thirds integrated | 72 | 16-20 | thirds become normal vocabulary |
| 6 | First fourths | 72 | 16-20 | one fourth, tightly controlled |
| 7 | Fourths integrated | 84 | 18-20 | fourths become normal vocabulary |
| 8 | First fifths | 84 | 18-20 | one fifth, strong recovery rules |
| 9 | Full v1 vocabulary | 96 | 20 | free diatonic beginner melodies |

## Global musicality rules

These rules should apply when turning the stage briefs into exact libraries.

- Avoid three identical notes in a row except in a small number of Stage 1 cards.
- Keep most melodies to no more than two direction changes.
- After a fourth or fifth, recover by step in the opposite direction unless there is a
  very good reason not to.
- Do not allow “interval-drill nonsense”: legal but ugly skip chains are still bad
  curriculum.
- Mix contour types inside each stage: ascent, descent, arch, valley, hold, and turn.
- Keep a healthy spread of starts and endings so the learner does not overfit one cue.
- Prefer singable ambitus over maximal span.

## Stage-by-stage design

### Stage 1: Neighbor patterns

Goal: first contact with tonal stability and staff decoding.

- no scale degree 7 yet
- start on 1, 3, or 5 only
- end on 1, 3, or 5 only
- interval vocabulary: unison and second only
- max ambitus: a third

Family mix:

- `upper_neighbor_return` x6
- `lower_neighbor_return` x4
- `up_plateau_back` x4
- `down_plateau_back` x4
- `delayed_ascent` x3
- `delayed_descent` x3

Desired character:

- very safe launches
- very clear landing points
- useful repetition is acceptable here

### Stage 2: Stable stepwise transfer

Goal: all seven degrees can appear, but the learner still launches and lands on stable
tones.

- start on 1, 3, or 5 only
- end on 1, 3, or 5 only
- interval vocabulary: unison and second only
- introduce 2, 4, 6, and 7 as passing or destination tones

Family mix:

- `stable_ascent_transfer` x8
- `stable_descent_transfer` x8
- `upper_neighbor_hold` x6
- `lower_neighbor_hold` x6
- `delayed_unstable_arrival` x4
- `tonic_boundary_resolution` x4

Desired character:

- still reassuring
- more complete tonal map
- enough variety that the stage no longer feels like three-note training wheels

### Stage 3: Fully stepwise

Goal: remove stable-start constraints while preserving stepwise singability.

- start on any degree
- end on any degree
- still unison and second only
- allow unfinished-feeling endings so the learner stops depending on cadence-like shapes

Family mix:

- `straight_ascent` x10
- `straight_descent` x10
- `arch` x8
- `valley` x8
- `repeated_arrival` x6
- `directional_turn` x6

Desired character:

- broader reading fluency
- more genuine melody fragments
- still easy enough to sing without interval-drill fatigue

### Stage 4: First thirds

Goal: introduce the first real skip without letting the stage become jumpy.

- start on 1, 3, or 5 only
- end on 1, 3, or 5 only
- at most one third per melody
- the rest of the line should stay stepwise

Family mix:

- `opening_third_up` x10
- `opening_third_down` x10
- `interior_third_up` x10
- `interior_third_down` x10
- `closing_third_up` x10
- `closing_third_down` x10

Desired character:

- the learner notices the new interval immediately
- the surrounding notes explain the leap
- nothing should feel acrobatic yet

### Stage 5: Thirds integrated

Goal: thirds stop feeling “special” and become part of normal melodic language.

- start on any degree
- end on any degree
- thirds may recur, but avoid ugly consecutive-skip patterns

Family mix:

- `opening_third_gesture` x12
- `closing_third_gesture` x12
- `two_thirds_separated_by_step` x12
- `third_chain_with_recovery` x12
- `step_and_skip_arch` x12
- `step_and_skip_valley` x12

Desired character:

- clearly more musical than Stage 4
- still beginner-friendly
- enough variety to keep the stage from turning into “spot the skip”

### Stage 6: First fourths

Goal: introduce a bigger leap while preserving strong tonal grounding.

- start on 1, 3, or 5 only
- end on any degree, but prefer 1 or 5
- at most one fourth per melody
- use stepwise contrary recovery after the fourth whenever possible

Family mix:

- `opening_fourth_up` x12
- `opening_fourth_down` x12
- `interior_fourth_up` x10
- `interior_fourth_down` x10
- `prepared_fourth_and_resolution` x14
- `single_fourth_inside_step_shell` x14

Desired character:

- stronger shape profile
- still tightly supervised
- the leap should be memorable, not random

### Stage 7: Fourths integrated

Goal: allow fourths to behave like normal melodic events instead of one-off surprises.

- start on any degree
- end on any degree
- fourths may recur, but keep them buffered by stepwise motion or a single smaller skip

Family mix:

- `fourth_launch_ascending` x12
- `fourth_launch_descending` x12
- `interior_fourth_bridge` x12
- `arch_with_fourth_peak` x12
- `valley_with_fourth_floor` x12
- `two_skips_with_step_buffer` x12
- `mixed_step_third_fourth` x12

Desired character:

- broader interval fluency
- still singable as melody, not as a diagnostic sheet

### Stage 8: First fifths

Goal: introduce the widest leap allowed in version 1.

- start on 1, 3, or 5 only
- end on any degree, but prefer 1 or 5
- at most one fifth per melody
- strongly prefer stepwise contrary recovery after the fifth

Family mix:

- `opening_fifth_up` x14
- `opening_fifth_down` x14
- `interior_fifth_up` x12
- `interior_fifth_down` x12
- `fifth_with_contrary_step_recovery` x16
- `fifth_with_supporting_small_skip` x16

Desired character:

- structurally bolder
- still controlled enough that a beginner can succeed with repetition

### Stage 9: Full version 1 vocabulary

Goal: free diatonic beginner melodies within the project’s current limits.

- start on any degree
- end on any degree
- seconds, thirds, fourths, and fifths all available
- musicality rules still matter more than legal interval vocabulary

Family mix:

- `opening_leap_control` x16
- `closing_leap_control` x16
- `arch_mixed_intervals` x14
- `valley_mixed_intervals` x14
- `double_skip_but_singable` x12
- `tonic_avoidant_launch` x12
- `cadence_like_closures` x12

Desired character:

- real beginner melodies
- multiple valid reading strategies
- a good stopping point before rhythm, chromaticism, or longer phrases

## Handoff to generation

The companion machine-readable version of this plan lives in
`src/sight_singing/fixed_audio_curriculum.py`.

That file should be treated as the source of truth for:

- stage counts
- support defaults
- interval vocabulary
- stage-specific rules
- melody family quotas
- example degree-shapes for later library generation

## Recommended next implementation step

Use this curriculum to build the **canonical degree-level melody library** first:

1. instantiate the exact finite melody set for Stages 1-3,
2. review the result for musical quality by ear,
3. then continue through Stages 4-9,
4. and only after that render audio assets.

That ordering keeps the expensive part, generating thousands of files, behind a curriculum
that has already been checked.
