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
    # Minimum number of DISTINCT diatonic indices the melody must use. Anti-noodle
    # rule for dictation: a loose stepwise spec otherwise yields dull neighbour
    # oscillation (do-re-do-do); requiring N distinct pitches forces real motion.
    min_distinct: int = 0
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


# --- Dictation curriculum (melodic spine) ----------------------------------
# See DICTATION_CURRICULUM.md (rev 3). Dictation is ordered by phrase length +
# working memory + interval audibility, NOT vocal difficulty, and draws its own
# pool. These are the PITCH-ONLY, even-rhythm stages (no rests → clean exact-match
# grading); rhythm is a separate strand (see the RD track) and pitch+rhythm
# integration waits on new generation logic, so it is intentionally absent here.
#
# Design rules enforced against the review pass (see the doc):
#   * ONE new variable per rung — a rung raises length OR introduces one interval
#     class, never both. Steps are pushed to length 6 (DD5) BEFORE any leap, then
#     length resets to 4 for thirds (DD6) and again for 4ths/5ths (DD7).
#   * NO immediate repeats in any pitch-only stage — enforced via `min_step >= 1`
#     (a repeat is an adjacent step of 0, which `min_step` rejects). Repeats carry
#     no pitch information in even rhythm and smuggle in a counting/rhythm task.
#   * INTERVAL CEILING is hard per stage via `max_step`; `max_step <= 4` (a 5th)
#     means the strand never produces a 6th.
#   * OBJECTIVE COVERAGE is enforced, not hoped for: DD8 pairs the tendency
#     resolution rule with `require_present_any=(ti)` so EVERY item actually
#     contains ti→do (the review found the old tendency stage claimed ti→do yet
#     produced none). tests/test_dictation_ladder.py asserts these invariants.
#
# A short priming floor (DP0–DP2) sits below the old first rung: a true beginner
# needs single-degree identification and 2-note fragments before 3-note melodies.
_DTRIAD = (D1, D3, D5)
_DPENTA = (D1, D2, D3, D4, D5)
_DFULL = (D1, D2, D3, D4, D5, D6, D7, D8)
_DFULL_L = (DL7, *_DFULL)  # full scale + the lower leading tone (ti, below do)

# DP0 · Tonic Echo — hear the key, then identify ONE degree against it. A single
# note is not a "melody" (the generator correctly rejects monotone sequences), so
# this rung is a fixed set the builder emits directly rather than generating. The
# pillars {do, mi, so} are the most stable anchors to start from.
DICTATION_PRIMING_SINGLETONS: tuple[tuple[int, ...], ...] = ((D1,), (D3,), (D5,))

