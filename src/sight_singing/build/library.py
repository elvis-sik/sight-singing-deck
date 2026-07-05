"""Realize curriculum stages into a concrete melody library.

Each library record is a plain dict ready for both the audio renderer
(``audio_assets.build_library_audio``) and the card serializer
(``card_data.melody_to_card_fields``):

    {
      "id", "stage_id", "phase", "title",   # provenance
      "degrees_idx",                          # raw diatonic indices (tuple)
      "notes", "durations", "degrees",        # realized, card-ready
      "solfege",                              # per-note syllables
      "clef", "key", "mode", "tonic",         # tonal context
      "tags",                                 # Anki tags
    }

Diatonic indices are key/mode/clef-independent; realization happens here so the
same generated melody can be re-used across keys and clefs later.
"""

from __future__ import annotations

import hashlib

from sight_singing.curriculum.stages import MAJOR_STAGES, Stage
from sight_singing.generate.errors import make_error_case
from sight_singing.generate.melody_gen import generate_stage
from sight_singing.theory.scales import (
    key as make_key,
)
from sight_singing.theory.scales import (
    realize_note,
    realize_sequence,
    solfege,
    tonic_octave_for,
)

# One quarter note per index; a length-4 melody is exactly one 4/4 bar. Rhythmic
# variety and longer phrases arrive with the rhythm ladder (a separate pass);
# the renderer draws a single stave, so we keep melodies to one bar for now.
_DEFAULT_DURATION = "q"


def _melody_id(stage_id: str, degrees_idx: tuple[int, ...]) -> str:
    """Stable, content-derived id (regenerating the library keeps ids fixed)."""
    blob = f"{stage_id}:{','.join(str(d) for d in degrees_idx)}"
    digest = hashlib.sha1(blob.encode("utf-8")).hexdigest()[:8]
    return f"{stage_id.lower()}_{digest}"


def realize_stage_melody(
    stage: Stage,
    degrees_idx: tuple[int, ...],
    *,
    key_name: str = "C",
    mode: str = "major",
    clef: str = "treble",
) -> dict[str, object]:
    """Realize one degree sequence for a stage into a card-ready record.

    The stage may override the realization ``mode`` (e.g. a harmonic-minor
    leading-tone stage inside an otherwise natural-minor ladder).
    """
    mode = stage.mode or mode
    k = make_key(key_name, mode)
    realized = realize_sequence(k, list(degrees_idx), clef)
    tonic_octave = tonic_octave_for(k, clef)
    tonic_note = realize_note(k, tonic_octave, 0)[0]

    notes = [str(item["note"]) for item in realized]
    durations = [_DEFAULT_DURATION] * len(notes)
    degrees = [int(str(item["degree"])) for item in realized]
    solfege = [str(item["solfege"]) for item in realized]

    return {
        "id": _melody_id(stage.id, degrees_idx),
        "stage_id": stage.id,
        "phase": stage.phase,
        "title": stage.title,
        "degrees_idx": tuple(degrees_idx),
        "notes": notes,
        "durations": durations,
        "degrees": degrees,
        "solfege": solfege,
        "clef": clef,
        "key": key_name,
        "mode": mode,
        "tonic": tonic_note,
        "tags": [
            "sight_singing",
            f"phase::{stage.phase}",
            f"stage::{stage.id}",
            f"key::{key_name}_{mode}",
            f"clef::{clef}",
        ],
    }


def build_library(
    stages: list[Stage] | None = None,
    *,
    key_name: str = "C",
    mode: str = "major",
    clef: str = "treble",
) -> list[dict[str, object]]:
    """Generate + realize every stage into an ordered melody library.

    Melodies keep curriculum order (stage by stage, quality-ranked within a
    stage), which is also a sensible default study order.
    """
    stages = list(stages if stages is not None else MAJOR_STAGES)
    library: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for stage in stages:
        for degrees_idx in generate_stage(stage):
            record = realize_stage_melody(
                stage, degrees_idx, key_name=key_name, mode=mode, clef=clef
            )
            if record["id"] in seen_ids:
                continue
            seen_ids.add(str(record["id"]))
            library.append(record)
    return library


def build_error_library(
    stages: list[Stage],
    *,
    key_name: str = "C",
    mode: str = "major",
    clef: str = "treble",
    per_stage: int = 8,
) -> list[dict[str, object]]:
    """Error-detection cases: take base melodies and alter one note each.

    Each record carries the ``written`` melody record (for notation + the
    "as written" clip), the realized ``played_notes`` (the wrong performance),
    the ``error_index``, a reveal ``error_label``, and Anki ``tags``.
    """
    k = make_key(key_name, mode)
    out: list[dict[str, object]] = []
    for stage in stages:
        made = 0
        for degrees_idx in generate_stage(stage):
            if made >= per_stage:
                break
            case = make_error_case(tuple(degrees_idx))
            if case is None:
                continue
            written = realize_stage_melody(
                stage, degrees_idx, key_name=key_name, mode=mode, clef=clef
            )
            played_idx = list(case["played"])  # type: ignore[call-overload]
            played_seq = realize_sequence(k, played_idx, clef)
            played_notes = [str(item["note"]) for item in played_seq]
            i = int(str(case["error_index"]))
            w_idx = int(str(case["written_index"]))
            p_idx = int(str(case["played_index"]))
            written_notes = written["notes"]
            assert isinstance(written_notes, list)
            w_pitch = str(written_notes[i])
            p_pitch = played_notes[i]
            label = (
                f"Note {i + 1}: written {solfege(k, w_idx)} ({w_pitch}), "
                f"played {solfege(k, p_idx)} ({p_pitch})."
            )
            made += 1
            out.append(
                {
                    "id": str(written["id"]),
                    "stage_id": stage.id,
                    "phase": stage.phase,
                    "title": stage.title,
                    "written": written,
                    "played_notes": played_notes,
                    "error_index": i,
                    "error_label": label,
                    "tags": [
                        "sight_singing",
                        "track::errors",
                        f"phase::{stage.phase}",
                        f"stage::{stage.id}",
                        f"key::{key_name}_{mode}",
                    ],
                }
            )
    return out


def error_audio_entries(error_lib: list[dict[str, object]]) -> list[dict[str, object]]:
    """Flatten error records into melody dicts for ``build_library_audio``.

    Emits both the written clip (from the written record) and the played
    (altered) clip under the ``<id>_e`` id that ``card_data`` references.
    """
    entries: list[dict[str, object]] = []
    for rec in error_lib:
        written = rec["written"]
        assert isinstance(written, dict)
        entries.append(written)
        entries.append(
            {
                "id": str(written["id"]) + "_e",
                "notes": rec["played_notes"],
                "durations": written["durations"],
                "tonic": written["tonic"],
            }
        )
    return entries
