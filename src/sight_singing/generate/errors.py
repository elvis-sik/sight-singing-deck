"""Error-detection cases: take a base melody and alter exactly one note.

The learner sees the *written* melody (notation) and hears the *played* melody,
which differs at one note, and must find the wrong note. Alteration stays in key
(a diatonic index shift), so the task is "know the tune", not just "spot the
out-of-key note".

Everything is deterministic (no RNG — which the workflow/runtime forbids anyway):
the altered index and shift are chosen by a stable scan so regenerating the deck
keeps the same cases.
"""

from __future__ import annotations

# Try these diatonic-index shifts, in order, for the altered note.
_SHIFTS = (1, -1, 2, -2)
# Keep altered notes within a sane singable band around the tonic octave.
_MIN_INDEX, _MAX_INDEX = -2, 9


def _distinct_from_neighbours(mel: tuple[int, ...], i: int, value: int) -> bool:
    """The altered pitch should differ from its neighbours (a real wrong note,
    not a disguised repeat)."""
    if i > 0 and mel[i - 1] == value:
        return False
    if i + 1 < len(mel) and mel[i + 1] == value:
        return False
    return True


def make_error_variants(
    base: tuple[int, ...], max_variants: int = 6
) -> list[dict[str, object]]:
    """All (position-diverse) single-note error variants for a base melody.

    The card picks one of these at *study time* (per view), so the wrong note is
    not memorisable to a fixed spot. We cover distinct interior positions first
    (one best shift each — maximum positional spread), then add alternate shifts
    on already-used positions until ``max_variants`` is reached. Fully
    deterministic (stable clip filenames across rebuilds).
    """
    n = len(base)
    if n < 3:
        return []
    order = sorted(range(1, n), key=lambda i: (abs(i - (n - 1) / 2), i))

    def variant(i: int, value: int) -> dict[str, object]:
        return {
            "played": base[:i] + (value,) + base[i + 1 :],
            "error_index": i,
            "written_index": base[i],
            "played_index": value,
        }

    first_pass: list[dict[str, object]] = []  # one per position
    extras: list[dict[str, object]] = []      # further shifts per position
    for i in order:
        original = base[i]
        used_here = 0
        for shift in _SHIFTS:
            value = original + shift
            if not (_MIN_INDEX <= value <= _MAX_INDEX):
                continue
            if value == original:
                continue
            if not _distinct_from_neighbours(base, i, value):
                continue
            (first_pass if used_here == 0 else extras).append(variant(i, value))
            used_here += 1
    return (first_pass + extras)[:max_variants]
