#!/usr/bin/env python3
"""Render the real card templates to HTML fixtures for the WebKit tests.

The WebKit injection emulation (`debug/anki-inject-emulation.html`) needs the
exact HTML Anki produces for each card side. Generating it from the live
templates keeps the fixtures from drifting; the WebKit Playwright config runs
this in globalSetup before the suite.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from sight_singing.anki_model import (  # noqa: E402
    BACK_TEMPLATE,
    FRONT_TEMPLATE,
    TRANSCRIBE_BACK_TEMPLATE,
    TRANSCRIBE_FRONT_TEMPLATE,
)
from sight_singing.card_data import melody_to_card_fields  # noqa: E402
from sight_singing.melodies import MELODIES  # noqa: E402


def _fill(template: str, fields: dict[str, str]) -> str:
    out = template
    for key, value in fields.items():
        out = out.replace("{{%s}}" % key, value)
        out = out.replace("{{text:%s}}" % key, value)
    for token in ("{{#MelodyAudioFile}}", "{{/MelodyAudioFile}}"):
        out = out.replace(token, "")
    return out


def main() -> int:
    fields = melody_to_card_fields(MELODIES[3])  # eighth-note arch, mixed rhythm
    out_dir = _ROOT / "debug" / "_fixtures"
    out_dir.mkdir(parents=True, exist_ok=True)

    sing_front = _fill(FRONT_TEMPLATE, fields)
    sing_back = _fill(BACK_TEMPLATE, fields).replace("{{FrontSide}}", sing_front)
    transcribe_front = _fill(TRANSCRIBE_FRONT_TEMPLATE, fields)
    transcribe_back = _fill(TRANSCRIBE_BACK_TEMPLATE, fields).replace(
        "{{FrontSide}}", transcribe_front
    )

    (out_dir / "sing-front.html").write_text(sing_front, encoding="utf-8")
    (out_dir / "sing-back.html").write_text(sing_back, encoding="utf-8")
    (out_dir / "transcribe-front.html").write_text(transcribe_front, encoding="utf-8")
    (out_dir / "transcribe-back.html").write_text(transcribe_back, encoding="utf-8")
    print(f"Wrote card fixtures to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
