"""Synthesize mono 16-bit WAV (triangle + ADSR) for deck audio assets."""

from __future__ import annotations

import array
import re
import struct
from pathlib import Path
from typing import Iterable

SAMPLE_RATE = 22050

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note_to_midi(name: str) -> int:
    m = re.match(r"^([A-Ga-g])([#b]?)(\d+)$", name.strip())
    if not m:
        return 60
    letter = m.group(1).upper()
    acc = m.group(2) or ""
    octv = int(m.group(3))
    pc = _PC[letter]
    if acc == "#":
        pc += 1
    if acc == "b":
        pc -= 1
    return (octv + 1) * 12 + pc


def midi_to_freq(midi: int) -> float:
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def note_to_freq(name: str) -> float:
    return midi_to_freq(note_to_midi(name))


def triangle_sample(t: float, freq: float) -> float:
    phase = (t * freq) % 1.0
    if phase < 0:
        phase += 1.0
    return 1.0 - 4.0 * abs(phase - 0.5)


def envelope_amp(i: int, note_len_samples: int, sr: int = SAMPLE_RATE) -> float:
    atk = max(1, int(0.02 * sr))
    dec = max(1, int(0.04 * sr))
    rel = max(1, int(0.12 * sr))
    peak = 0.22
    sus = 0.12
    if i < atk:
        return 0.0001 + (peak - 0.0001) * (i / atk)
    if i < atk + dec:
        u = (i - atk) / dec
        return peak * ((sus / peak) ** u)
    sustain_end = note_len_samples - rel
    if i < sustain_end:
        return sus
    if i >= note_len_samples:
        return 0.0
    v = (i - sustain_end) / rel
    return sus * ((0.0001 / sus) ** min(1.0, v))


def render_note_samples(freq_hz: float, duration_sec: float, sr: int = SAMPLE_RATE) -> list[int]:
    n = max(1, int(duration_sec * sr))
    out: list[int] = []
    for i in range(n):
        t = i / sr
        amp = envelope_amp(i, n, sr)
        s = triangle_sample(t, freq_hz) * amp
        v = int(round(s * 32000))
        v = max(-32768, min(32767, v))
        out.append(v)
    return out


def silence_samples(duration_sec: float, sr: int = SAMPLE_RATE) -> list[int]:
    return [0] * max(0, int(duration_sec * sr))


def concat_samples(parts: Iterable[list[int]]) -> list[int]:
    out: list[int] = []
    for p in parts:
        out.extend(p)
    return out


def write_wav_int16_mono(path: Path, samples: list[int], sr: int = SAMPLE_RATE) -> None:
    data_size = len(samples) * 2
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        sr,
        sr * 2,
        2,
        16,
        b"data",
        data_size,
    )
    body = array.array("h", samples).tobytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + body)
