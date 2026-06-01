"""Tiny MIDI writer for offline piano rendering."""

from __future__ import annotations

from pathlib import Path

TICKS_PER_QUARTER = 480


def _var_len(value: int) -> bytes:
    if value < 0:
        raise ValueError("delta time must be non-negative")
    parts = [value & 0x7F]
    value >>= 7
    while value:
        parts.append(0x80 | (value & 0x7F))
        value >>= 7
    return bytes(reversed(parts))


def _tempo_meta(microseconds_per_quarter: int) -> bytes:
    return bytes(
        [
            0x00,
            0xFF,
            0x51,
            0x03,
            (microseconds_per_quarter >> 16) & 0xFF,
            (microseconds_per_quarter >> 8) & 0xFF,
            microseconds_per_quarter & 0xFF,
        ]
    )


def _end_of_track() -> bytes:
    return b"\x00\xFF\x2F\x00"


def write_midi(
    out_path: Path,
    *,
    microseconds_per_quarter: int,
    notes: list[dict[str, int]],
    program: int = 0,
) -> None:
    """Write a format-0 MIDI file.

    Each note entry must provide:

    - ``pitch``: MIDI note number
    - ``start_tick``: absolute start tick
    - ``duration_ticks``: note length in ticks
    - optional ``velocity``: 1-127, default 96
    """

    events: list[tuple[int, bytes]] = [(0, bytes([0xC0, int(program) & 0x7F]))]
    for note in notes:
        pitch = int(note["pitch"])
        start_tick = int(note["start_tick"])
        duration_ticks = int(note["duration_ticks"])
        velocity = int(note.get("velocity", 96))
        if duration_ticks <= 0:
            raise ValueError("duration_ticks must be positive")
        events.append((start_tick, bytes([0x90, pitch, velocity])))
        events.append((start_tick + duration_ticks, bytes([0x80, pitch, 0x40])))

    events.sort(key=lambda item: (item[0], item[1][0] != 0x90, item[1][1]))

    track = bytearray()
    track.extend(_tempo_meta(microseconds_per_quarter))

    previous_tick = 0
    for tick, message in events:
        delta = tick - previous_tick
        track.extend(_var_len(delta))
        track.extend(message)
        previous_tick = tick

    track.extend(_end_of_track())

    header = (
        b"MThd"
        + (6).to_bytes(4, "big")
        + (0).to_bytes(2, "big")
        + (1).to_bytes(2, "big")
        + TICKS_PER_QUARTER.to_bytes(2, "big")
    )
    chunk = b"MTrk" + len(track).to_bytes(4, "big") + bytes(track)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(header + chunk)
