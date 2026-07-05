"""Machine-readable v2 curriculum stages (see CURRICULUM.md).

Stages are expressed as *constraint specs* over **diatonic indices** (0 = tonic,
1 = 2nd, ... 7 = octave, -1 = the degree below the tonic). The generator
enumerates melodies from `pool` under the interval/start/end constraints and the
musicality rules, then samples a diverse set of `count` melodies.

The ordering is FUNCTION-FIRST: so-mi, then the tonic triad (easy leaps), then
steps, then tendency tones, then wider leaps — not raw interval size.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace


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
    min_step: int = 0  # min adjacent step; set == max_step to pin an interval
    default_support: tuple[str, ...] = ("cadence", "first")
    # rule flags
    max_direction_changes: int = 3
    allow_three_repeats: bool = False
    require_leap: bool = False  # stage introduces a leap -> require one
    require_leap_min: int = 0  # require >=1 adjacent leap of at least this
    #   diatonic size (1=2nd .. 4=5th). Forces a *headline* stage (M6/M8) to
    #   actually contain its named interval, not just any >=3rd.
    max_leaps: int | None = None  # cap on notes reached by a >2nd
    # Reject any adjacent melodic tritone (6 semitones — a fa<->ti leap). Off in
    # tonal music for beginners: it is the single hardest interval to sing and is
    # avoided as a bare leap. Mode-aware (see melody_gen), so it also strips the
    # tritone out of the "fourths"/"fifths" interval drills.
    forbid_tritone_leap: bool = True
    require_recovery: bool = True  # after a >=3rd, step back the other way
    require_tendency_resolution: bool = False  # ti->do, fa->mi resolve by step
    require_tendency_present: bool = False
    # Which diatonic-index positions (mod 7) are tendency tones and how they must
    # resolve. Defaults are MAJOR: leading tone ti (index 6) pulls up to do; fa
    # (index 3) pulls down to mi. Minor stages override these (the half-steps sit
    # at different scale positions, and harmonic minor adds a raised leading tone).
    tendency_up_from: tuple[int, ...] = (6,)  # must step +1
    tendency_down_from: tuple[int, ...] = (3,)  # must step -1
    # Realization mode override (None -> use the caller's mode). Lets a minor
    # ladder run mostly in natural minor but raise a harmonic-minor leading-tone
    # stage without changing the others.
    mode: str | None = None
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
        pool=(D3, D5, D6), start_pool=(D3, D5), end_pool=(D3, D5, D6),
        max_step=2, count=12, require_present_any=(D6,),
        notes="Add la above so; the children's-chant set. La must appear "
              "(else it is just So–Mi again).",
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
        max_step=1, count=20, max_direction_changes=2, require_present_any=(D2, D4),
        notes="Fill the low pentachord by step; re/fa connect the triad tones "
              "(require one of them, or it collapses to a triad-tone neighbourhood).",
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
        end_pool=(D1, D5, D8), max_step=3, count=24, length=5, require_leap=True,
        require_leap_min=3, max_leaps=1,
        default_support=("first_optional",),
        notes="One controlled fourth (sol->do, do->fa) inside a short phrase, "
              "with stepwise recovery.",
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
        end_pool=(D1, D5, D8), max_step=5, count=24, length=5, require_leap=True,
        require_leap_min=4, max_leaps=1,
        default_support=(),
        notes="do->sol, do->la: the widest v1 leaps, inside a short phrase with "
              "strong stepwise recovery.",
    ),
    Stage(
        "M9", "Free Diatonic Melodies", "leaps",
        pool=(DL7, D1, D2, D3, D4, D5, D6, D7, D8), start_pool=(D1, D2, D3, D4, D5),
        end_pool=(D1, D3, D5, D8), max_step=4, count=56, length=6, max_leaps=3,
        default_support=(),
        notes="Real beginner melodies, longer phrases, mixed intervals.",
    ),
]

# --- Minor ladder ------------------------------------------------------------
# La-based minor: the tonic triad is la-do-mi = diatonic indices 0, 2, 4 — the
# SAME indices as the major tonic triad (do-mi-so). Because the whole ladder is
# anchored to those triad indices, the structural stages (triad, steps, leaps)
# are function-correct when simply realized in natural minor; only the tendency
# tones differ (minor's half-steps sit at ti->do and fa->mi, i.e. indices 1 and
# 5), and harmonic minor adds a raised leading tone (si, index 6 -> la).

# Titles reflect minor solfège (index 0=la, 2=do, 4=mi, ...); everything else is
# inherited from the matching major stage's constraint spec.
_MINOR_TITLES = {
    "M0_1": "La–Do–Mi Core (do–mi)",
    "M0_2": "Do–Mi–Fa",
    "M0_3": "The Minor Triad (la–do–mi)",
    "M0_4": "Lower Tetrachord (la–ti–do)",
    "M1": "Stepwise Around Anchors",
    "M2": "The Whole Scale (minor)",
    "M4": "Free Stepwise",
    "M5": "Thirds Integrated",
    "M6": "Perfect Fourths",
    "M7": "Fourths Integrated",
    "M8": "Fifths & Sixths",
    "M9": "Free Diatonic Melodies (minor)",
}


def _to_minor(stage: Stage) -> Stage:
    """Recast a major structural stage as its natural-minor counterpart."""
    return replace(
        stage,
        id="N" + stage.id[1:],
        title=_MINOR_TITLES.get(stage.id, stage.title),
        phase="minor-" + stage.phase,
        mode="natural_minor",
        # Structural stages carry no tendency requirements; make that explicit so
        # no major-specific tendency config leaks in.
        require_tendency_present=False,
        require_tendency_resolution=False,
        tendency_up_from=(1,),
        tendency_down_from=(5,),
    )


_MINOR_STRUCTURAL = [_to_minor(s) for s in MAJOR_STAGES if s.id != "M3"]

# Natural-minor tendency stage (replaces major M3): fa->mi and ti->do resolve by
# half-step. In la-based minor those half-steps sit at indices 5 (fa) and 1 (ti).
_N3_NATURAL = Stage(
    "N3", "Fa Wants Mi / Ti Wants Do (minor)", "minor-steps",
    pool=(DL7, D1, D2, D3, D4, D5, D6, D7), start_pool=(D1, D2, D3, D5),
    end_pool=(D1, D3, D5), max_step=1, count=24, max_direction_changes=3,
    mode="natural_minor",
    require_tendency_present=True, require_tendency_resolution=True,
    tendency_up_from=(1,), tendency_down_from=(5,),
    default_support=("first",),
    notes="Natural-minor half-steps: ti->do (index 1) and fa->mi (index 5).",
)

# Harmonic-minor leading-tone stage: the raised 7 (si, index 6 in harmonic minor)
# is a real leading tone pulling up a half-step to la. Thirds allowed so si can
# be reached without the awkward augmented 2nd (fa is left out of the pool).
_N3_HARMONIC = Stage(
    "N7h", "The Raised 7th — Harmonic Minor (si->la)", "minor-tendency",
    pool=(D1, D3, D4, D5, D7, D8), start_pool=(D1, D3, D5),
    end_pool=(D1, D8), max_step=2, count=24, length=5, max_leaps=2,
    mode="harmonic_minor",
    require_tendency_present=True, require_tendency_resolution=True,
    require_present_any=(D7,),  # si (raised 7) must actually appear
    tendency_up_from=(6,), tendency_down_from=(),
    require_recovery=False,
    default_support=("first",),
    notes="Harmonic minor's leading tone si (index 6) resolves up to la; "
          "cadential figures like mi-si-la and do-re-si-la.",
)

# Order: foundations & steps, the natural tendency stage in the M3 slot, then the
# rest, with the harmonic-minor leading tone as a capstone.
MINOR_STAGES: list[Stage] = []
for _s in _MINOR_STRUCTURAL:
    MINOR_STAGES.append(_s)
    if _s.id == "N2":  # insert the natural-minor tendency stage after N2
        MINOR_STAGES.append(_N3_NATURAL)
MINOR_STAGES.append(_N3_HARMONIC)


# --- Interval-singing challenge -----------------------------------------------
# Isolated two-note drills: hear the first note (the template establishes the key
# first), then sing up or down to the second. Each stage pins ONE diatonic
# interval (min_step == max_step) and the generator yields both directions across
# the range. No template change — these are ordinary length-2 melodies rendered
# by the Sing card.
_INTERVALS = [
    ("IV2", "Diatonic Seconds", 1),
    ("IV3", "Diatonic Thirds", 2),
    ("IV4", "Fourths", 3),
    ("IV5", "Fifths", 4),
    ("IV6", "Sixths", 5),
    ("IV7", "Sevenths", 6),
    ("IV8", "The Octave", 7),
]

_INTERVAL_POOL = (DL7, D1, D2, D3, D4, D5, D6, D7, D8)

INTERVAL_STAGES: list[Stage] = [
    Stage(
        stage_id, title, "intervals",
        pool=_INTERVAL_POOL, start_pool=_INTERVAL_POOL, end_pool=_INTERVAL_POOL,
        max_step=step, min_step=step, count=12, length=2,
        require_recovery=False, default_support=("cadence", "first"),
        notes=f"Isolated {title.lower()}, ascending and descending, in key.",
    )
    for stage_id, title, step in _INTERVALS
]


STAGES_BY_ID = {
    s.id: s for s in (*MAJOR_STAGES, *MINOR_STAGES, *INTERVAL_STAGES)
}
