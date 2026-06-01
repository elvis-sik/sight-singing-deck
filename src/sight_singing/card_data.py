"""Serialize melody dicts into Anki note fields."""

from __future__ import annotations

import json
from typing import Any

from sight_singing.audio_assets import (
    CADENCE_FILENAME,
    melody_clip_filename,
    note_clip_filename,
)


def melody_to_card_fields(melody: dict[str, Any]) -> dict[str, str]:
    notes = melody["notes"]
    if not isinstance(notes, list):
        raise TypeError("melody['notes'] must be a list")
    durations = melody.get("durations", ["q"] * len(notes))
    if not isinstance(durations, list):
        raise TypeError("melody['durations'] must be a list when present")
    if len(durations) != len(notes):
        raise ValueError("melody notes and durations must have the same length")

    mid = str(melody["id"])
    events = []
    for note, duration in zip(notes, durations):
        if note in (None, "rest"):
            events.append({"kind": "rest", "duration": str(duration)})
        else:
            events.append(
                {
                    "kind": "note",
                    "pitch": str(note),
                    "duration": str(duration),
                }
            )

    first_sounded_note = next(
        (str(note) for note in notes if note not in (None, "rest")),
        "C4",
    )

    payload = {
        "version": 2,
        "clef": "treble",
        "key": "C",
        "mode": "major",
        "timeSig": "4/4",
        "notes": notes,
        "durations": durations,
        "bars": [{"events": events}],
        "degrees": melody["degrees"],
        "supports": {
            "tonic": "C4",
            "firstNote": first_sounded_note,
            "cadenceKey": "C",
        },
        "audio": {
            "melody": melody_clip_filename(mid),
            "cadence": CADENCE_FILENAME,
            "first": note_clip_filename(first_sounded_note),
            "tonic": note_clip_filename("C4"),
        },
    }
    melody_audio = f"[sound:{melody_clip_filename(mid)}]"
    cadence_audio = f"[sound:{CADENCE_FILENAME}]"
    first_note_audio = f"[sound:{note_clip_filename(first_sounded_note)}]"
    tonic_audio = f"[sound:{note_clip_filename('C4')}]"

    return {
        "MelodyJSON": json.dumps(payload, separators=(",", ":")),
        "StageID": "stage1",
        "MelodyID": str(melody["id"]),
        "CadenceAudio": cadence_audio,
        "FirstNoteAudio": first_note_audio,
        "TonicAudio": tonic_audio,
        "MelodyAudio": melody_audio,
        "CadenceAudioFile": CADENCE_FILENAME,
        "FirstNoteAudioFile": note_clip_filename(first_sounded_note),
        "TonicAudioFile": note_clip_filename("C4"),
        "MelodyAudioFile": melody_clip_filename(mid),
    }
