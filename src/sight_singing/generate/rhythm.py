"""Rhythm-first generator: one-bar 4/4 rhythms on a single repeated pitch.

Each generated bar yields two views:

- ``audio``: [(duration, is_rest), ...] — what the clip plays (ties merged into
  one sustained note; triplet eighths as "8t" = 1/3 beat).
- ``render``: [{kind, duration, tie?, tuplet?}, ...] — the notation (tied notes
  drawn as tied pairs; triplet members flagged so the renderer draws the "3").

R1-R6 build from beat-cells (pulse/duration, rests, eighth pairs, mixed, offbeat,
dotted). R7 is syncopation (offbeat quarters written as tied eighths across the
beat), R8 is beat-level triplets, R9 mixes everything.

RC1-RC3 are compound meter (6/8): the beat is a dotted quarter (three eighths)
and a bar is two beats. Every compound figure stays inside a beat (no ties/tuplets
needed), so notation == audio there too.
"""

from __future__ import annotations

# --- beat cells (R1-R6) -------------------------------------------------------
Q = (1, (("q", False),))                    # quarter note
QR = (1, (("q", True),))                     # quarter rest
H = (2, (("h", False),))                     # half note
W = (4, (("w", False),))                     # whole note
E2 = (1, (("8", False), ("8", False)))       # two eighths (beamed)
E_R = (1, (("8", False), ("8", True)))       # eighth + eighth rest (offbeat)
R_E = (1, (("8", True), ("8", False)))       # eighth rest + eighth (weak entry)
DQE = (2, (("qd", False), ("8", False)))     # dotted quarter + eighth

# --- compound beat cells (RC1-RC3, 6/8) ---------------------------------------
# In 6/8 the beat is a dotted quarter = three eighths; a bar is two beats. Each
# cell fills ONE beat with real note values, and every figure stays inside its
# beat so the notation view equals the audio view (no ties/tuplets).
CQD = (1, (("qd", False),))                              # dotted quarter (held beat)
C3E = (1, (("8", False), ("8", False), ("8", False)))    # three eighths
CQE = (1, (("q", False), ("8", False)))                  # quarter + eighth (long–short)
CEQ = (1, (("8", False), ("q", False)))                  # eighth + quarter (short–long)
CQDR = (1, (("qd", True),))                              # dotted-quarter rest (silent beat)
CRE2 = (1, (("8", True), ("8", False), ("8", False)))    # eighth rest + two eighths
CERE = (1, (("8", False), ("8", True), ("8", False)))    # eighth, eighth rest, eighth


class RhythmStage:
    def __init__(
        self, sid, title, count, kind,
        cells=(), require_any=(), time_sig="4/4", beats=4,
    ):
        self.id = sid
        self.title = title
        self.count = count
        self.kind = kind  # "cells" | "syncopation" | "triplet" | "mixed" | "compound"
        self.cells = cells
        self.require_any = require_any
        self.time_sig = time_sig
        self.beats = beats  # beat-cells per bar (compound 6/8 = 2 dotted-quarter beats)


RHYTHM_STAGES = [
    RhythmStage("R1", "Pulse and Duration", 24, "cells", (Q, H, W)),
    RhythmStage("R2", "Silence and Entry", 30, "cells", (Q, QR, H)),
    RhythmStage("R3", "First Eighth Pairs", 36, "cells", (Q, E2), (E2,)),
    RhythmStage("R4", "Mixed Beat Fillings", 42, "cells", (Q, H, E2)),
    RhythmStage("R5", "Offbeat Feel", 48, "cells", (Q, E2, E_R, R_E), (E_R, R_E)),
    RhythmStage("R6", "Dotted Patterns", 48, "cells", (Q, E2, DQE), (DQE,)),
    RhythmStage("R7", "Ties Across Beats", 40, "syncopation"),
    RhythmStage("R8", "Triplet Pulse", 40, "triplet"),
    RhythmStage("R9", "Full Beginner Rhythm", 48, "mixed"),
    RhythmStage("RC1", "Compound Pulse (6/8)", 9, "compound",
                (CQD, C3E, CQE), time_sig="6/8", beats=2),
    RhythmStage("RC2", "Compound Divisions (6/8)", 12, "compound",
                (CQD, C3E, CQE, CEQ), require_any=(CQE, CEQ),
                time_sig="6/8", beats=2),
    RhythmStage("RC3", "Compound with Rests (6/8)", 12, "compound",
                (CQD, C3E, CQDR, CRE2, CERE), require_any=(CQDR, CRE2, CERE),
                time_sig="6/8", beats=2),
]

