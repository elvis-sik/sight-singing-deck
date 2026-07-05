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


def make_error_case(base: tuple[int, ...]) -> dict[str, object] | None:
    """Return an error case for a base melody (diatonic indices), or None.

    The result carries the written and played index sequences, the 0-based
    error index, and the written/played diatonic indices at that spot.
    """
    n = len(base)
    if n < 3:
        return None
    # Prefer altering an interior note (keeps the opening tonal anchor intact);
    # fall back to the last note. Deterministic order: middle-out.
    order = sorted(range(1, n), key=lambda i: (abs(i - (n - 1) / 2), i))
    for i in order:
        original = base[i]
        for shift in _SHIFTS:
            value = original + shift
            if not (_MIN_INDEX <= value <= _MAX_INDEX):
                continue
            if value == original:
                continue
            if not _distinct_from_neighbours(base, i, value):
                continue
            played = base[:i] + (value,) + base[i + 1 :]
            return {
                "written": base,
                "played": played,
                "error_index": i,
                "written_index": original,
                "played_index": value,
            }
    return None
