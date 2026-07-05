"""Tiny apkg exercising all THREE note types (Sing/Transcribe, Error, Rhythm).

Purpose-built so a disposable-Anki deck smoke — which only renders the first N
cards — actually covers the Error and Rhythm templates (in the full curriculum
they sit after ~1500 melodic cards, out of the render window). Not shipped.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))

import genanki  # noqa: E402

from build_deck import write_package  # noqa: E402
from sight_singing.anki_model import (  # noqa: E402
    ERROR_FIELD_NAMES,
    FIELD_NAMES,
    make_error_model,
    make_model,
    make_rhythm_model,
)
from sight_singing.audio_assets import (  # noqa: E402
    build_library_audio,
    library_audio_basenames,
)
from sight_singing.build.library import (  # noqa: E402
    build_error_library,
    build_library,
    build_rhythm_library,
    error_audio_entries,
)
from sight_singing.card_data import error_to_card_fields, melody_to_card_fields  # noqa: E402
from sight_singing.curriculum.stages import MAJOR_STAGES, STAGES_BY_ID  # noqa: E402

OUT = _ROOT / "out" / "notetype-smoke.apkg"
ASSETS = _ROOT / "assets"


def main() -> int:
    sing_lib = build_library(MAJOR_STAGES[:1])[:2]
    err_lib = build_error_library([STAGES_BY_ID["M5"]], per_stage=2)
    rhy_lib = build_rhythm_library("treble")[:2]

    audio = sing_lib + error_audio_entries(err_lib) + rhy_lib
    build_library_audio(ASSETS, audio)

    sing_model, err_model, rhy_model = make_model(), make_error_model(), make_rhythm_model()
    deck = genanki.Deck(2_948_817_099, "Note-Type Smoke")

    for mel in sing_lib:
        f = melody_to_card_fields(mel)
        deck.add_note(genanki.Note(model=sing_model, fields=[f[n] for n in FIELD_NAMES]))
    for rec in err_lib:
        written, variants = rec["written"], rec["variants"]
        assert isinstance(written, dict)
        assert isinstance(variants, list)
        f = error_to_card_fields(written, variants)
        deck.add_note(genanki.Note(model=err_model, fields=[f[n] for n in ERROR_FIELD_NAMES]))
    for mel in rhy_lib:
        f = melody_to_card_fields(mel)
        deck.add_note(genanki.Note(model=rhy_model, fields=[f[n] for n in FIELD_NAMES]))

    pkg = genanki.Package(deck)
    media = []
    for bn in library_audio_basenames(audio):
        clip = ASSETS / bn
        if not clip.is_file():
            raise FileNotFoundError(f"Missing generated audio {clip}")
        media.append(str(clip))
    pkg.media_files = media

    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_package(pkg, OUT)
    print(f"Wrote {OUT} ({len(deck.notes)} notes across 3 note types)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
