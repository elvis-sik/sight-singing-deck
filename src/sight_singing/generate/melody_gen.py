"""Melody generation: enumerate valid degree sequences for a stage, score them
for musicality, and sample a diverse, deduplicated study set.

Everything is in diatonic indices (see theory.scales). A "melody" here is just a
tuple of diatonic indices; realization into pitches/keys/clefs happens later.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable

from sight_singing.curriculum.stages import Stage
from sight_singing.theory.scales import diatonic_semitone


def _steps(mel: tuple[int, ...]) -> list[int]:
    return [b - a for a, b in zip(mel, mel[1:])]


def _direction_changes(mel: tuple[int, ...]) -> int:
    dirs = [1 if s > 0 else -1 if s < 0 else 0 for s in _steps(mel)]
    dirs = [d for d in dirs if d != 0]
    return sum(1 for a, b in zip(dirs, dirs[1:]) if a != b)


def _max_run(mel: tuple[int, ...]) -> int:
    best = run = 1
    for a, b in zip(mel, mel[1:]):
        run = run + 1 if a == b else 1
        best = max(best, run)
    return best


def passes_hard_rules(mel: tuple[int, ...], stage: Stage) -> bool:
    """Reject melodies that violate a stage's hard constraints."""
    steps = _steps(mel)
    abs_steps = [abs(s) for s in steps]

    if mel[0] not in stage.start_pool or mel[-1] not in stage.end_pool:
        return False
    if any(a > stage.max_step for a in abs_steps):
        return False
    if stage.min_step and any(a < stage.min_step for a in abs_steps):
        return False
    if len(set(mel)) == 1:  # monotone
        return False
    if stage.min_distinct and len(set(mel)) < stage.min_distinct:
        return False
    if not stage.allow_three_repeats and _max_run(mel) >= 3:
        return False
    if _direction_changes(mel) > stage.max_direction_changes:
        return False

    leaps = [s for s in abs_steps if s >= 2]
    if stage.require_leap and not leaps:
        return False
    if stage.max_leaps is not None and len(leaps) > stage.max_leaps:
        return False
    # Headline leap: a named-interval stage (e.g. "Perfect Fourths") must contain
    # at least one adjacent leap of its size, not merely any >=3rd.
    if stage.require_leap_min and not any(
        a >= stage.require_leap_min for a in abs_steps
    ):
        return False

    # No bare melodic tritone (6 semitones). Diatonic-step size can't see this —
    # a diatonic 4th is a P4 almost everywhere but an augmented 4th between fa and
    # ti — so we check the realized semitone interval for the stage's mode.
    if stage.forbid_tritone_leap:
        mode = stage.mode or "major"
        for a, b in zip(mel, mel[1:]):
            if abs(diatonic_semitone(b, mode) - diatonic_semitone(a, mode)) == 6:
                return False

    # Recovery after a big leap (>= a third): the next motion should step back
    # in the opposite direction (contrary stepwise recovery).
    if stage.require_recovery:
        for i, s in enumerate(steps):
            if abs(s) >= 3:  # a fourth or wider
                if i + 1 >= len(steps):
                    # a wide leap as the final motion is left hanging
                    return False
                nxt = steps[i + 1]
                if not (0 < abs(nxt) <= 2 and (nxt > 0) != (s > 0)):
                    return False

    # Tendency tones resolve by step. Which scale positions pull, and in which
    # direction, is mode-dependent (see Stage.tendency_up_from/down_from). Major
    # default: ti (index 6) -> up to do; fa (index 3) -> down to mi. Indices
    # repeat every 7, so compare on the position mod 7.
    up = stage.tendency_up_from
    down = stage.tendency_down_from
    if stage.require_tendency_resolution:
        for a, b in zip(mel, mel[1:]):
            pos = a % 7
            if pos in up and (b - a) != 1:
                return False
            if pos in down and (b - a) != -1:
                return False
    if stage.require_tendency_present:
        tendency_positions = set(up) | set(down)
        if not any((n % 7) in tendency_positions for n in mel):
            return False
    if stage.require_present_any:
        if not any(n in stage.require_present_any for n in mel):
            return False

    return True