DICTATION_STAGES: list[Stage] = [
    # ---- Priming floor: below the old first rung ----
    Stage(
        "DP1", "Two-Note Pillars", "dictation",
        pool=_DTRIAD, start_pool=_DTRIAD, end_pool=_DTRIAD,
        max_step=4, min_step=2, length=2, count=6,
        require_recovery=False, max_direction_changes=1,
        notes="Two triad tones, either direction: relate a second stable pitch to "
              "the tonic. The true rung 1.",
    ),
    Stage(
        "DP2", "Two-Note Step", "dictation",
        pool=_DPENTA, start_pool=_DPENTA, end_pool=_DPENTA,
        max_step=1, min_step=1, length=2, count=8,
        require_recovery=False, max_direction_changes=1,
        notes="A single adjacent step up or down, incl. the mi–fa half-step: "
              "hear step-size before stringing steps together.",
    ),
    # ---- Length ramp on STEPS ONLY (isolate length from leaps) ----
    Stage(
        "DD1", "The Triad Skeleton", "dictation",
        pool=_DTRIAD, start_pool=_DTRIAD, end_pool=_DTRIAD,
        max_step=4, min_step=2, length=3, count=6, min_distinct=3,
        require_recovery=False, max_direction_changes=2,
        notes="The six orderings of do-mi-so (min_distinct=3 pins them to the true "
              "permutations): hear the stable pitches against a firm key. Leaps "
              "here land only on triad tones (the easy case).",
    ),
    Stage(
        "DD2", "Stepwise Neighbors", "dictation",
        pool=_DPENTA, start_pool=_DTRIAD, end_pool=(D1, D3, D5),
        max_step=1, min_step=1, length=3, count=8, min_distinct=2,
        require_recovery=False,
        notes="Short conjunct fragments, mi–fa half-step featured: step vs. skip.",
    ),
    Stage(
        "DD3", "The Pentachord", "dictation",
        # Length-4 stepwise with no repeats flips parity 3 times, so a triad->triad
        # phrase is impossible (all triad tones are even indices). Allow any
        # pentachord launch/arrival so the stage yields both closing shapes
        # (fa-mi-re-do) and open ones (do-re-mi-fa); scoring still prefers tonic
        # arrivals.
        pool=_DPENTA, start_pool=_DPENTA, end_pool=_DPENTA,
        max_step=1, min_step=1, length=4, count=12, min_distinct=3,
        notes="Length 4, stepwise, traversing do–sol (fa in context).",
    ),
    Stage(
        "DD4", "Into the Upper Scale", "dictation",
        pool=_DFULL, start_pool=_DPENTA, end_pool=(D1, D3, D5, D6, D8),
        max_step=1, min_step=1, length=5, count=14, min_distinct=3,
        require_present_any=(D6, D7, D8),
        notes="Length 5, stepwise, reaching la/ti/do′ and settling.",
    ),
    Stage(
        "DD5", "Long Stepwise Phrases", "dictation",
        pool=_DFULL, start_pool=_DPENTA, end_pool=(D1, D3, D5, D6, D8),
        max_step=1, min_step=1, length=6, count=18, min_distinct=4,
        require_present_any=(D6, D7, D8),
        notes="Length pushed to 6 with STEPS ONLY — length is the sole new "
              "variable before any leap appears. Pure chunking/memory.",
    ),
    # ---- Leaps enter — length RESETS to 4, one interval class at a time ----
    Stage(
        "DD6", "Skips of a Third", "dictation",
        pool=_DFULL, start_pool=_DTRIAD, end_pool=(D1, D3, D5, D8),
        max_step=2, min_step=1, length=4, count=16,
        require_leap=True, require_leap_min=2, max_leaps=2, min_distinct=3,
        notes="Reset to length 4; add the 3rd (the most audible leap). Steps + "
              "≥1 third, ceiling a 3rd.",
    ),
    Stage(
        "DD7", "Fourths & Fifths", "dictation",
        pool=_DFULL_L, start_pool=_DTRIAD, end_pool=(D1, D5, D8),
        max_step=4, min_step=1, length=4, count=16,
        require_leap_min=3, max_leaps=2, require_recovery=True, min_distinct=3,
        notes="Still length 4; add the P4/P5 (no tritone), landing on framework "
              "tones and recovering by step. Ceiling a 5th — never a 6th.",
    ),
    # ---- Length grows again; then the capstone ----
    Stage(
        "DD8", "Tendency Tones (the leading tone)", "dictation",
        pool=_DFULL_L, start_pool=(D1, D2, D3, D4, D5), end_pool=(D1, D3, D5, D8),
        max_step=2, min_step=1, length=5, count=16, min_distinct=3,
        max_leaps=2, require_recovery=False,
        require_tendency_present=True, require_tendency_resolution=True,
        require_present_any=(D7, DL7),
        # Only the leading tone is held to resolution here; fa is left free.
        # Forcing EVERY fa to descend (the generic default) rejects any ascending
        # line through fa — even the plain major scale fa-so — and starved the
        # stage to ~4 items. ti is the tendency the review found missing, so we
        # force it: require_present_any=(ti, ti,) + resolution => ti→do in EVERY
        # item. fa→mi is trained across the stepwise stages (DD2's so-fa-mi …) and
        # still appears here. Thirds are already learned (DD6/DD7), so approaching
        # the leading tone by a ≤3rd is not a new variable — it just lifts yield
        # and musicality (fa-mi-so-ti-do′, so-fa-la-ti-do′).
        tendency_up_from=(6,), tendency_down_from=(),
        notes="Foreground the leading tone: ti→do resolves in every item (the "
              "review found the old tendency stage claimed ti→do yet produced "
              "none). Length grows 4→5; no new leap class (≤3rd, already learned).",
    ),
    Stage(
        "DD9", "Free Diatonic (capstone)", "dictation",
        pool=_DFULL_L, start_pool=_DPENTA, end_pool=(D1, D3, D5, D8),
        max_step=4, min_step=1, length=6, count=20, max_leaps=2,
        require_recovery=True, require_tendency_present=True, min_distinct=5,
        notes="Combine everything: length 6, steps + learned leaps (ceiling a "
              "5th), a tendency tone present, stepwise recovery after leaps, "
              "resolving to a stable tone. The exit skill → transcribe real music.",
    ),
]


# --- Minor dictation ladder (ND-series) ---------------------------------------
# Mirror of DICTATION_STAGES into la-based minor, exactly as MINOR_STAGES mirrors
# MAJOR_STAGES: the structural rungs recast into natural minor (tonic triad
# la-do-mi = indices 0,2,4, same as major, so triad/step/leap specs stay
# function-correct); only the half-steps move (ti→do at index 1, fa→mi at index
# 5). The major tendency stage (DD8) is replaced by a natural-minor leading-tone
# stage (ND8), and a harmonic-minor capstone (ND9h, raised 7 si→la) is defined but
# kept OUT of the built deck — its si is a G♯ (a non-key-signature accidental) and
# the transcription editor has no accidental input yet. All dictation invariants
# carry over (one new variable per rung, no repeats, ceiling ≤5th, forced tendency).
_MINOR_DICT_TITLES = {
    "DP1": "Two-Note Pillars (la–do–mi)",
    "DP2": "Two-Note Step (minor)",
    "DD1": "The Minor Triad Skeleton (la–do–mi)",
    "DD2": "Stepwise Neighbors (minor)",
    "DD3": "The Minor Pentachord",
    "DD4": "Into the Upper Scale (minor)",
    "DD5": "Long Stepwise Phrases (minor)",
    "DD6": "Skips of a Third (minor)",
    "DD7": "Fourths & Fifths (minor)",
    "DD9": "Free Diatonic (minor capstone)",
}