RHYTHM_STAGES_BY_ID = {s.id: s for s in RHYTHM_STAGES}


# --- R1-R6: cell enumeration --------------------------------------------------
def _enumerate_bars(cells, beats=4):
    out = []

    def rec(remaining, acc):
        if remaining == 0:
            out.append(tuple(acc))
            return
        for c in cells:
            if c[0] <= remaining:
                rec(remaining - c[0], (*acc, c))

    rec(beats, ())
    return out


def _cell_events(bar):
    evs = []
    for _beats, cell_events in bar:
        evs.extend(cell_events)
    return evs


def _attacks(events):
    return sum(1 for _d, is_rest in events if not is_rest)


def _passes_cells(bar, stage):
    evs = _cell_events(bar)
    if not any(not is_rest for _d, is_rest in evs):
        return False
    if stage.require_any and not any(c in stage.require_any for c in bar):
        return False
    eighth_cells = sum(1 for c in bar if c in (E2, E_R, R_E))
    if eighth_cells == len(bar) and len(bar) >= 3:
        return False
    return True


def _score_cells(bar):
    score = 0.0
    n = _attacks(_cell_events(bar))
    score += {0: -5, 1: -1, 2: 0.6, 3: 1.0, 4: 1.0, 5: 0.8, 6: 0.5}.get(n, 0.2)
    if not _cell_events(bar)[0][1]:
        score += 0.5
    score += 0.2 * len(set(bar))
    return score


def _render_plain(audio_events):
    """R1-R6: notation == audio (no ties/tuplets)."""
    out = []
    for dur, is_rest in audio_events:
        out.append({"kind": "rest" if is_rest else "note", "duration": dur})
    return out


def _generate_cells(stage):
    bars = [b for b in _enumerate_bars(stage.cells) if _passes_cells(b, stage)]
    bars.sort(key=_score_cells, reverse=True)
    picked, seen, leftovers = [], set(), []
    for bar in bars:
        evs = _cell_events(bar)
        sig = (tuple(c[0] for c in bar), _attacks(evs))
        if sig not in seen:
            seen.add(sig)
            picked.append(evs)
            if len(picked) >= stage.count:
                break
        else:
            leftovers.append(evs)
    for evs in leftovers:
        if len(picked) >= stage.count:
            break
        picked.append(evs)
    return [{"audio": evs, "render": _render_plain(evs)} for evs in picked]


# --- R7: syncopation (ties across beats) --------------------------------------
# Work in eighth SLOTS (8 per bar). An onset pattern places note-starts; each run
# between onsets is a note. We restrict runs to 1 slot (eighth) or 2 slots
# (quarter); a length-2 run starting on an offbeat (odd slot) crosses the beat
# and is drawn as two tied eighths — the syncopation the stage teaches.
_SLOT_DUR = {1: "8", 2: "q"}


def _onset_bars(n_slots=8):
    """All onset patterns starting on slot 0 with every run length in {1, 2}."""
    out = []

    def rec(slot, runs):
        if slot == n_slots:
            out.append(tuple(runs))
            return
        for run in (1, 2):
            if slot + run <= n_slots:
                rec(slot + run, (*runs, run))

    rec(0, ())
    return out


def _sync_views(runs):
    """(audio, render) for an onset-run bar; ties where a quarter is offbeat."""
    audio, render = [], []
    slot = 0
    for run in runs:
        audio.append((_SLOT_DUR[run], False))
        if run == 2 and slot % 2 == 1:  # offbeat quarter -> two tied eighths
            render.append({"kind": "note", "duration": "8", "tie": True})
            render.append({"kind": "note", "duration": "8"})
        else:
            render.append({"kind": "note", "duration": _SLOT_DUR[run]})
        slot += run
    return audio, render


def _is_syncopated(runs):
    slot = 0
    for run in runs:
        if run == 2 and slot % 2 == 1:
            return True
        slot += run
    return False


