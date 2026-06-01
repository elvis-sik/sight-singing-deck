#!/usr/bin/env python3
"""Build the sight-singing MVP .apkg."""

from __future__ import annotations

import argparse
import itertools
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import zipfile
from pathlib import Path

# Allow `python scripts/build_deck.py` without install
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import genanki

from genanki.apkg_col import APKG_COL
from genanki.apkg_schema import APKG_SCHEMA
from sight_singing.anki_model import (
    DECK_ID,
    FIELD_NAMES,
    RENDERER_ASSET_NAME,
    TRANSCRIPTION_ASSET_NAME,
    VEXFLOW_ASSET_NAME,
    make_model,
)
from sight_singing.audio_assets import build_all_audio, media_audio_basenames
from sight_singing.card_data import melody_to_card_fields
from sight_singing.melodies import MELODIES


def build(out_path: Path, deck_name: str, assets_dir: Path) -> None:
    build_all_audio(assets_dir)
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
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ss-deck-media-build-") as tmp:
        tmp_dir = Path(tmp)
        js_sources = [
            ("_vexflow.js", VEXFLOW_ASSET_NAME),
            ("_renderer.js", RENDERER_ASSET_NAME),
            ("_transcription.js", TRANSCRIPTION_ASSET_NAME),
        ]
        media_files: list[str] = []
        for src_name, dest_name in js_sources:
            src_path = assets_dir / src_name
            if not src_path.is_file():
                raise FileNotFoundError(f"Missing asset: {src_path}")
            dest_path = tmp_dir / dest_name
            shutil.copyfile(src_path, dest_path)
            media_files.append(str(dest_path))
        for bn in media_audio_basenames():
            p = assets_dir / bn
            if not p.is_file():
                raise FileNotFoundError(
                    f"Missing generated audio {p}; build_all_audio should create it."
                )
            media_files.append(str(p))
        pkg.media_files = media_files
        write_package(pkg, out_path)


def _disable_autoplay(cursor: sqlite3.Cursor) -> None:
    dconf_json_str, = cursor.execute("SELECT dconf FROM col").fetchone()
    dconf = json.loads(dconf_json_str)
    for conf in dconf.values():
        conf["autoplay"] = False
        conf["replayq"] = True
    cursor.execute("UPDATE col SET dconf = ?", (json.dumps(dconf),))


def write_package(pkg: genanki.Package, out_path: Path) -> None:
    fd, dbfilename = tempfile.mkstemp()
    os.close(fd)
    try:
        conn = sqlite3.connect(dbfilename)
        cursor = conn.cursor()
        timestamp = time.time()
        id_gen = itertools.count(int(timestamp * 1000))
        cursor.executescript(APKG_SCHEMA)
        cursor.executescript(APKG_COL)
        for deck in pkg.decks:
            deck.write_to_db(cursor, timestamp, id_gen)
        _disable_autoplay(cursor)
        conn.commit()
        conn.close()

        with zipfile.ZipFile(out_path, "w") as outzip:
            outzip.write(dbfilename, "collection.anki2")
            media_file_idx_to_path = dict(enumerate(pkg.media_files))
            media_json = {
                idx: os.path.basename(path)
                for idx, path in media_file_idx_to_path.items()
            }
            outzip.writestr("media", json.dumps(media_json))
            for idx, path in media_file_idx_to_path.items():
                outzip.write(path, str(idx))
    finally:
        try:
            os.unlink(dbfilename)
        except FileNotFoundError:
            pass


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Build sight-singing MVP Anki deck.")
    ap.add_argument("--out", type=Path, default=_ROOT / "out" / "sight-singing-mvp.apkg")
    ap.add_argument("--deck-name", default="Sight Singing MVP")
    ap.add_argument(
        "--assets",
        type=Path,
        default=_ROOT / "assets",
        help="Directory for JS, VexFlow bundle, and generated audio clips",
    )
    args = ap.parse_args(argv)
    build(args.out, args.deck_name, args.assets)
    print(f"Wrote {args.out} ({len(MELODIES)} melody notes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
