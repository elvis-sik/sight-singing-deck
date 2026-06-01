"""Finite staged curriculum spec for the rhythm-first deck family."""

from __future__ import annotations

TOTAL_CANONICAL_RHYTHM_CARDS = 408
TOTAL_CANONICAL_MERGE_CARDS = 234


RHYTHM_CURRICULUM = {
    "version": 1,
    "threads": {
        "pitch_first": {
            "summary": (
                "Use the existing melody curriculum with little or no rhythmic "
                "complexity until merge."
            ),
            "recommended_rhythm_policy": "Mostly quarter-note based until merge.",
        },
        "rhythm_first": {
            "summary": (
                "Teach rhythmic decoding on a repeated pitch so the learner is not "
                "simultaneously solving melody and rhythm."
            ),
            "default_rendering": {
                "count_in": "optional_1_or_2_beats",
                "cadence": False,
                "default_pitch_treble": "B4",
                "default_pitch_bass": "D3",
            },
        },
        "merge": {
            "summary": (
                "Curate combined pitch-and-rhythm cards instead of taking a full "
                "cross-product of both threads."
            )
        },
    },
    "advance_policy": {
        "default_guideline": "Advance after roughly 10-18 strong cards in a stage."
    },
    "global_quality_rules": [
        "Every bar should feel musically plausible, not merely legal.",
        "Introduce only one genuinely new rhythmic idea per stage.",
        "Do not let every beat in a bar use the same cell unless the stage requires it.",
        "Mix sparse, medium, and denser attack patterns inside each stage.",
        "In dotted, tied, and triplet stages, keep the surrounding context plain.",
        "Reject ugly but technically valid bars.",
    ],
    "rhythm_stages": [
        {
            "id": "r1",
            "title": "Pulse and duration",
            "target_count": 24,
            "advance_after": {"comfortable": 10, "stretch": 12},
            "allowed_values": ["q", "h", "w"],
            "stage_rules": [
                "No rests yet.",
                "All attacks happen on beat.",
                "Subdivision is not yet introduced.",
            ],
            "families": [
                {"id": "four_quarters", "count": 6},
                {"id": "two_halves", "count": 4},
                {"id": "whole_note_bar", "count": 2},
                {"id": "half_then_two_quarters", "count": 6},
                {"id": "two_quarters_then_half", "count": 6},
            ],
        },
        {
            "id": "r2",
            "title": "Silence and entry",
            "target_count": 30,
            "advance_after": {"comfortable": 10, "stretch": 14},
            "allowed_values": ["q", "h", "w", "qr"],
            "stage_rules": [
                "Add quarter rests only.",
                "Attacks still happen only on beat.",
            ],
            "families": [
                {"id": "quarter_rest_then_motion", "count": 6},
                {"id": "motion_then_quarter_rest", "count": 6},
                {"id": "interior_quarter_rest", "count": 6},
                {"id": "half_rest_equivalent_feel", "count": 6},
                {"id": "rested_arrival_bar", "count": 6},
            ],
        },
        {
            "id": "r3",
            "title": "First eighth pairs",
            "target_count": 36,
            "advance_after": {"comfortable": 12, "stretch": 14},
            "allowed_values": ["q", "h", "w", "qr", "8+8"],
            "stage_rules": [
                "Use eighths only as paired subdivisions inside one beat.",
                "No isolated offbeat attacks yet.",
            ],
            "families": [
                {"id": "single_eighth_pair", "count": 8},
                {"id": "two_eighth_pairs", "count": 8},
                {"id": "eighth_pair_opening", "count": 6},
                {"id": "eighth_pair_closing", "count": 6},
                {"id": "eighth_pair_between_quarters", "count": 8},
            ],
        },
        {
            "id": "r4",
            "title": "Mixed beat fillings",
            "target_count": 42,
            "advance_after": {"comfortable": 12, "stretch": 16},
            "allowed_values": ["q", "h", "w", "qr", "8+8"],
            "stage_rules": [
                "Any beat may be quarter or paired eighths.",
                "Use half notes only as contrast.",
            ],
            "families": [
                {"id": "quarter_vs_pair_contrast", "count": 10},
                {"id": "paired_center", "count": 8},
                {"id": "paired_edges", "count": 8},
                {"id": "half_plus_subdivision", "count": 8},
                {"id": "three_density_levels", "count": 8},
            ],
        },
        {
            "id": "r5",
            "title": "Offbeat feel",
            "target_count": 48,
            "advance_after": {"comfortable": 14, "stretch": 16},
            "allowed_values": ["q", "h", "qr", "8+8", "8r+8"],
            "stage_rules": [
                "Allow weak-beat entries.",
                "Do not use ties yet.",
            ],
            "families": [
                {"id": "eighth_rest_pickup", "count": 10},
                {"id": "offbeat_answer", "count": 10},
                {"id": "quarter_then_offbeat", "count": 10},
                {"id": "offbeat_then_quarter", "count": 8},
                {"id": "mixed_onbeat_offbeat", "count": 10},
            ],
        },
        {
            "id": "r6",
            "title": "Dotted patterns",
            "target_count": 48,
            "advance_after": {"comfortable": 14, "stretch": 18},
            "allowed_values": ["q", "h", "qr", "8+8", "8r+8", "q.+8"],
            "stage_rules": [
                "Introduce dotted quarter plus eighth as the main new idea.",
                "Keep surrounding beats plain.",
            ],
            "families": [
                {"id": "single_dotted_figure", "count": 12},
                {"id": "dotted_opening", "count": 8},
                {"id": "dotted_closing", "count": 8},
                {"id": "dotted_between_plain_beats", "count": 10},
                {"id": "two_dotted_figures_separated", "count": 10},
            ],
        },
        {
            "id": "r7",
            "title": "Ties across beats",
            "target_count": 54,
            "advance_after": {"comfortable": 14, "stretch": 18},
            "allowed_values": ["q", "h", "qr", "8+8", "8r+8", "q.+8", "ties"],
            "stage_rules": [
                "Teach sustain across beat boundaries.",
                "Use same-pitch tie clarity in the rhythm-only track.",
            ],
            "families": [
                {"id": "quarter_tied_to_quarter", "count": 10},
                {"id": "quarter_tied_to_eighth", "count": 10},
                {"id": "eighth_tied_across_beat", "count": 10},
                {"id": "single_tie_in_plain_bar", "count": 12},
                {"id": "tie_with_rest_context", "count": 12},
            ],
        },
        {
            "id": "r8",
            "title": "Triplet pulse",
            "target_count": 54,
            "advance_after": {"comfortable": 14, "stretch": 18},
            "allowed_values": [
                "q",
                "h",
                "qr",
                "8+8",
                "8r+8",
                "q.+8",
                "ties",
                "triplet_8",
            ],
            "stage_rules": [
                "Use beat-level eighth-note triplets only.",
                "No nested tuplets or combined triplet-plus-tie complexity yet.",
            ],
            "families": [
                {"id": "single_triplet_beat", "count": 12},
                {"id": "triplet_opening", "count": 10},
                {"id": "triplet_closing", "count": 10},
                {"id": "triplet_between_plain_beats", "count": 10},
                {"id": "two_triplet_beats", "count": 12},
            ],
        },
        {
            "id": "r9",
            "title": "Full v1 rhythm",
            "target_count": 72,
            "advance_after": {"comfortable": 16, "stretch": 18},
            "allowed_values": [
                "q",
                "h",
                "w",
                "qr",
                "8+8",
                "8r+8",
                "q.+8",
                "ties",
                "triplet_8",
            ],
            "stage_rules": [
                "Integrate the full beginner rhythm vocabulary.",
                "At most one hard event family should dominate a bar.",
            ],
            "families": [
                {"id": "plain_with_one_spice", "count": 16},
                {"id": "syncopated_answer_bar", "count": 12},
                {"id": "dotted_or_tied_center", "count": 12},
                {"id": "triplet_contrast_bar", "count": 12},
                {"id": "dense_vs_sparse_pairing", "count": 10},
                {"id": "phrase_like_beginner_bar", "count": 10},
            ],
        },
    ],
    "merge_stages": [
        {"id": "m1", "title": "Stepwise plus pulse rhythms", "target_count": 36},
        {"id": "m2", "title": "Thirds plus subdivision", "target_count": 42},
        {"id": "m3", "title": "Fourths plus offbeat feel", "target_count": 48},
        {"id": "m4", "title": "Fifths plus sustained rhythm", "target_count": 48},
        {"id": "m5", "title": "Full v1 merge", "target_count": 60},
    ],
}
