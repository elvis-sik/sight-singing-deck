"""Diatonic music theory: keys, scales, degree→pitch realization, MIDI.

The whole generator works in **diatonic indices**: an integer `d` where `d == 0`
is the tonic, `+1` is the next scale degree up, `-1` the degree below the tonic,
`+7` the tonic an octave up, and so on. This makes neighbors below the tonic and
octave motion fall out naturally, and keeps the melody logic independent of key,
mode, and clef until the very end (realization).
"""

from __future__ import annotations

from dataclasses import dataclass

LETTERS = "CDEFGAB"
LETTER_SEMITONE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# Interval patterns (semitones from tonic) for one octave of each mode.
MODE_STEPS = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "natural_minor": [0, 2, 3, 5, 7, 8, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
}

# Movable-do solfège. Major is do-based; minor is la-based (tonic = la), which is
# the standard ear-training convention and makes relative major/minor share
# syllables. Harmonic minor's raised 7 is "si".
_SOLFEGE_MAJOR = ["do", "re", "mi", "fa", "so", "la", "ti"]
_SOLFEGE_MINOR_LA = ["la", "ti", "do", "re", "mi", "fa", "so"]
_SOLFEGE_MINOR_HARMONIC = ["la", "ti", "do", "re", "mi", "fa", "si"]

# Accidental spelling as text.
_ACC_TEXT = {-2: "bb", -1: "b", 0: "", 1: "#", 2: "x"}


def _acc_for_letter(letter: str, target_pc: int) -> int:
    """Accidental (semitone offset) so `letter` sounds at pitch-class target_pc."""
    diff = (target_pc - LETTER_SEMITONE[letter]) % 12
    if diff > 6:
        diff -= 12
    return diff


@dataclass(frozen=True)
class Key:
    """A key = a tonic pitch class (as a letter+accidental) plus a mode."""

    tonic_letter: str  # "C".."B"
    tonic_accidental: int  # -1 flat, 0 natural, 1 sharp
    mode: str  # "major" | "natural_minor" | "harmonic_minor"

    @property
    def tonic_pc(self) -> int:
        return (LETTER_SEMITONE[self.tonic_letter] + self.tonic_accidental) % 12

    def scale_spelling(self) -> list[tuple[str, int]]:
        """The 7 scale notes as (letter, accidental), each letter used once."""
        steps = MODE_STEPS[self.mode]
        start = LETTERS.index(self.tonic_letter)
        out: list[tuple[str, int]] = []
        for i in range(7):
            letter = LETTERS[(start + i) % 7]
            target_pc = (self.tonic_pc + steps[i]) % 12
            out.append((letter, _acc_for_letter(letter, target_pc)))
        return out

    def accidental_by_letter(self) -> dict[str, int]:
        return {letter: acc for letter, acc in self.scale_spelling()}

    def solfege_syllables(self) -> list[str]:
        if self.mode == "major":
            return _SOLFEGE_MAJOR
        if self.mode == "harmonic_minor":
            return _SOLFEGE_MINOR_HARMONIC
        return _SOLFEGE_MINOR_LA


def key(tonic: str, mode: str = "major") -> Key:
    """Build a Key from a name like 'C', 'F#', 'Bb' and a mode."""
    letter = tonic[0].upper()
    acc = 0
    for ch in tonic[1:]:
        if ch in ("#", "s"):
            acc += 1
        elif ch in ("b", "f"):
            acc -= 1
    return Key(letter, acc, mode)


def _abs_position(letter: str, octave: int) -> int:
    """Absolute diatonic ladder position (octave*7 + letter index, 0=C)."""
    return octave * 7 + LETTERS.index(letter)


def note_name(letter: str, accidental: int, octave: int) -> str:
    return f"{letter}{_ACC_TEXT[accidental]}{octave}"


def note_midi(letter: str, accidental: int, octave: int) -> int:
    # MIDI: C4 == 60, so octave n starts at (n+1)*12.
    return (octave + 1) * 12 + LETTER_SEMITONE[letter] + accidental


def parse_note_name(name: str) -> tuple[str, int, int]:
    """'F#4' -> ('F', 1, 4); 'Bb3' -> ('B', -1, 3); 'C4' -> ('C', 0, 4)."""
    letter = name[0].upper()
    i = 1
    acc = 0
    while i < len(name) and name[i] in "#bsxf":
        if name[i] in ("#", "s"):
            acc += 1
        elif name[i] in ("b", "f"):
            acc -= 1
        elif name[i] == "x":
            acc += 2
        i += 1
    octave = int(name[i:])
    return letter, acc, octave


