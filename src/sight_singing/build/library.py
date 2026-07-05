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
from sight_singing.generate.melody_gen import generate_stage
from sight_singing.theory.scales import (
    key as make_key,
)
from sight_singing.theory.scales import (
    realize_note,
    realize_sequence,
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
    """Realize one degree sequence for a stage into a card-ready record."""
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
