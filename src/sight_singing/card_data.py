"""Serialize melody dicts into Anki note fields."""

from __future__ import annotations

import json
from typing import Any

from sight_singing.audio_assets import (
    CADENCE_FILENAME,
    melody_clip_filename_for,
    note_clip_filename,
)


def melody_to_card_fields(melody: dict[str, Any]) -> dict[str, str]:
    """Serialize one melody into Anki note fields.

    Recognized (all optional, defaulting to the C-major/treble MVP context):
    ``notes``, ``durations``, ``degrees``, ``id``, ``stage_id``, ``clef``,
    ``key`` (name like "C"), ``mode``, and ``tonic`` (note name of the tonal
    centre, e.g. "C4"). Melody audio is content-hashed from notes/durations, so
    this works for both hardcoded and generated melodies.
    """
    notes = melody["notes"]
    if not isinstance(notes, list):
        raise TypeError("melody['notes'] must be a list")
    durations = melody.get("durations", ["q"] * len(notes))
    if not isinstance(durations, list):
        raise TypeError("melody['durations'] must be a list when present")
    if len(durations) != len(notes):
        raise ValueError("melody notes and durations must have the same length")

    mid = str(melody["id"])
    clef = str(melody.get("clef", "treble"))
    key_name = str(melody.get("key", "C"))
    mode = str(melody.get("mode", "major"))
    stage_id = str(melody.get("stage_id", "stage1"))

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
    tonic_note = str(melody.get("tonic", "C4"))

    melody_file = melody_clip_filename_for(
        mid, [str(n) for n in notes], [str(d) for d in durations]
    )
    first_file = note_clip_filename(first_sounded_note)
    tonic_file = note_clip_filename(tonic_note)

    payload = {
        "version": 2,
        "clef": clef,
        "key": key_name,
        "mode": mode,
        "timeSig": "4/4",
        "notes": notes,
        "durations": durations,
        "bars": [{"events": events}],
        "degrees": melody["degrees"],
        "supports": {
            "tonic": tonic_note,
            "firstNote": first_sounded_note,
            "cadenceKey": key_name,
        },
        "audio": {
            "melody": melody_file,
            "cadence": CADENCE_FILENAME,
            "first": first_file,
            "tonic": tonic_file,
        },
    }

    return {
        "MelodyJSON": json.dumps(payload, separators=(",", ":")),
        "StageID": stage_id,
        "MelodyID": mid,
        "CadenceAudio": f"[sound:{CADENCE_FILENAME}]",
        "FirstNoteAudio": f"[sound:{first_file}]",
        "TonicAudio": f"[sound:{tonic_file}]",
        "MelodyAudio": f"[sound:{melody_file}]",
        "CadenceAudioFile": CADENCE_FILENAME,
        "FirstNoteAudioFile": first_file,
        "TonicAudioFile": tonic_file,
        "MelodyAudioFile": melody_file,
    }