def midi_from_name(name: str) -> int:
    letter, acc, octave = parse_note_name(name)
    return note_midi(letter, acc, octave)


def key_signature(k: Key) -> tuple[str, dict[str, int]]:
    """VexFlow key-signature name + its letter→accidental map.

    Uses the NATURAL key signature: harmonic minor shares natural minor's
    signature (its raised 7th is drawn as an explicit accidental, not baked into
    the signature). Returns e.g. ("G", {"F": 1, ...}) or ("Am", {all 0}).
    """
    base_mode = "major" if k.mode == "major" else "natural_minor"
    natural = Key(k.tonic_letter, k.tonic_accidental, base_mode)
    name = f"{k.tonic_letter}{_ACC_TEXT[k.tonic_accidental]}"
    if base_mode == "natural_minor":
        name += "m"
    return name, natural.accidental_by_letter()


def realize_note(k: Key, tonic_octave: int, d: int) -> tuple[str, int]:
    """Realize diatonic index `d` in key `k` (tonic at `tonic_octave`).

    Returns (note_name, midi).
    """
    acc_by_letter = k.accidental_by_letter()
    tonic_abs = _abs_position(k.tonic_letter, tonic_octave)
    abs_pos = tonic_abs + d
    octave, li = divmod(abs_pos, 7)
    letter = LETTERS[li]
    acc = acc_by_letter[letter]
    return note_name(letter, acc, octave), note_midi(letter, acc, octave)


def degree_number(d: int) -> int:
    """Scale-degree number 1..7 for a diatonic index (octave-agnostic)."""
    return (d % 7) + 1


def diatonic_semitone(d: int, mode: str = "major") -> int:
    """Semitone height of diatonic index `d` above the tonic, for a given mode.

    Key-independent (transposition preserves intervals): a melodic interval's
    semitone size is ``diatonic_semitone(b) - diatonic_semitone(a)``. Lets the
    key-agnostic generator reason about *interval quality* (e.g. reject a
    6-semitone melodic tritone) without committing to a key.
    """
    steps = MODE_STEPS[mode]
    octave, pos = divmod(d, 7)
    return steps[pos] + 12 * octave


def solfege(k: Key, d: int) -> str:
    return k.solfege_syllables()[d % 7]


def is_tendency_tone(k: Key, d: int) -> bool:
    """Fa (deg 4) and Ti (deg 7, leading tone) in major; la-minor analogues."""
    deg = degree_number(d)
    if k.mode == "major":
        return deg in (4, 7)
    # la-based minor: unstable tones are re(4→3) and, in harmonic minor, si(7).
    if k.mode == "harmonic_minor":
        return deg in (4, 7)
    return deg == 4  # natural minor: fa pulls to mi; no true leading tone


# --- clef anchoring (MIDI) ---------------------------------------------------
# The tonic sits at a FIXED octave per (key, clef) so "do" (or "la") is always
# the same pitch across every card in that key — the learner establishes the
# tonal centre once. The anchor is a low-ish staff target so melodies rise into
# the staff; a few lower-neighbour/descent notes dip just below.
CLEF_TONIC_ANCHOR = {"treble": 64, "bass": 47}  # ~E4 / ~B2


def tonic_octave_for(k: Key, clef: str) -> int:
    """Fixed tonic octave for a key/clef (independent of any melody)."""
    target = CLEF_TONIC_ANCHOR[clef]
    best_octave, best = 4, None
    for tonic_octave in range(1, 7):
        midi = realize_note(k, tonic_octave, 0)[1]
        dist = abs(midi - target)
        if best is None or dist < best:
            best, best_octave = dist, tonic_octave
    return best_octave


def realize_sequence(
    k: Key, degrees: list[int], clef: str
) -> list[dict[str, object]]:
    """Realize a degree sequence into per-note data for a key/mode/clef."""
    tonic_octave = tonic_octave_for(k, clef)
    out = []
    for d in degrees:
        name, midi = realize_note(k, tonic_octave, d)
        out.append(
            {
                "d": d,
                "note": name,
                "midi": midi,
                "degree": degree_number(d),
                "solfege": solfege(k, d),
                "tendency": is_tendency_tone(k, d),
            }
        )
    return out
