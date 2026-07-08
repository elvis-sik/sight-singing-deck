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
from sight_singing.generate.errors import make_error_variants
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

# One quarter note per index; a length-4 melody is exactly one 4/4 bar. Longer
# phrases (length 5-6) span multiple bars — the renderer splits them at the
# barline and pads the final bar with rests. Rhythmic variety arrives with the
# rhythm ladder (a separate pass).
_DEFAULT_DURATION = "q"


def _durations_for(stage: Stage, n: int) -> list[str]:
    """Per-note note values for a stage's melodies.

    Isolated interval drills are two *sustained* pitches (hear one, sing the
    other): notate and sound them as half notes so the two notes fill a complete
    4/4 bar instead of leaving beats 3-4 empty. Every other stage keeps one
    quarter per index.
    """
    if stage.phase in ("intervals", "dictation-interval"):
        return ["h"] * n
    return [_DEFAULT_DURATION] * n


def _melody_id(
    stage_id: str,
    degrees_idx: tuple[int, ...],
    key_name: str = "C",
    mode: str = "major",
    clef: str = "treble",
) -> str:
    """Stable, content-derived id (regenerating the library keeps ids fixed).

    The default C-major/treble context keeps bare ids (stable across builds); any
    other key/mode/clef gets a short context suffix so the same melody realized in
    different keys/clefs stays globally unique.
    """
    blob = f"{stage_id}:{','.join(str(d) for d in degrees_idx)}"
    digest = hashlib.sha1(blob.encode("utf-8")).hexdigest()[:8]
    base = f"{stage_id.lower()}_{digest}"
    if (key_name, mode, clef) == ("C", "major", "treble"):
        return base
    tag = f"{key_name}{'maj' if mode == 'major' else 'min'}{clef[0]}".lower()
    return f"{base}_{tag}"


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
    durations = _durations_for(stage, len(notes))
    degrees = [int(str(item["degree"])) for item in realized]
    solfege = [str(item["solfege"]) for item in realized]

    return {
        "id": _melody_id(stage.id, degrees_idx, key_name, mode, clef),
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
    per_stage: int | None = None,
) -> list[dict[str, object]]:
    """Generate + realize every stage into an ordered melody library.

    Melodies keep curriculum order (stage by stage, quality-ranked within a
    stage), which is also a sensible default study order. ``per_stage`` caps the
    melodies kept per stage (for bounded transfer tracks in extra keys/clefs).
    """
    stages = list(stages if stages is not None else MAJOR_STAGES)
    library: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for stage in stages:
        kept = generate_stage(stage)
        if per_stage is not None:
            kept = kept[:per_stage]
        for degrees_idx in kept:
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
    max_variants: int = 6,
) -> list[dict[str, object]]:
    """Error-detection cases: one base melody, MANY single-note error variants.

    Each record carries the ``written`` melody record (for notation + the
    "as written" clip) and a list of ``variants``; each variant is a distinct
    wrong performance (realized ``played_notes``, its ``error_index``, a reveal
    ``label``, and a stable ``sub_id`` used to name its clip). The card picks a
    variant per study view, so the wrong note is not memorisable to one spot.
    """
    k = make_key(key_name, mode)
    out: list[dict[str, object]] = []
    for stage in stages:
        made = 0
        for degrees_idx in generate_stage(stage):
            if made >= per_stage:
                break
            cases = make_error_variants(tuple(degrees_idx), max_variants=max_variants)
            if not cases:
                continue
            written = realize_stage_melody(
                stage, degrees_idx, key_name=key_name, mode=mode, clef=clef
            )
            written_notes = written["notes"]
            assert isinstance(written_notes, list)
            variants: list[dict[str, object]] = []
            for vn, case in enumerate(cases):
                played_idx = list(case["played"])  # type: ignore[call-overload]
                played_seq = realize_sequence(k, played_idx, clef)
                played_notes = [str(item["note"]) for item in played_seq]
                i = int(str(case["error_index"]))
                w_idx = int(str(case["written_index"]))
                p_idx = int(str(case["played_index"]))
                w_pitch = str(written_notes[i])
                p_pitch = played_notes[i]
                variants.append(
                    {
                        "sub_id": f"{written['id']}_e{vn}",
                        "played_notes": played_notes,
                        "error_index": i,
                        "label": (
                            f"Note {i + 1}: written {solfege(k, w_idx)} "
                            f"({w_pitch}), played {solfege(k, p_idx)} ({p_pitch})."
                        ),
                    }
                )
            made += 1
            out.append(
                {
                    "id": str(written["id"]),
                    "stage_id": stage.id,
                    "phase": stage.phase,
                    "title": stage.title,
                    "written": written,
                    "variants": variants,
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


_RHYTHM_PITCH = {"treble": "B4", "bass": "D3"}


def build_rhythm_library(clef: str = "treble") -> list[dict[str, object]]:
    """Rhythm-first cards: one bar per card on a single repeated pitch.

    Reuses the melody-record shape (so ``melody_to_card_fields`` and the audio
    renderer work unchanged); the pitch is constant and the interest is timing.
    """
    from sight_singing.generate.rhythm import RHYTHM_STAGES, generate_rhythm_stage

    pitch = _RHYTHM_PITCH.get(clef, "B4")
    library: list[dict[str, object]] = []
    for stage in RHYTHM_STAGES:
        for bar in generate_rhythm_stage(stage):
            audio = bar["audio"]
            durations = [d for d, _rest in audio]
            notes = [("rest" if is_rest else pitch) for _d, is_rest in audio]
            render_events = []
            for e in bar["render"]:
                item = dict(e)
                if item.get("kind") != "rest":
                    item["pitch"] = pitch
                render_events.append(item)
            blob = f"{stage.id}:{clef}:" + "|".join(
                f"{e.get('duration')}{'t' if e.get('tie') else ''}"
                f"{'T' if e.get('tuplet') else ''}"
                for e in render_events
            )
            digest = hashlib.sha1(blob.encode("utf-8")).hexdigest()[:8]
            library.append(
                {
                    "id": f"{stage.id.lower()}_{clef[0]}_{digest}",
                    "stage_id": stage.id,
                    "title": stage.title,
                    "notes": notes,
                    "durations": durations,
                    "render_events": render_events,
                    "degrees": [],  # rhythm cards have no scale-degree chips
                    "clef": clef,
                    "key": "C",
                    "mode": "major",
                    "tonic": pitch,
                    "tags": [
                        "sight_singing",
                        "track::rhythm",
                        f"stage::{stage.id}",
                        f"clef::{clef}",
                    ],
                }
            )
    return library


def error_audio_entries(error_lib: list[dict[str, object]]) -> list[dict[str, object]]:
    """Flatten error records into melody dicts for ``build_library_audio``.

    Emits the written (correct) clip plus one clip per variant, under the
    ``<id>_e{n}`` ids that ``card_data`` references. The card plays a randomly
    chosen variant clip each view.
    """
    entries: list[dict[str, object]] = []
    for rec in error_lib:
        written = rec["written"]
        assert isinstance(written, dict)
        entries.append(written)
        variants = rec["variants"]
        assert isinstance(variants, list)
        for v in variants:
            entries.append(
                {
                    "id": str(v["sub_id"]),
                    "notes": v["played_notes"],
                    "durations": written["durations"],
                    "tonic": written["tonic"],
                }
            )
    return entries
