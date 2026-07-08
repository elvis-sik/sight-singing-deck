"""Serialize melody dicts into Anki note fields."""

from __future__ import annotations

import json
from typing import Any

from sight_singing.audio_assets import (
    cadence_filename_for,
    drone_clip_filename,
    melody_clip_filename_for,
    note_clip_filename,
)
from sight_singing.theory.scales import key as make_key
from sight_singing.theory.scales import key_signature


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
    key_sig, key_accidentals = key_signature(make_key(key_name, mode))

    # Notation events. Ties/triplets need a notation view that differs from the
    # audio view (a tie is one sustained note in audio but two tied notes on the
    # staff; a triplet eighth is 1/3 beat), so a melody may carry an explicit
    # ``render_events`` for the staff while ``notes``/``durations`` drive audio.
    render_events = melody.get("render_events")
    if render_events:
        events = [dict(e) for e in render_events]
    else:
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

    cadence_file = cadence_filename_for(key_name, mode, clef)
    melody_file = melody_clip_filename_for(
        mid, [str(n) for n in notes], [str(d) for d in durations]
    )
    first_file = note_clip_filename(first_sounded_note)
    tonic_file = note_clip_filename(tonic_note)
    drone_file = drone_clip_filename(tonic_note)

    payload = {
        "version": 2,
        "clef": clef,
        "key": key_name,
        "mode": mode,
        "keySig": key_sig,
        "keyAccidentals": key_accidentals,
        "timeSig": str(melody.get("time_sig", "4/4")),
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
            "cadence": cadence_file,
            "first": first_file,
            "tonic": tonic_file,
            "drone": drone_file,
        },
    }
    # Rhythm-dictation cards grade by sounded rhythm (pitch-agnostic, rest-spelling
    # equivalent). Only emitted when set, so melodic MelodyJSON stays unchanged.
    grade_mode = melody.get("grade_mode")
    if grade_mode:
        payload["gradeMode"] = str(grade_mode)

    return {
        "MelodyJSON": json.dumps(payload, separators=(",", ":")),
        "StageID": stage_id,
        "MelodyID": mid,
        "CadenceAudio": f"[sound:{cadence_file}]",
        "FirstNoteAudio": f"[sound:{first_file}]",
        "TonicAudio": f"[sound:{tonic_file}]",
        "MelodyAudio": f"[sound:{melody_file}]",
        "DroneAudio": f"[sound:{drone_file}]",
        "CadenceAudioFile": cadence_file,
        "FirstNoteAudioFile": first_file,
        "TonicAudioFile": tonic_file,
        "MelodyAudioFile": melody_file,
        "DroneAudioFile": drone_file,
    }


def error_to_card_fields(
    written: dict[str, Any],
    variants: list[dict[str, Any]],
) -> dict[str, str]:
    """Serialize an error-detection note with MANY wrong-performance variants.

    ``written`` is the correct melody record (notation + "as written" clip).
    ``variants`` is the list from ``build_error_library`` — each a distinct
    single-note alteration with its ``played_notes``, ``error_index``, ``label``
    and ``sub_id``. The card picks one variant per view (client-side), so the
    ErrorVariants field ships ALL of them: the wrong note is never at a fixed
    spot across reviews.
    """
    base = melody_to_card_fields(written)
    durations = [str(d) for d in written.get("durations", ["q"] * len(written["notes"]))]
    payload = []
    for v in variants:
        played_file = melody_clip_filename_for(
            str(v["sub_id"]),
            [str(n) for n in v["played_notes"]],
            durations,
        )
        payload.append(
            {
                "f": played_file,              # clip of this wrong performance
                "i": int(v["error_index"]),    # which note is wrong
                "label": str(v["label"]),      # human reveal
            }
        )
    return {
        "MelodyJSON": base["MelodyJSON"],
        "StageID": base["StageID"],
        "MelodyID": base["MelodyID"],
        "ErrorVariants": json.dumps(payload, separators=(",", ":")),
        "CadenceAudioFile": base["CadenceAudioFile"],
        "FirstNoteAudioFile": base["FirstNoteAudioFile"],
        "TonicAudioFile": base["TonicAudioFile"],
        "DroneAudioFile": base["DroneAudioFile"],
        "WrittenAudioFile": base["MelodyAudioFile"],  # the correct melody
    }
