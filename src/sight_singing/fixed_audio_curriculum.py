"""Finite staged curriculum spec for pre-rendered melody audio."""

from __future__ import annotations

TOTAL_CANONICAL_MELODIES = 576
FULL_MIRROR_VARIANTS = 4
TOTAL_RENDERED_CLIPS_IF_FULLY_MIRRORED = (
    TOTAL_CANONICAL_MELODIES * FULL_MIRROR_VARIANTS
)


FIXED_AUDIO_CURRICULUM = {
    "version": 1,
    "canonical_unit": (
        "One 4-note melody encoded as scale degrees before realization into a specific "
        "mode, clef, and audio file."
    ),
    "advance_policy": {
        "summary": (
            "Learners do not need to master every melody in a stage. Each stage should "
            "contain noticeably more melodies than the learner needs."
        ),
        "default_guideline": "Advance after roughly 12-20 solid melodies.",
    },
    "support_fade_plan": [
        {
            "stages": ["stage_1", "stage_2"],
            "default_support": ["cadence", "first_note"],
        },
        {
            "stages": ["stage_3", "stage_4"],
            "default_support": ["first_note"],
        },
        {
            "stages": ["stage_5", "stage_6"],
            "default_support": ["first_note_optional"],
        },
        {
            "stages": ["stage_7", "stage_8", "stage_9"],
            "default_support": [],
        },
    ],
    "global_quality_rules": [
        "Avoid three identical notes in a row except for a small number of Stage 1 cards.",
        "Keep most melodies to no more than two direction changes.",
        "After a fourth or fifth, prefer recovery by step in the opposite direction.",
        "Reject legal-but-ugly skip chains; musicality beats combinatorics.",
        "Mix ascent, descent, arch, valley, hold, and turn shapes inside each stage.",
        "Spread starts and endings across the allowed degrees inside each stage.",
        "Prefer singable ambitus over maximal span.",
    ],
    "stages": [
        {
            "id": "stage_1",
            "title": "Neighbor patterns",
            "target_melody_count": 24,
            "suggested_advance_after": {"comfortable": 12, "stretch": 16},
            "default_support": ["cadence", "first_note"],
            "allowed_adjacent_intervals": ["unison", "second"],
            "allowed_start_degrees": [1, 3, 5],
            "allowed_end_degrees": [1, 3, 5],
            "preferred_end_degrees": [1, 3, 5],
            "stage_rules": [
                "Do not introduce scale degree 7 yet.",
                "Keep the ambitus to a third or smaller.",
                "Allow useful repetition, but avoid making one stable degree dominate.",
            ],
            "families": [
                {
                    "id": "upper_neighbor_return",
                    "count": 6,
                    "role": "Introduce local upward motion around stable tones.",
                    "example_degree_shapes": [[1, 2, 1, 1], [3, 4, 3, 3], [5, 6, 5, 5]],
                },
                {
                    "id": "lower_neighbor_return",
                    "count": 4,
                    "role": "Add a controlled lower-neighbor response around 3 and 5.",
                    "example_degree_shapes": [[3, 2, 3, 3], [5, 4, 5, 5]],
                },
                {
                    "id": "up_plateau_back",
                    "count": 4,
                    "role": "Teach a brief move away from home before a stable return.",
                    "example_degree_shapes": [[1, 2, 2, 1], [3, 4, 4, 3], [5, 6, 6, 5]],
                },
                {
                    "id": "down_plateau_back",
                    "count": 4,
                    "role": "Mirror the plateau idea downward without destabilizing the stage.",
                    "example_degree_shapes": [[3, 2, 2, 3], [5, 4, 4, 5]],
                },
                {
                    "id": "delayed_ascent",
                    "count": 3,
                    "role": "Let the learner hear a stable note before moving upward.",
                    "example_degree_shapes": [[1, 1, 2, 3], [3, 3, 4, 5]],
                },
                {
                    "id": "delayed_descent",
                    "count": 3,
                    "role": "Balance the stage with equally safe downward transfers.",
                    "example_degree_shapes": [[5, 5, 4, 3], [3, 3, 2, 1]],
                },
            ],
        },
        {
            "id": "stage_2",
            "title": "Stable stepwise transfer",
            "target_melody_count": 36,
            "suggested_advance_after": {"comfortable": 12, "stretch": 16},
            "default_support": ["cadence", "first_note"],
            "allowed_adjacent_intervals": ["unison", "second"],
            "allowed_start_degrees": [1, 3, 5],
            "allowed_end_degrees": [1, 3, 5],
            "preferred_end_degrees": [1, 3, 5],
            "stage_rules": [
                "All seven degrees may appear, but keep launch and landing stable.",
                "Use 7 mostly as a passing or resolving tone.",
                "Preserve the feeling that the learner always knows where home is.",
            ],
            "families": [
                {
                    "id": "stable_ascent_transfer",
                    "count": 8,
                    "role": "Expand the tonal map through stepwise upward travel.",
                    "example_degree_shapes": [[1, 2, 3, 3], [3, 4, 5, 5], [5, 6, 7, 1]],
                },
                {
                    "id": "stable_descent_transfer",
                    "count": 8,
                    "role": "Give the same broadening effect in the descending direction.",
                    "example_degree_shapes": [[3, 2, 1, 1], [5, 4, 3, 3], [1, 7, 6, 5]],
                },
                {
                    "id": "upper_neighbor_hold",
                    "count": 6,
                    "role": "Keep some highly reassuring local-return shapes in the mix.",
                    "example_degree_shapes": [[1, 2, 2, 1], [3, 4, 4, 3], [5, 6, 6, 5]],
                },
                {
                    "id": "lower_neighbor_hold",
                    "count": 6,
                    "role": "Mirror the reassurance pattern downward, including 7 to 1.",
                    "example_degree_shapes": [[1, 7, 7, 1], [3, 2, 2, 3], [5, 4, 4, 5]],
                },
                {
                    "id": "delayed_unstable_arrival",
                    "count": 4,
                    "role": "Let unstable tones appear late, after a stable setup.",
                    "example_degree_shapes": [[1, 1, 2, 3], [3, 3, 4, 5], [5, 5, 6, 5]],
                },
                {
                    "id": "tonic_boundary_resolution",
                    "count": 4,
                    "role": "Teach the learner to hear the 7-to-1 seam clearly.",
                    "example_degree_shapes": [[6, 7, 1, 1], [5, 6, 7, 1], [1, 7, 6, 5]],
                },
            ],
        },
        {
            "id": "stage_3",
            "title": "Fully stepwise",
            "target_melody_count": 48,
            "suggested_advance_after": {"comfortable": 14, "stretch": 18},
            "default_support": ["first_note"],
            "allowed_adjacent_intervals": ["unison", "second"],
            "allowed_start_degrees": [1, 2, 3, 4, 5, 6, 7],
            "allowed_end_degrees": [1, 2, 3, 4, 5, 6, 7],
            "preferred_end_degrees": [1, 3, 5],
            "stage_rules": [
                "Allow unfinished endings; not every melody should sound cadence-like.",
                "Spread the starts broadly across all seven degrees.",
                "Do not let one contour family dominate the stage.",
            ],
            "families": [
                {
                    "id": "straight_ascent",
                    "count": 10,
                    "role": "Train clean upward reading without skips.",
                    "example_degree_shapes": [[1, 2, 3, 4], [2, 3, 4, 5], [4, 5, 6, 7]],
                },
                {
                    "id": "straight_descent",
                    "count": 10,
                    "role": "Balance the stage with equally direct downward reading.",
                    "example_degree_shapes": [[4, 3, 2, 1], [7, 6, 5, 4], [5, 4, 3, 2]],
                },
                {
                    "id": "arch",
                    "count": 8,
                    "role": "Introduce a natural rise and fall without changing the interval set.",
                    "example_degree_shapes": [[1, 2, 3, 2], [3, 4, 5, 4], [5, 6, 7, 6]],
                },
                {
                    "id": "valley",
                    "count": 8,
                    "role": "Mirror the arch family with a dip and rebound.",
                    "example_degree_shapes": [[4, 3, 2, 3], [6, 5, 4, 5], [2, 1, 7, 1]],
                },
                {
                    "id": "repeated_arrival",
                    "count": 6,
                    "role": "Use one repeated note to make the line feel more melodic than scalar.",
                    "example_degree_shapes": [[2, 3, 3, 4], [5, 4, 4, 3], [6, 7, 7, 1]],
                },
                {
                    "id": "directional_turn",
                    "count": 6,
                    "role": "Teach quick contour reversal without introducing skips.",
                    "example_degree_shapes": [[2, 3, 2, 1], [5, 4, 5, 6], [6, 7, 6, 5]],
                },
            ],
        },
        {
            "id": "stage_4",
            "title": "First thirds",
            "target_melody_count": 60,
            "suggested_advance_after": {"comfortable": 14, "stretch": 18},
            "default_support": ["first_note"],
            "allowed_adjacent_intervals": ["unison", "second", "third"],
            "allowed_start_degrees": [1, 3, 5],
            "allowed_end_degrees": [1, 3, 5],
            "preferred_end_degrees": [1, 3, 5],
            "stage_rules": [
                "Allow at most one third per melody.",
                "Everything around the third should help explain it.",
                "The leap should feel like the new event, not part of random motion.",
            ],
            "families": [
                {
                    "id": "opening_third_up",
                    "count": 10,
                    "role": "Expose the leap immediately, then recover by step.",
                    "example_degree_shapes": [[1, 3, 2, 1], [3, 5, 4, 3]],
                },
                {
                    "id": "opening_third_down",
                    "count": 10,
                    "role": "Mirror the opening leap downward with stepwise repair.",
                    "example_degree_shapes": [[5, 3, 4, 5], [3, 1, 2, 3]],
                },
                {
                    "id": "interior_third_up",
                    "count": 10,
                    "role": "Hide the leap inside a stepwise shell.",
                    "example_degree_shapes": [[1, 2, 4, 3], [3, 4, 6, 5]],
                },
                {
                    "id": "interior_third_down",
                    "count": 10,
                    "role": "Give the learner an interior downward skip with a clear context.",
                    "example_degree_shapes": [[5, 4, 2, 3], [3, 2, 7, 1]],
                },
                {
                    "id": "closing_third_up",
                    "count": 10,
                    "role": "Let the line arrive by leap after a stepwise setup.",
                    "example_degree_shapes": [[1, 2, 1, 3], [3, 4, 3, 5]],
                },
                {
                    "id": "closing_third_down",
                    "count": 10,
                    "role": "Balance the stage with a downward leap into the arrival.",
                    "example_degree_shapes": [[5, 4, 5, 3], [3, 2, 3, 1]],
                },
            ],
        },
        {
            "id": "stage_5",
            "title": "Thirds integrated",
            "target_melody_count": 72,
            "suggested_advance_after": {"comfortable": 16, "stretch": 20},
            "default_support": ["first_note_optional"],
            "allowed_adjacent_intervals": ["unison", "second", "third"],
            "allowed_start_degrees": [1, 2, 3, 4, 5, 6, 7],
            "allowed_end_degrees": [1, 2, 3, 4, 5, 6, 7],
            "preferred_end_degrees": [1, 3, 5],
            "stage_rules": [
                "Thirds may recur, but avoid ugly consecutive-skip patterns.",
                "Do not let the stage collapse into disguised broken triads.",
                "Keep some lines mostly stepwise so the third feels contextualized.",
            ],
            "families": [
                {
                    "id": "opening_third_gesture",
                    "count": 12,
                    "role": "Normalize the skip at the start of a melody.",
                    "example_degree_shapes": [[1, 3, 2, 3], [2, 4, 3, 4], [3, 5, 4, 5]],
                },
                {
                    "id": "closing_third_gesture",
                    "count": 12,
                    "role": "Make leap-based arrival feel ordinary rather than dramatic.",
                    "example_degree_shapes": [[1, 2, 3, 5], [5, 4, 3, 1]],
                },
                {
                    "id": "two_thirds_separated_by_step",
                    "count": 12,
                    "role": "Use multiple thirds without sounding like an exercise book.",
                    "example_degree_shapes": [[1, 3, 4, 2], [5, 3, 2, 4]],
                },
                {
                    "id": "third_chain_with_recovery",
                    "count": 12,
                    "role": "Allow a more assertive skip profile while keeping recovery clear.",
                    "example_degree_shapes": [[1, 3, 2, 4], [4, 2, 3, 1]],
                },
                {
                    "id": "step_and_skip_arch",
                    "count": 12,
                    "role": "Blend thirds into arch-shaped melodic motion.",
                    "example_degree_shapes": [[2, 3, 5, 4], [4, 5, 3, 4]],
                },
                {
                    "id": "step_and_skip_valley",
                    "count": 12,
                    "role": "Balance the stage with downward contour plus skip recovery.",
                    "example_degree_shapes": [[5, 4, 2, 3], [3, 2, 4, 3]],
                },
            ],
        },
        {
            "id": "stage_6",
            "title": "First fourths",
            "target_melody_count": 72,
            "suggested_advance_after": {"comfortable": 16, "stretch": 20},
            "default_support": ["first_note_optional"],
            "allowed_adjacent_intervals": ["unison", "second", "third", "fourth"],
            "allowed_start_degrees": [1, 3, 5],
            "allowed_end_degrees": [1, 2, 3, 4, 5, 6, 7],
            "preferred_end_degrees": [1, 5],
            "stage_rules": [
                "Allow at most one fourth per melody.",
                "Prefer contrary stepwise recovery after the fourth.",
                "Keep the leap memorable and structurally clear.",
            ],
            "families": [
                {
                    "id": "opening_fourth_up",
                    "count": 12,
                    "role": "Introduce the fourth as an immediately exposed event.",
                    "example_degree_shapes": [[1, 4, 3, 2], [3, 6, 5, 4]],
                },
                {
                    "id": "opening_fourth_down",
                    "count": 12,
                    "role": "Mirror the new leap downward with clear repair motion.",
                    "example_degree_shapes": [[5, 2, 3, 4], [3, 7, 1, 2]],
                },
                {
                    "id": "interior_fourth_up",
                    "count": 10,
                    "role": "Place the fourth after a short preparation.",
                    "example_degree_shapes": [[1, 2, 5, 4], [3, 4, 7, 6]],
                },
                {
                    "id": "interior_fourth_down",
                    "count": 10,
                    "role": "Use a prepared downward fourth that still feels singable.",
                    "example_degree_shapes": [[5, 4, 1, 2], [3, 4, 1, 2]],
                },
                {
                    "id": "prepared_fourth_and_resolution",
                    "count": 14,
                    "role": "Let the leap point toward a strong tonal settling motion.",
                    "example_degree_shapes": [[1, 2, 5, 1], [5, 4, 1, 5]],
                },
                {
                    "id": "single_fourth_inside_step_shell",
                    "count": 14,
                    "role": "Keep the surrounding context easy while the leap itself is new.",
                    "example_degree_shapes": [[1, 4, 3, 1], [5, 2, 3, 5]],
                },
            ],
        },
        {
            "id": "stage_7",
            "title": "Fourths integrated",
            "target_melody_count": 84,
            "suggested_advance_after": {"comfortable": 18, "stretch": 20},
            "default_support": [],
            "allowed_adjacent_intervals": ["unison", "second", "third", "fourth"],
            "allowed_start_degrees": [1, 2, 3, 4, 5, 6, 7],
            "allowed_end_degrees": [1, 2, 3, 4, 5, 6, 7],
            "preferred_end_degrees": [1, 3, 5],
            "stage_rules": [
                "Fourths may recur, but buffer them with stepwise motion or one smaller skip.",
                "Do not allow the stage to become leap-heavy noise.",
                "Maintain a wide mix of contour families.",
            ],
            "families": [
                {
                    "id": "fourth_launch_ascending",
                    "count": 12,
                    "role": "Normalize a fourth at the start of an upward-moving line.",
                    "example_degree_shapes": [[2, 5, 4, 6], [1, 4, 5, 4]],
                },
                {
                    "id": "fourth_launch_descending",
                    "count": 12,
                    "role": "Balance the stage with equally readable downward launches.",
                    "example_degree_shapes": [[6, 3, 4, 2], [5, 2, 3, 4]],
                },
                {
                    "id": "interior_fourth_bridge",
                    "count": 12,
                    "role": "Use a fourth to connect two more local gestures.",
                    "example_degree_shapes": [[2, 3, 6, 5], [5, 4, 1, 2]],
                },
                {
                    "id": "arch_with_fourth_peak",
                    "count": 12,
                    "role": "Make the leap feel like the crest of a phrase fragment.",
                    "example_degree_shapes": [[1, 3, 6, 5], [2, 3, 6, 4]],
                },
                {
                    "id": "valley_with_fourth_floor",
                    "count": 12,
                    "role": "Mirror the previous family with the leap as a low-point reveal.",
                    "example_degree_shapes": [[6, 4, 1, 2], [5, 3, 1, 3]],
                },
                {
                    "id": "two_skips_with_step_buffer",
                    "count": 12,
                    "role": "Allow a richer contour while protecting singability.",
                    "example_degree_shapes": [[1, 4, 5, 2], [5, 2, 3, 6]],
                },
                {
                    "id": "mixed_step_third_fourth",
                    "count": 12,
                    "role": "Prepare the learner for later free vocabulary stages.",
                    "example_degree_shapes": [[2, 4, 5, 1], [5, 3, 4, 7]],
                },
            ],
        },
        {
            "id": "stage_8",
            "title": "First fifths",
            "target_melody_count": 84,
            "suggested_advance_after": {"comfortable": 18, "stretch": 20},
            "default_support": [],
            "allowed_adjacent_intervals": ["unison", "second", "third", "fourth", "fifth"],
            "allowed_start_degrees": [1, 3, 5],
            "allowed_end_degrees": [1, 2, 3, 4, 5, 6, 7],
            "preferred_end_degrees": [1, 5],
            "stage_rules": [
                "Allow at most one fifth per melody.",
                "Strongly prefer contrary stepwise recovery after the fifth.",
                "Keep the stage bold but still clearly beginner-oriented.",
            ],
            "families": [
                {
                    "id": "opening_fifth_up",
                    "count": 14,
                    "role": "Expose the widest leap immediately, then guide the recovery.",
                    "example_degree_shapes": [[1, 5, 4, 3], [3, 7, 6, 5]],
                },
                {
                    "id": "opening_fifth_down",
                    "count": 14,
                    "role": "Mirror the fifth downward with strong tonal repair.",
                    "example_degree_shapes": [[5, 1, 2, 3], [3, 6, 5, 4]],
                },
                {
                    "id": "interior_fifth_up",
                    "count": 12,
                    "role": "Let a short setup prepare the leap.",
                    "example_degree_shapes": [[1, 2, 6, 5], [3, 4, 1, 7]],
                },
                {
                    "id": "interior_fifth_down",
                    "count": 12,
                    "role": "Provide the descending mirror of the previous family.",
                    "example_degree_shapes": [[5, 6, 2, 3], [3, 4, 7, 1]],
                },
                {
                    "id": "fifth_with_contrary_step_recovery",
                    "count": 16,
                    "role": "Make recovery behavior extremely clear and teachable.",
                    "example_degree_shapes": [[1, 5, 4, 5], [5, 1, 2, 1]],
                },
                {
                    "id": "fifth_with_supporting_small_skip",
                    "count": 16,
                    "role": "Surround the large leap with one smaller skip for variety.",
                    "example_degree_shapes": [[1, 5, 3, 2], [5, 1, 3, 4]],
                },
            ],
        },
        {
            "id": "stage_9",
            "title": "Full version 1 vocabulary",
            "target_melody_count": 96,
            "suggested_advance_after": {"comfortable": 20, "stretch": 20},
            "default_support": [],
            "allowed_adjacent_intervals": ["unison", "second", "third", "fourth", "fifth"],
            "allowed_start_degrees": [1, 2, 3, 4, 5, 6, 7],
            "allowed_end_degrees": [1, 2, 3, 4, 5, 6, 7],
            "preferred_end_degrees": [1, 3, 5],
            "stage_rules": [
                "Seconds, thirds, fourths, and fifths are all available.",
                "Musical quality still matters more than raw interval coverage.",
                "Use this stage to sound like real beginner melodies, not controlled drills.",
            ],
            "families": [
                {
                    "id": "opening_leap_control",
                    "count": 16,
                    "role": "Allow stronger openings while keeping the rest coherent.",
                    "example_degree_shapes": [[2, 5, 4, 6], [4, 1, 2, 3]],
                },
                {
                    "id": "closing_leap_control",
                    "count": 16,
                    "role": "Make leap-based arrivals feel normal and readable.",
                    "example_degree_shapes": [[2, 3, 4, 7], [6, 5, 4, 1]],
                },
                {
                    "id": "arch_mixed_intervals",
                    "count": 14,
                    "role": "Use a phrase-like rise and fall with mixed interval sizes.",
                    "example_degree_shapes": [[1, 3, 6, 5], [2, 4, 7, 6]],
                },
                {
                    "id": "valley_mixed_intervals",
                    "count": 14,
                    "role": "Mirror the arch family with a lower-center contour.",
                    "example_degree_shapes": [[6, 4, 1, 2], [5, 3, 1, 3]],
                },
                {
                    "id": "double_skip_but_singable",
                    "count": 12,
                    "role": "Allow more interval richness while retaining clear recovery.",
                    "example_degree_shapes": [[1, 3, 6, 5], [6, 4, 2, 3]],
                },
                {
                    "id": "tonic_avoidant_launch",
                    "count": 12,
                    "role": "Force broader internal hearing by not always starting at home.",
                    "example_degree_shapes": [[2, 4, 5, 3], [6, 7, 5, 4]],
                },
                {
                    "id": "cadence_like_closures",
                    "count": 12,
                    "role": "Keep some satisfying closures in the final stage mix.",
                    "example_degree_shapes": [[2, 5, 1, 1], [6, 5, 4, 1]],
                },
            ],
        },
    ],
}


def total_target_melodies() -> int:
    """Return the canonical target size of the fixed library."""
    return sum(
        stage["target_melody_count"] for stage in FIXED_AUDIO_CURRICULUM["stages"]
    )


def _validate_curriculum() -> None:
    total = 0
    for stage in FIXED_AUDIO_CURRICULUM["stages"]:
        family_total = sum(family["count"] for family in stage["families"])
        if family_total != stage["target_melody_count"]:
            raise ValueError(
                f"{stage['id']} family count {family_total} does not match "
                f"target {stage['target_melody_count']}"
            )
        total += family_total

    if total != TOTAL_CANONICAL_MELODIES:
        raise ValueError(
            f"Curriculum total {total} does not match "
            f"{TOTAL_CANONICAL_MELODIES}"
        )


_validate_curriculum()