def enumerate_stage(stage: Stage) -> list[tuple[int, ...]]:
    """All degree sequences satisfying the stage's hard rules."""
    out = []
    for mel in itertools.product(stage.pool, repeat=stage.length):
        if mel[0] not in stage.start_pool or mel[-1] not in stage.end_pool:
            continue
        if any(abs(b - a) > stage.max_step for a, b in zip(mel, mel[1:])):
            continue
        if passes_hard_rules(mel, stage):
            out.append(mel)
    return out


def quality_score(mel: tuple[int, ...], stage: Stage) -> float:
    """Higher = more musical. Used for ranking and diverse sampling."""
    steps = _steps(mel)
    abs_steps = [abs(s) for s in steps]
    score = 0.0

    # Prefer clear contour: reward one or two direction changes over zero or many.
    dc = _direction_changes(mel)
    score += {0: 0.3, 1: 1.0, 2: 0.8, 3: 0.4}.get(dc, 0.1)

    # Reward some motion but not constant leaping.
    n_leaps = sum(1 for a in abs_steps if a >= 2)
    n_steps = sum(1 for a in abs_steps if a == 1)
    score += 0.15 * n_steps
    score += 0.25 * n_leaps if n_leaps <= (stage.max_leaps or 2) else -0.5

    # Ending on the tonic (index 0 or 7) feels resolved; mild reward.
    if mel[-1] % 7 == 0:
        score += 0.4
    elif mel[-1] % 7 in (2, 4):  # mi / sol
        score += 0.2

    # Penalise immediate note repetition (some is fine, a lot is dull).
    score -= 0.2 * sum(1 for s in steps if s == 0)

    # Reward using distinct pitches (variety within a short melody).
    score += 0.15 * len(set(mel))

    # Reward using the stage's range (differentiates otherwise-overlapping step
    # stages: a later stage that allows 6/7 should lead with melodies that reach
    # them, not with the same low-pentachord melodies as the earlier stage).
    ambitus = max(mel) - min(mel)
    score += 0.18 * ambitus

    # Leap stages should foreground their headline leap.
    if stage.max_step >= 2:
        headline = 3 if stage.max_step >= 3 else 2  # fourth+ stages want a >=4th
        if any(a >= headline for a in abs_steps):
            score += 0.6
        else:
            score -= 0.4

    # Gentle penalty for zig-zag (up-down-up-down neighbour noise).
    if len(steps) >= 3 and all(abs(s) == 1 for s in steps):
        dirs = [1 if s > 0 else -1 for s in steps]
        if all(a != b for a, b in zip(dirs, dirs[1:])):
            score -= 0.5
    return score


def contour_signature(mel: tuple[int, ...]) -> tuple:
    """A coarse shape key for diversity sampling: direction pattern + endpoints."""
    dirs = tuple(1 if b > a else -1 if b < a else 0 for a, b in zip(mel, mel[1:]))
    return (dirs, mel[0] % 7, mel[-1] % 7)


def sample_diverse(
    ranked: Iterable[tuple[int, ...]], stage: Stage, target: int
) -> list[tuple[int, ...]]:
    """Greedily pick a diverse, high-quality subset up to `target`.

    First pass: at most one melody per contour signature (spreads shapes).
    Second pass: fill remaining slots from the leftovers, best-first.
    """
    ranked = list(ranked)
    picked: list[tuple[int, ...]] = []
    seen_sig: set = set()
    leftovers: list[tuple[int, ...]] = []
    for mel in ranked:
        sig = contour_signature(mel)
        if sig not in seen_sig:
            seen_sig.add(sig)
            picked.append(mel)
            if len(picked) >= target:
                return picked
        else:
            leftovers.append(mel)
    for mel in leftovers:
        if len(picked) >= target:
            break
        picked.append(mel)
    return picked


def generate_stage(stage: Stage) -> list[tuple[int, ...]]:
    """The full pipeline for one stage: enumerate → rank → diverse sample."""
    candidates = enumerate_stage(stage)
    candidates.sort(key=lambda m: quality_score(m, stage), reverse=True)
    return sample_diverse(candidates, stage, stage.count)
