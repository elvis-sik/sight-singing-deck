#!/usr/bin/env python3
"""Push a note type's template(s) to the LIVE Anki collection via AnkiConnect.

Used to propagate a template-only change (e.g. the multi-bar transcription editor,
which is inlined into the Transcribe template) to cards already in the collection,
without re-importing or touching notes/scheduling. Templates are model-level, so
`updateModelTemplates` re-renders every existing card of that model immediately.

Safety: snapshots the current live templates to a timestamped JSON first, asserts
the expected before/after marker strings, and re-reads to confirm the change
landed. Requires Anki running with AnkiConnect (localhost:8765).

  # dry run — snapshot + show the diff markers, change nothing:
  python scripts/apply_live_template_update.py --model '<name>' --check
  # apply:
  python scripts/apply_live_template_update.py --model '<name>' --apply

See [[ankiconnect-live-deck-update]].
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
    TRANSCRIBE_BACK_TEMPLATE,
    TRANSCRIBE_FRONT_TEMPLATE,
)

ANKICONNECT = "http://localhost:8765"
SNAP_DIR = _ROOT / "out" / "snapshots"

# The Transcribe template is the only one that embeds _transcription.js, so it is
# the only one the multi-bar editor change touches. Marker strings prove the
# before (single-bar) and after (multi-bar) state without diffing 600 KB blobs.
NEW_TEMPLATES = {
    "Transcribe": {"Front": TRANSCRIBE_FRONT_TEMPLATE, "Back": TRANSCRIBE_BACK_TEMPLATE}
}
AFTER_MARKER = "capacityForData"  # present only in the multi-bar editor
BEFORE_MARKER = "cursor === BAR_UNITS"  # the old single-bar gate


def ac(action: str, **params: object) -> object:
    req = urllib.request.Request(
        ANKICONNECT,
        data=json.dumps({"action": action, "version": 6, "params": params}).encode(),
        headers={"Content-Type": "application/json"},
    )
    payload = json.load(urllib.request.urlopen(req, timeout=20))
    if payload.get("error"):
        raise RuntimeError(f"AnkiConnect {action} failed: {payload['error']}")
    return payload["result"]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Push template(s) to the live collection.")
    ap.add_argument("--model", required=True, help="Exact live note-type name.")
    ap.add_argument("--apply", action="store_true", help="Actually push (else dry run).")
    ap.add_argument("--check", action="store_true", help="Dry run (default).")
    args = ap.parse_args(argv)

    names = ac("modelNames")
    assert isinstance(names, list)
    if args.model not in names:
        print(f"ERROR: model {args.model!r} not found in the live collection.")
        return 1

    current = ac("modelTemplates", modelName=args.model)
    assert isinstance(current, dict)
    if "Transcribe" not in current:
        print(f"ERROR: model {args.model!r} has no 'Transcribe' template.")
        return 1

    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    snap = SNAP_DIR / f"{args.model.replace(' ', '_')}-{stamp}-before.json"
    snap.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")

    before_front = current["Transcribe"]["Front"]
    has_before = BEFORE_MARKER in before_front
    has_after_already = AFTER_MARKER in before_front
    print(f"model: {args.model}")
    print(f"snapshot: {snap}")
    print(f"  live Transcribe currently single-bar ({BEFORE_MARKER!r}): {has_before}")
    print(f"  live Transcribe already multi-bar ({AFTER_MARKER!r}):     {has_after_already}")
    print(f"  new template is multi-bar: {AFTER_MARKER in TRANSCRIBE_FRONT_TEMPLATE}")

    if not args.apply:
        print("\nDRY RUN — no changes made. Re-run with --apply to push.")
        return 0

    ac("updateModelTemplates", model={"name": args.model, "templates": NEW_TEMPLATES})

    after = ac("modelTemplates", modelName=args.model)
    assert isinstance(after, dict)
    after_front = after["Transcribe"]["Front"]
    ok = AFTER_MARKER in after_front and BEFORE_MARKER not in after_front
    print(f"\nAPPLIED. live Transcribe now multi-bar: {AFTER_MARKER in after_front}; "
          f"old gate gone: {BEFORE_MARKER not in after_front}")
    if not ok:
        print("WARNING: post-update markers unexpected — inspect the model.")
        return 1
    print("Verified. Existing Transcribe cards now use the multi-bar editor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