def _generate_syncopation(stage):
    bars = [r for r in _onset_bars() if _is_syncopated(r)]
    # Prefer clear bars: a few onsets, not a wall of eighths.
    bars.sort(key=lambda r: abs(len(r) - 5))
    picked, seen = [], set()
    for runs in bars:
        if runs in seen:
            continue
        seen.add(runs)
        audio, render = _sync_views(runs)
        picked.append({"audio": audio, "render": render})
        if len(picked) >= stage.count:
            break
    return picked


# --- R8: beat-level triplets --------------------------------------------------
# Beat cells: a quarter, two eighths, or a triplet (three eighths, 3-in-2).
_TB_Q = "q"
_TB_E2 = "e2"
_TB_T3 = "t3"
_TRIPLET_BEATS = (_TB_Q, _TB_E2, _TB_T3)


def _triplet_views(beats):
    audio, render = [], []
    for beat in beats:
        if beat == _TB_Q:
            audio.append(("q", False))
            render.append({"kind": "note", "duration": "q"})
        elif beat == _TB_E2:
            audio.extend([("8", False), ("8", False)])
            render.extend([{"kind": "note", "duration": "8"}] * 2)
        else:  # triplet
            audio.extend([("8t", False)] * 3)
            render.extend(
                [{"kind": "note", "duration": "8", "tuplet": True}] * 3
            )
    return audio, render


def _generate_triplet(stage):
    bars = []

    def rec(remaining, acc):
        if remaining == 0:
            bars.append(tuple(acc))
            return
        for b in _TRIPLET_BEATS:
            rec(remaining - 1, (*acc, b))

    rec(4, ())
    # Require >=1 triplet; avoid an all-triplet wall.
    bars = [b for b in bars if _TB_T3 in b and b.count(_TB_T3) < 4]
    # Fewer triplets first (clearer), then more.
    bars.sort(key=lambda b: (b.count(_TB_T3), b.count(_TB_E2)))
    picked = []
    for beats in bars:
        audio, render = _triplet_views(beats)
        picked.append({"audio": audio, "render": render})
        if len(picked) >= stage.count:
            break
    return picked


# --- RC1-RC3: compound meter (6/8) --------------------------------------------
# Two dotted-quarter beats per bar, each filled by one compound beat-cell. Every
# cell stays inside its beat, so audio == notation (plain, no ties/tuplets).
def _passes_compound(bar, stage):
    evs = _cell_events(bar)
    if not any(not is_rest for _d, is_rest in evs):  # need at least one attack
        return False
    if stage.require_any and not any(c in stage.require_any for c in bar):
        return False
    return True


def _score_compound(bar):
    score = 0.0
    n = _attacks(_cell_events(bar))
    score += {0: -5, 1: -1, 2: 0.5, 3: 0.8, 4: 1.0, 5: 0.9, 6: 0.6}.get(n, 0.3)
    if not _cell_events(bar)[0][1]:  # bar starts with sound, not a rest
        score += 0.4
    score += 0.3 * len(set(bar))  # reward cell variety
    return score


def _generate_compound(stage):
    bars = [
        b
        for b in _enumerate_bars(stage.cells, beats=stage.beats)
        if _passes_compound(b, stage)
    ]
    bars.sort(key=_score_compound, reverse=True)
    picked, seen = [], set()
    for bar in bars:
        evs = _cell_events(bar)
        sig = tuple(evs)
        if sig in seen:
            continue
        seen.add(sig)
        picked.append(evs)
        if len(picked) >= stage.count:
            break
    return [{"audio": evs, "render": _render_plain(evs)} for evs in picked]


# --- R9: mixed review ---------------------------------------------------------
def _generate_mixed(stage):
    """A diverse mix pulling from the mixed, dotted, syncopation, triplet stages."""
    sources = ["R4", "R6", "R7", "R8"]
    per = max(1, stage.count // len(sources))
    picked = []
    for sid in sources:
        picked.extend(generate_rhythm_stage(RHYTHM_STAGES_BY_ID[sid])[:per])
    return picked[: stage.count]


def generate_rhythm_stage(stage):
    """Return a stage's bars as [{"audio": [...], "render": [...]}, ...]."""
    if stage.kind == "cells":
        return _generate_cells(stage)
    if stage.kind == "syncopation":
        return _generate_syncopation(stage)
    if stage.kind == "triplet":
        return _generate_triplet(stage)
    if stage.kind == "compound":
        return _generate_compound(stage)
    if stage.kind == "mixed":
        return _generate_mixed(stage)
    raise ValueError(f"unknown rhythm stage kind: {stage.kind}")
