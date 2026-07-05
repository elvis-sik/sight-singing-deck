"""Machine-readable v2 curriculum stages (see CURRICULUM.md).

Stages are expressed as *constraint specs* over **diatonic indices** (0 = tonic,
1 = 2nd, ... 7 = octave, -1 = the degree below the tonic). The generator
enumerates melodies from `pool` under the interval/start/end constraints and the
musicality rules, then samples a diverse set of `count` melodies.

The ordering is FUNCTION-FIRST: so-mi, then the tonic triad (easy leaps), then
steps, then tendency tones, then wider leaps — not raw interval size.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Stage:
    id: str
    title: str
    phase: str
    pool: tuple[int, ...]  # diatonic indices available
    start_pool: tuple[int, ...]
    end_pool: tuple[int, ...]
    max_step: int  # max adjacent diatonic step (1=2nd, 2=3rd, 3=4th, 4=5th)
    count: int  # target canonical melodies to keep
    length: int = 4
    default_support: tuple[str, ...] = ("cadence", "first")
    # rule flags
    max_direction_changes: int = 3
    allow_three_repeats: bool = False
    require_leap: bool = False  # stage introduces a leap -> require one
    max_leaps: int | None = None  # cap on notes reached by a >2nd
    require_recovery: bool = True  # after a >=3rd, step back the other way
    require_tendency_resolution: bool = False  # ti->do, fa->mi resolve by step
    require_tendency_present: bool = False
    # At least one note whose diatonic index is in this set must appear. Used to
    # make each step stage foreground the *new* degree it introduces (so nested
    # pools like M0_4 c M1 c M2 don't all lead with the same low melody).
    require_present_any: tuple[int, ...] = field(default_factory=tuple)
    notes: str = ""
    families_hint: tuple[str, ...] = field(default_factory=tuple)


# Convenience: scale-degree number -> its diatonic index in the base octave.
D1, D2, D3, D4, D5, D6, D7, D8 = 0, 1, 2, 3, 4, 5, 6, 7  # D8 = octave tonic
DL7 = -1  # leading tone / subtonic below the tonic (lower neighbour of 1)

MAJOR_STAGES: list[Stage] = [
    # ---- Phase 0: tonal foundation (triad core) ----
    Stage(
        "M0_1", "So–Mi", "foundation",
        pool=(D3, D5), start_pool=(D3, D5), end_pool=(D3, D5),
        max_step=2, count=10, default_support=("cadence", "first"),
        allow_three_repeats=True,
        notes="The universal first interval: sol–mi, up/down/hold/return.",
        families_hint=("so_mi_call", "mi_so_return"),
    ),
    Stage(
        "M0_2", "So–Mi–La", "foundation",
        pool=(D3, D5, D6), start_pool=(D3, D5), end_pool=(D3, D5),
        max_step=2, count=14,
        notes="Add la above so; the children's-chant set.",
    ),
    Stage(
        "M0_3", "The Triad Anchors", "foundation",
        pool=(D1, D3, D5, D8), start_pool=(D1, D3, D5, D8), end_pool=(D1, D5, D8),
        max_step=3, count=16, require_recovery=False,
        notes="do–mi–sol as leaps: the easy, harmonic-skeleton leaps.",
        families_hint=("triad_ascend", "triad_descend", "arpeggio_return"),
    ),
    Stage(
        "M0_4", "Lower Tetrachord", "foundation",
        pool=(D1, D2, D3), start_pool=(D1, D3), end_pool=(D1, D3),
        max_step=1, count=12,
        notes="do–re–mi: first true steps.",
    ),
    # ---- Phase 1: diatonic steps, triad-anchored ----
    Stage(
        "M1", "Stepwise Around Anchors", "steps",
        pool=(D1, D2, D3, D4, D5), start_pool=(D1, D3, D5), end_pool=(D1, D3, D5),
        max_step=1, count=20, max_direction_changes=2, require_present_any=(D4,),
        notes="Fill the low pentachord by step; fa/re connect the triad tones.",
    ),
    Stage(
        "M2", "The Whole Scale", "steps",
        pool=(D1, D2, D3, D4, D5, D6, D7, D8), start_pool=(D1, D3, D5),
        end_pool=(D1, D3, D5, D8), max_step=1, count=28, length=6,
        max_direction_changes=3, require_present_any=(D6, D7),
        notes="Longer stepwise phrases spanning do-to-octave; 6 and 7 in context.",
    ),
    Stage(
        "M3", "Ti Wants Do / Fa Wants Mi", "steps",
        pool=(DL7, D1, D2, D3, D4, D5, D6, D7), start_pool=(D1, D2, D3, D5),
        end_pool=(D1, D3, D5), max_step=1, count=24, max_direction_changes=3,
        require_tendency_present=True, require_tendency_resolution=True,
        default_support=("first",),
        notes="Feature ti->do and fa->mi resolutions: tendency tones as the lesson.",
    ),
    Stage(
        "M4", "Free Stepwise", "steps",
        pool=(DL7, D1, D2, D3, D4, D5, D6, D7, D8), start_pool=(DL7, D1, D2, D3, D4, D5, D6, D7),
        end_pool=(DL7, D1, D2, D3, D4, D5, D6, D7, D8), max_step=1, count=36,
        max_direction_changes=3, default_support=("first",),
        notes="Any launch/arrival; unfinished endings break cadence dependence.",
    ),
    # ---- Phase 2: leaps by function ----
    Stage(
        "M5", "Thirds Integrated", "leaps",
        pool=(D1, D2, D3, D4, D5, D6, D7, D8), start_pool=(D1, D3, D5),
        end_pool=(D1, D3, D5, D8), max_step=2, count=40, max_leaps=2,
        default_support=("first",),
        notes="Thirds become ordinary vocabulary; steps still dominate.",
    ),
    Stage(
        "M6", "Perfect Fourths", "leaps",
        pool=(DL7, D1, D2, D3, D4, D5, D6, D7, D8), start_pool=(D1, D3, D5),
        end_pool=(D1, D5, D8), max_step=3, count=44, require_leap=True, max_leaps=1,
        default_support=("first_optional",),
        notes="One controlled fourth (sol->do, do->fa) with stepwise recovery.",
    ),
    Stage(
        "M7", "Fourths Integrated", "leaps",
        pool=(DL7, D1, D2, D3, D4, D5, D6, D7, D8), start_pool=(D1, D2, D3, D4, D5, D6, D7),
        end_pool=(D1, D3, D5, D8), max_step=3, count=48, max_leaps=2,
        default_support=("first_optional",),
        notes="Fourths behave like normal melodic events, buffered by steps.",
    ),
    Stage(
        "M8", "Fifths & Sixths", "leaps",
        pool=(DL7, D1, D2, D3, D4, D5, D6, D7, D8), start_pool=(D1, D3, D5),
        end_pool=(D1, D5, D8), max_step=5, count=48, require_leap=True, max_leaps=1,
        default_support=(),
        notes="do->sol, do->la: the widest v1 leaps, with strong recovery.",
    ),
    Stage(
        "M9", "Free Diatonic Melodies", "leaps",
        pool=(DL7, D1, D2, D3, D4, D5, D6, D7, D8), start_pool=(D1, D2, D3, D4, D5),
        end_pool=(D1, D3, D5, D8), max_step=4, count=56, length=6, max_leaps=3,
        default_support=(),
        notes="Real beginner melodies, longer phrases, mixed intervals.",
    ),
]

STAGES_BY_ID = {s.id: s for s in MAJOR_STAGES}
