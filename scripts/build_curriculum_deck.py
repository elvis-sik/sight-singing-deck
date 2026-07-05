#!/usr/bin/env python3
"""Build the full function-first sight-singing curriculum .apkg.

Generates every curriculum stage (major and minor tracks), realizes each melody,
renders its audio, and emits one Anki note per melody. Each note yields a Sing
card and a Transcribe (dictation) card; notes are filed into a per-stage subdeck
under a per-track subdeck so the curriculum order is visible in Anki's deck list.

v1 realizes the major track in C major and the minor track in A minor (the
relative minor — both notate on the natural, white-key staff), all treble clef.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
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
from sight_singing.curriculum.stages import (
    INTERVAL_STAGES,
    MAJOR_STAGES,
    MINOR_STAGES,
    Stage,
)


@dataclass(frozen=True)
class Track:
    key: str  # subdeck label + tag, e.g. "Major"
    stages: list[Stage]
    key_name: str  # tonic letter, e.g. "C" / "A"
    mode: str  # default realization mode
    deck_id_base: int  # per-stage deck ids start here


TRACKS = [
    Track("Major", MAJOR_STAGES, "C", "major", DECK_ID + 100),
    Track("Minor", MINOR_STAGES, "A", "natural_minor", DECK_ID + 200),
    Track("Intervals", INTERVAL_STAGES, "C", "major", DECK_ID + 300),
]


def _deck_name(base: str, track: str, index: int, stage_id: str, title: str) -> str:
    # Zero-padded index keeps Anki's alphabetical deck sort in curriculum order.
    return f"{base}::{track}::{index:02d} {stage_id} · {title}"


def _track_library(track: Track) -> list[dict[str, object]]:
    return build_library(track.stages, key_name=track.key_name, mode=track.mode)


def build(out_path: Path, base_deck_name: str, assets_dir: Path, limit: int | None) -> int:
    # Build every track's library first so audio renders once for the whole set.
    track_libraries: list[tuple[Track, list[dict[str, object]]]] = []
    for track in TRACKS:
        lib = _track_library(track)
        if limit is not None:
            lib = lib[:limit]
        track_libraries.append((track, lib))

    full_library = [rec for _, lib in track_libraries for rec in lib]
    print(f"Rendering audio for {len(full_library)} melodies …", flush=True)
    build_library_audio(assets_dir, full_library)

    model = make_model()
    ordered_decks: list[genanki.Deck] = []

    for track, lib in track_libraries:
        order = {s.id: i for i, s in enumerate(track.stages)}
        decks: dict[str, genanki.Deck] = {}
        for record in lib:
            stage_id = str(record["stage_id"])
            if stage_id not in decks:
                index = order.get(stage_id, 99)
                name = _deck_name(
                    base_deck_name, track.key, index, stage_id, str(record["title"])
                )
                decks[stage_id] = genanki.Deck(
                    deck_id=track.deck_id_base + index, name=name
                )
            fields = melody_to_card_fields(record)
            tags = record["tags"]
            assert isinstance(tags, list)
            note = genanki.Note(
                model=model,
                fields=[fields[f] for f in FIELD_NAMES],
                tags=[str(t) for t in tags] + [f"track::{track.key.lower()}"],
            )
            decks[stage_id].add_note(note)
        ordered_decks.extend(decks[s.id] for s in track.stages if s.id in decks)

    pkg = genanki.Package(ordered_decks)

    expected = library_audio_basenames(full_library)
    media_files: list[str] = []
    for bn in expected:
        clip = assets_dir / bn
        if not clip.is_file():
            raise FileNotFoundError(f"Missing generated audio {clip}")
        media_files.append(str(clip))
    pkg.media_files = media_files

    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_package(pkg, out_path)
    return len(full_library)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build the full sight-singing curriculum deck.")
    ap.add_argument("--out", type=Path, default=_ROOT / "out" / "sight-singing-curriculum.apkg")
    ap.add_argument("--deck-name", default="Sight Singing")
    ap.add_argument("--assets", type=Path, default=_ROOT / "assets")
    ap.add_argument(
        "--limit", type=int, default=None,
        help="Only build the first N melodies per track (fast smoke build).",
    )
    args = ap.parse_args(argv)
    count = build(args.out, args.deck_name, args.assets, args.limit)
    print(f"Wrote {args.out} ({count} melodies, model '{MODEL_NAME}')")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