def _to_minor_dictation(stage: Stage) -> Stage:
    """Recast a structural dictation stage into natural minor (cf. _to_minor)."""
    new_id = "N" + stage.id if stage.id.startswith("DP") else "N" + stage.id[1:]
    return replace(
        stage,
        id=new_id,
        title=_MINOR_DICT_TITLES.get(stage.id, stage.title),
        phase="minor-dictation",
        mode="natural_minor",
        require_tendency_present=False,
        require_tendency_resolution=False,
        tendency_up_from=(1,),
        tendency_down_from=(5,),
    )


# Priming singletons for minor: indices 0,2,4 = the la/do/mi pillars (NDP0).
DICTATION_MINOR_PRIMING_SINGLETONS: tuple[tuple[int, ...], ...] = (
    (D1,), (D3,), (D5,),
)

_MINOR_DICT_STRUCTURAL = [
    _to_minor_dictation(s)
    for s in DICTATION_STAGES
    if s.id not in ("DD8", "DD9")
]

# ND8 · natural-minor leading tone — ti→do (index 1→2) resolves in EVERY item.
# Mirror of DD8: require the leading tone present (require_present_any=(D2,) = ti,
# index 1) and hold it to resolution; leave fa free (tendency_down_from=()) so
# ascending lines through fa aren't rejected. end_pool excludes ti so it always
# has a successor to resolve into.
_ND8 = Stage(
    "ND8", "Tendency Tones — Ti Wants Do (natural minor)", "minor-dictation",
    pool=_DFULL_L, start_pool=(D1, D2, D3, D4, D5), end_pool=(D1, D3, D5, D8),
    max_step=2, min_step=1, length=5, count=16, min_distinct=3,
    max_leaps=2, require_recovery=False,
    mode="natural_minor",
    require_tendency_present=True, require_tendency_resolution=True,
    require_present_any=(D2,),
    tendency_up_from=(1,), tendency_down_from=(),
    notes="Foreground the natural-minor leading tone: ti→do (index 1) resolves in "
          "every item. fa→mi is trained across the stepwise stages and appears "
          "here too. Length 4→5; no new leap class (≤3rd, already learned).",
)

# ND9 · free diatonic capstone (natural minor). Mirror of DD9 but with minor's
# half-step positions; keep DD9's require_tendency_present (a blind recast clears
# it), so build it explicitly.
_ND9 = replace(
    next(s for s in DICTATION_STAGES if s.id == "DD9"),
    id="ND9",
    title=_MINOR_DICT_TITLES["DD9"],
    phase="minor-dictation",
    mode="natural_minor",
    tendency_up_from=(1,), tendency_down_from=(5,),
)

# ND9h · harmonic-minor capstone — raised 7 (si) resolves up a half-step to la in
# EVERY item. Both leading tones available (lower si index -1 → tonic la index 0;
# upper si index 6 → la′ index 7); fa (index 5) left out to avoid the augmented
# 2nd fa→si. DEFERRED from the built deck: si = G♯ needs accidental input.
_ND9h = Stage(
    "ND9h", "The Raised 7th — Harmonic Minor (si→la)", "minor-dictation",
    pool=(DL7, D1, D2, D3, D4, D5, D7, D8), start_pool=(D1, D3, D5),
    end_pool=(D1, D8), max_step=2, min_step=1, length=5, count=16, min_distinct=3,
    max_leaps=2, require_recovery=False,
    mode="harmonic_minor",
    require_tendency_present=True, require_tendency_resolution=True,
    require_present_any=(D7, DL7),
    tendency_up_from=(6,), tendency_down_from=(),
    notes="Harmonic minor's raised 7 (si) resolves up to la in every item. "
          "Deferred from the built deck until the editor accepts accidentals "
          "(si = G♯ in A minor).",
)

# Natural-minor ladder (built). The harmonic capstone is kept separate.
DICTATION_MINOR_STAGES: list[Stage] = [*_MINOR_DICT_STRUCTURAL, _ND8, _ND9]
DICTATION_MINOR_HARMONIC_STAGES: list[Stage] = [_ND9h]


# --- Interval dictation (IVD-series) ------------------------------------------
# The interval-singing specs re-tagged for the Dictate card: length-2, one pinned
# diatonic interval each, both directions. A separate sub-track (not part of the
# melodic-spine invariants), so 6ths/7ths/octaves (max_step > 4) are legitimate.
DICTATION_INTERVAL_STAGES: list[Stage] = [
    replace(
        s,
        id="IVD" + s.id[2:],
        phase="dictation-interval",
        notes=s.notes + " (dictation: hear the interval, notate it).",
    )
    for s in INTERVAL_STAGES
]


STAGES_BY_ID = {
    s.id: s
    for s in (
        *MAJOR_STAGES, *MINOR_STAGES, *INTERVAL_STAGES, *DICTATION_STAGES,
        *DICTATION_MINOR_STAGES, *DICTATION_MINOR_HARMONIC_STAGES,
        *DICTATION_INTERVAL_STAGES,
    )
}
