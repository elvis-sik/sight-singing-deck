#!/usr/bin/env python3
"""Build the melodic-dictation .apkg (its own deck tree and note type).

Dictation is a curriculum in its own right (see DICTATION_CURRICULUM.md, rev 3):
ordered by phrase length + working memory + interval audibility, with its own
pool. This builds the PITCH-ONLY, even-rhythm spine — a priming floor (DP0 tonic
echo, DP1/DP2 two-note rungs) then DD1-DD9 — realized in C major, treble clef,
into a top-level ``Dictation`` deck tree. Each melody is one Dictate card (hear ->
notate) on the single-template dictation note type, carrying per-stage
listen-count thresholds.

Run:  python scripts/build_dictation_deck.py [--limit N]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
_SCRIPTS = _ROOT / "scripts"
for p in (_SRC, _SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import genanki

from build_deck import write_package  # reuse apkg writer + autoplay-off
from sight_singing.anki_model import (
    DICTATION_FIELD_NAMES,
    DICTATION_MODEL_NAME,
    make_dictation_model,
)
from sight_singing.audio_assets import build_library_audio, library_audio_basenames
from sight_singing.build.library import build_library, realize_stage_melody
from sight_singing.card_data import melody_to_card_fields
from sight_singing.curriculum.stages import (
    DICTATION_PRIMING_SINGLETONS,
    DICTATION_STAGES,
    Stage,
)

# Own deck-id range, well clear of the sight-singing tree.
DICT_DECK_BASE = 2_948_817_900

_DICT_ROOT_DESC = (
    "Melodic dictation — hear a short melody, then notate it. Its OWN curriculum, "
    "ordered by phrase length and memory (not vocal difficulty). Work top to bottom: "
    "the priming floor (DP0-DP2) first, then DD1-DD9. Every card establishes the key "
    "and the melody is replayable; the <b>listen count</b> on the front is your "
    "effort gauge — grade by how many replays it took."
)

# DP0 is a fixed set of single-degree echoes (a lone note isn't a generatable
# melody, so it isn't a Stage); this carrier lets us realize the singletons
# through the normal pipeline.
_DP0 = Stage(
    "DP0", "Tonic Echo", "dictation",
    pool=(0, 2, 4), start_pool=(0, 2, 4), end_pool=(0, 2, 4),
    max_step=4, count=len(DICTATION_PRIMING_SINGLETONS), length=1,
    notes="Hear the key, identify one degree (do/mi/so).",
)


def _listen_targets(length: int) -> dict[str, int]:
    """Per-stage listen-count thresholds, scaling with phrase length.

    ``good`` = replays at/under which the recall was easy; ``hard`` = the ceiling
    before it's really an ``Again``. Longer phrases earn more slack. Editable per
    card (the field ships the JSON).
    """
    good = max(1, length - 2)
    hard = max(good + 1, length)
    return {"good": good, "hard": hard}


def _ordered_records() -> list[tuple[str, dict[str, object]]]:
    """(stage_id, record) in curriculum order: DP0 singletons, then DD stages."""
    records: list[tuple[str, dict[str, object]]] = []
    for degrees in DICTATION_PRIMING_SINGLETONS:
        rec = realize_stage_melody(_DP0, degrees, key_name="C", mode="major", clef="treble")
        records.append(("DP0", rec))
    for stage in DICTATION_STAGES:
        lib = build_library([stage], key_name="C", mode="major", clef="treble")
        for rec in lib:
            records.append((stage.id, rec))
    return records


def _stage_order() -> list[tuple[str, str, int]]:
    """(stage_id, title, length) for every stage, DP0 first, in ladder order."""
    out = [("DP0", _DP0.title, _DP0.length)]
    out += [(s.id, s.title, s.length) for s in DICTATION_STAGES]
    return out


def build(out_path: Path, base_deck_name: str, assets_dir: Path, limit: int | None) -> int:
    records = _ordered_records()
    if limit is not None:
        # Keep it per-stage so a smoke build still spans the ladder.
        by_stage: dict[str, int] = {}
        trimmed: list[tuple[str, dict[str, object]]] = []
        for sid, rec in records:
            n = by_stage.get(sid, 0)
            if n < limit:
                trimmed.append((sid, rec))
                by_stage[sid] = n + 1
        records = trimmed

    audio_library = [rec for _, rec in records]
    print(f"Rendering audio for {len(audio_library)} dictation melodies …", flush=True)
    build_library_audio(assets_dir, audio_library)

    model = make_dictation_model()
    length_by_stage = {sid: length for sid, _title, length in _stage_order()}
    order = {sid: i for i, (sid, _t, _l) in enumerate(_stage_order())}
    title_by_stage = {sid: title for sid, title, _l in _stage_order()}

    decks: dict[str, genanki.Deck] = {}
    for sid, rec in records:
        if sid not in decks:
            idx = order.get(sid, 99)
            name = f"{base_deck_name}::{idx:02d} {sid} · {title_by_stage.get(sid, sid)}"
            decks[sid] = genanki.Deck(deck_id=DICT_DECK_BASE + 1 + idx, name=name)
        fields = melody_to_card_fields(rec)
        fields["ListenTargets"] = json.dumps(
            _listen_targets(length_by_stage.get(sid, 4)), separators=(",", ":")
        )
        tags = rec.get("tags", [])
        assert isinstance(tags, list)
        note = genanki.Note(
            model=model,
            fields=[fields[f] for f in DICTATION_FIELD_NAMES],
            tags=[str(t) for t in tags if not str(t).startswith("track::")]
            + ["track::dictation"],
        )
        decks[sid].add_note(note)

    umbrella = genanki.Deck(
        deck_id=DICT_DECK_BASE, name=base_deck_name, description=_DICT_ROOT_DESC
    )
    ordered = [umbrella] + [decks[sid] for sid, _t, _l in _stage_order() if sid in decks]
    pkg = genanki.Package(ordered)

    media_files: list[str] = []
    for bn in library_audio_basenames(audio_library):
        clip = assets_dir / bn
        if not clip.is_file():
            raise FileNotFoundError(f"Missing generated audio {clip}")
        media_files.append(str(clip))
    pkg.media_files = media_files

    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_package(pkg, out_path)
    return len(records)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build the melodic-dictation deck.")
    ap.add_argument("--out", type=Path, default=_ROOT / "out" / "dictation-curriculum.apkg")
    ap.add_argument("--deck-name", default="Dictation")
    ap.add_argument("--assets", type=Path, default=_ROOT / "assets")
    ap.add_argument("--limit", type=int, default=None,
                    help="Cap melodies per stage (fast smoke build).")
    args = ap.parse_args(argv)
    count = build(args.out, args.deck_name, args.assets, args.limit)
    print(f"Wrote {args.out} ({count} notes, model '{DICTATION_MODEL_NAME}')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
