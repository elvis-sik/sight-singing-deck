#!/usr/bin/env python3
"""Re-apply the Dictation deck to the LIVE collection (delete → reimport → template).

The Dictation deck was restructured (140 flat → 340 across Major/Minor/Intervals)
AND its Dictate template gained the range/clef editor. An .apkg import does not
overwrite an existing model's templates, so this: (1) snapshots, (2) deletes the
old Dictation deck+cards, (3) importPackage the new apkg, (4) pushes the updated
Dictate template to whichever model the imported cards use, (5) verifies.

Requires Anki running with AnkiConnect. Dry-run by default.

  python scripts/apply_dictation_deck_live.py --check
  python scripts/apply_dictation_deck_live.py --apply
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from sight_singing.anki_model import (  # noqa: E402
    DICTATION_BACK_TEMPLATE,
    DICTATION_FRONT_TEMPLATE,
)

APKG = _ROOT / "out" / "dictation-curriculum.apkg"
SNAP_DIR = _ROOT / "out" / "snapshots"
EDITOR_MARKER = "buildPitches"  # present only in the range/clef editor


def ac(action: str, **params: object) -> object:
    req = urllib.request.Request(
        "http://localhost:8765",
        data=json.dumps({"action": action, "version": 6, "params": params}).encode(),
        headers={"Content-Type": "application/json"},
    )
    payload = json.load(urllib.request.urlopen(req, timeout=180))
    if payload.get("error"):
        raise RuntimeError(f"AnkiConnect {action} failed: {payload['error']}")
    return payload["result"]


def _count(query: str) -> int:
    cards = ac("findCards", query=query)
    assert isinstance(cards, list)
    return len(cards)


def _dictation_model() -> str | None:
    notes = ac("findNotes", query='deck:"Dictation"')
    assert isinstance(notes, list)
    if not notes:
        return None
    info = ac("notesInfo", notes=notes[:1])
    assert isinstance(info, list)
    return str(info[0]["modelName"])


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Re-apply the Dictation deck live.")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    if not APKG.is_file():
        print(f"ERROR: {APKG} not found — build it first.")
        return 1

    before = _count('deck:"Dictation"')
    model_before = _dictation_model()
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    if model_before:
        tpl = ac("modelTemplates", modelName=model_before)
        (SNAP_DIR / f"dictation-model-{stamp}-before.json").write_text(
            json.dumps(tpl, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    print(f"live Dictation cards now: {before} (model {model_before})")
    print(f"new apkg: {APKG} ({APKG.stat().st_size // 1024 // 1024} MB)")

    if not args.apply:
        print("\nDRY RUN — will delete the Dictation deck, reimport, and push the "
              "range/clef Dictate template. Re-run with --apply.")
        return 0

    ac("deleteDecks", decks=["Dictation"], cardsToo=True)
    ac("importPackage", path=str(APKG.resolve()))
    model = _dictation_model()
    assert model, "no Dictation cards after import"
    ac(
        "updateModelTemplates",
        model={
            "name": model,
            "templates": {
                "Dictate": {
                    "Front": DICTATION_FRONT_TEMPLATE,
                    "Back": DICTATION_BACK_TEMPLATE,
                }
            },
        },
    )

    after = _count('deck:"Dictation"')
    front = ac("modelTemplates", modelName=model)["Dictate"]["Front"]  # type: ignore[index]
    ok = after >= 300 and EDITOR_MARKER in front
    print(f"\nAPPLIED. Dictation cards: {before} → {after} (model {model}); "
          f"range/clef editor present: {EDITOR_MARKER in front}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
