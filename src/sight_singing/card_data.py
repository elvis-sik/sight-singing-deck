"""Serialize melody dicts into Anki note fields."""

from __future__ import annotations

import json
from typing import Any


def melody_to_card_fields(melody: dict[str, Any]) -> dict[str, str]:
    notes = melody["notes"]
    if not isinstance(notes, list):
        raise TypeError("melody['notes'] must be a list")

    payload = {
        "clef": "treble",
        "key": "C",
        "mode": "major",
        "timeSig": "4/4",
        "notes": notes,
        "durations": ["q", "q", "q", "q"],
        "degrees": melody["degrees"],
        "supports": {
            "tonic": "C4",
            "firstNote": notes[0],
            "cadenceKey": "C",
        },
    }

    return {
        "MelodyJSON": json.dumps(payload, separators=(",", ":")),
        "StageID": "stage1",
        "MelodyID": str(melody["id"]),
    }
