"""Rhythm-first generator: one-bar 4/4 rhythms on a single repeated pitch.

Bars are built from beat-cells (each filling a whole number of beats) drawn from
a stage's allowed set, enumerated to fill exactly 4 beats, filtered for
musicality, and diversely sampled. Covers R1-R6 of RHYTHM_CURRICULUM.md
(pulse/duration, rests, eighth pairs, mixed, offbeat, dotted). Ties and triplets
(R7-R9) need StaveTie/Tuplet renderer support and are a later step.

A cell is (beats, [(duration, is_rest), ...]); durations use the renderer's
vocabulary ("q", "h", "w", "8", dotted "qd").
"""

from __future__ import annotations

# --- beat cells ---------------------------------------------------------------
Q = (1, (("q", False),))                    # quarter note
QR = (1, (("q", True),))                     # quarter rest
H = (2, (("h", False),))                     # half note
W = (4, (("w", False),))                     # whole note
E2 = (1, (("8", False), ("8", False)))       # two eighths (beamed)
E_R = (1, (("8", False), ("8", True)))       # eighth + eighth rest (offbeat)
R_E = (1, (("8", True), ("8", False)))       # eighth rest + eighth (weak entry)
DQE = (2, (("qd", False), ("8", False)))     # dotted quarter + eighth


class RhythmStage:
    def __init__(self, sid, title, count, cells, require_any=(), length_beats=4):
        self.id = sid
        self.title = title
        self.count = count
        self.cells = cells
        self.require_any = require_any  # cells whose presence the stage requires
        self.length_beats = length_beats


RHYTHM_STAGES = [
    RhythmStage("R1", "Pulse and Duration", 24, (Q, H, W)),
    RhythmStage("R2", "Silence and Entry", 30, (Q, QR, H)),
    RhythmStage("R3", "First Eighth Pairs", 36, (Q, E2), require_any=(E2,)),
    RhythmStage("R4", "Mixed Beat Fillings", 42, (Q, H, E2)),
    RhythmStage("R5", "Offbeat Feel", 48, (Q, E2, E_R, R_E), require_any=(E_R, R_E)),
    RhythmStage("R6", "Dotted Patterns", 48, (Q, E2, DQE), require_any=(DQE,)),
]

RHYTHM_STAGES_BY_ID = {s.id: s for s in RHYTHM_STAGES}


def _enumerate_bars(cells, beats):
    """All ordered cell sequences summing to exactly `beats`."""
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


def _events(bar):
    """Flatten a bar (tuple of cells) into (duration, is_rest) events."""
    evs = []
    for _beats, cell_events in bar:
        evs.extend(cell_events)
    return evs


def _attacks(bar):
    return sum(1 for dur, is_rest in _events(bar) if not is_rest)


def _passes(bar, stage):
    evs = _events(bar)
    if all(is_rest for _d, is_rest in evs):
        return False  # a bar of pure silence
    if not any(not is_rest for _d, is_rest in evs):
        return False
    if stage.require_any and not any(c in stage.require_any for c in bar):
        return False
    # Avoid a monotonous wall of eighths unless it is genuinely the only option.
    eighth_cells = sum(1 for c in bar if c in (E2, E_R, R_E))
    if eighth_cells == len(bar) and len(bar) >= 3:
        return False
    return True


def _score(bar):
    """Higher = nicer. Reward strong-beat clarity + a mix of attack densities."""
    score = 0.0
    n_attacks = _attacks(bar)
    # A plausible bar has a few attacks, not one and not a dozen.
    score += {0: -5, 1: -1, 2: 0.6, 3: 1.0, 4: 1.0, 5: 0.8, 6: 0.5}.get(n_attacks, 0.2)
    # Reward starting on a real attack (strong downbeat).
    first = _events(bar)[0]
    if not first[1]:
        score += 0.5
    # Reward some variety of cell types.
    score += 0.2 * len(set(bar))
    return score


def _signature(bar):
    """Coarse shape key for diverse sampling: the beat pattern + attack count."""
    return (tuple(c[0] for c in bar), _attacks(bar))


def generate_rhythm_stage(stage):
    """Enumerate → filter → rank → diversely sample a stage's rhythm bars.

    Returns a list of duration/rest event lists: [[(duration, is_rest), ...], ...].
    """
    bars = [b for b in _enumerate_bars(stage.cells, stage.length_beats) if _passes(b, stage)]
    bars.sort(key=_score, reverse=True)
    picked = []
    seen_sig = set()
    leftovers = []
    for bar in bars:
        sig = _signature(bar)
        if sig not in seen_sig:
            seen_sig.add(sig)
            picked.append(bar)
            if len(picked) >= stage.count:
                break
        else:
            leftovers.append(bar)
    for bar in leftovers:
        if len(picked) >= stage.count:
            break
        picked.append(bar)
    return [_events(b) for b in picked]
