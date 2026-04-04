#!/usr/bin/env python3
"""Build the sight-singing MVP .apkg."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `python scripts/build_deck.py` without install
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import genanki

from sight_singing.anki_model import DECK_ID, FIELD_NAMES, make_model
from sight_singing.card_data import melody_to_card_fields
from sight_singing.melodies import MELODIES


def media_paths(assets_dir: Path) -> list[str]:
    names = ["_vexflow.js", "_player.js", "_renderer.js"]
    out: list[str] = []
    for n in names:
        p = assets_dir / n
        if not p.is_file():
            raise FileNotFoundError(f"Missing asset: {p}")
        out.append(str(p))
    return out


def build(out_path: Path, deck_name: str, assets_dir: Path) -> None:
    model = make_model()
    deck = genanki.Deck(deck_id=DECK_ID, name=deck_name)

    for melody in MELODIES:
        fields = melody_to_card_fields(melody)
        note = genanki.Note(
            model=model,
            fields=[fields[f] for f in FIELD_NAMES],
            tags=["sight_singing", "mvp", "stage1", "treble", "C_major"],
        )
        deck.add_note(note)

    pkg = genanki.Package(deck)
    pkg.media_files = media_paths(assets_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pkg.write_to_file(str(out_path))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build sight-singing MVP Anki deck.")
    ap.add_argument("--out", type=Path, default=_ROOT / "out" / "sight-singing-mvp.apkg")
    ap.add_argument("--deck-name", default="Sight Singing MVP")
    ap.add_argument(
        "--assets",
        type=Path,
        default=_ROOT / "assets",
        help="Directory containing _vexflow.js, _player.js, _renderer.js",
    )
    args = ap.parse_args(argv)
    build(args.out, args.deck_name, args.assets)
    print(f"Wrote {args.out} ({len(MELODIES)} notes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
