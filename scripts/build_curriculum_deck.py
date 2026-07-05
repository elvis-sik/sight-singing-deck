#!/usr/bin/env python3
"""Build the full function-first sight-singing curriculum .apkg.

Generates every curriculum stage, realizes each melody (C major / treble for
v1), renders its audio, and emits one Anki note per melody. Each note yields a
Sing card and a Transcribe (dictation) card; notes are filed into a per-stage
subdeck so the curriculum order is visible in Anki's deck list.
"""

from __future__ import annotations

import argparse
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
from sight_singing.anki_model import DECK_ID, FIELD_NAMES, MODEL_NAME, make_model
from sight_singing.audio_assets import build_library_audio, library_audio_basenames
from sight_singing.build.library import build_library
from sight_singing.card_data import melody_to_card_fields
from sight_singing.curriculum.stages import MAJOR_STAGES


def _stage_order() -> dict[str, int]:
    return {stage.id: i for i, stage in enumerate(MAJOR_STAGES)}


def _deck_name(base: str, index: int, stage_id: str, title: str) -> str:
    # Zero-padded index keeps Anki's alphabetical deck sort in curriculum order.
    return f"{base}::{index:02d} {stage_id} · {title}"


def build(out_path: Path, base_deck_name: str, assets_dir: Path, limit: int | None) -> int:
    library = build_library()
    if limit is not None:
        library = library[:limit]

    print(f"Rendering audio for {len(library)} melodies …", flush=True)
    build_library_audio(assets_dir, library)

    model = make_model()
    order = _stage_order()
    decks: dict[str, genanki.Deck] = {}

    for record in library:
        stage_id = str(record["stage_id"])
        if stage_id not in decks:
            index = order.get(stage_id, 99)
            name = _deck_name(base_deck_name, index, stage_id, str(record["title"]))
            # Stable, unique per-stage deck id.
            deck_id = DECK_ID + 1 + index
            decks[stage_id] = genanki.Deck(deck_id=deck_id, name=name)

        fields = melody_to_card_fields(record)
        tags = record["tags"]
        assert isinstance(tags, list)
        note = genanki.Note(
            model=model,
            fields=[fields[f] for f in FIELD_NAMES],
            tags=[str(t) for t in tags],
        )
        decks[stage_id].add_note(note)

    ordered_decks = [decks[s.id] for s in MAJOR_STAGES if s.id in decks]
    pkg = genanki.Package(ordered_decks)

    expected = library_audio_basenames(library)
    media_files: list[str] = []
    for bn in expected:
        clip = assets_dir / bn
        if not clip.is_file():
            raise FileNotFoundError(f"Missing generated audio {clip}")
        media_files.append(str(clip))
    pkg.media_files = media_files

    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_package(pkg, out_path)
    return len(library)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build the full sight-singing curriculum deck.")
    ap.add_argument("--out", type=Path, default=_ROOT / "out" / "sight-singing-curriculum.apkg")
    ap.add_argument("--deck-name", default="Sight Singing")
    ap.add_argument("--assets", type=Path, default=_ROOT / "assets")
    ap.add_argument(
        "--limit", type=int, default=None,
        help="Only build the first N melodies (fast smoke build).",
    )
    args = ap.parse_args(argv)
    count = build(args.out, args.deck_name, args.assets, args.limit)
    print(f"Wrote {args.out} ({count} melodies, model '{MODEL_NAME}')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
