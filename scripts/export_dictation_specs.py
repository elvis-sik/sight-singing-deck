#!/usr/bin/env python3
"""Emit the dictation ladder as machine-readable JSON.

Two artifacts under out/:

  dictation_specs.json      — the constraint spec for every stage (the generator's
                              input, serialised): pool / start / end / step bounds /
                              length / count / rule flags. This is the reviewable,
                              tool-consumable form of the ladder.
  dictation_exercises.json  — the CURATED output: what each spec actually generates,
                              as diatonic-index sequences plus movable-do solfège, so
                              the resulting exercises can be eyeballed and hand-curated
                              without running Python.

Run:  python scripts/export_dictation_specs.py
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from sight_singing.curriculum.stages import (
    DICTATION_PRIMING_SINGLETONS,
    DICTATION_STAGES,
)
from sight_singing.generate.melody_gen import generate_stage

OUT = Path(__file__).resolve().parents[1] / "out"

# Movable-do solfège by diatonic index. Indices repeat every 7; a trailing comma
# marks the octave below the tonic, a prime marks the octave above.
_SYLL = ["do", "re", "mi", "fa", "so", "la", "ti"]


def solfege(index: int) -> str:
    syll = _SYLL[index % 7]
    octave = index // 7
    if octave > 0:
        return syll + "'" * octave
    if octave < 0:
        return syll + "," * -octave
    return syll


def solfege_seq(mel: tuple[int, ...]) -> str:
    return "-".join(solfege(n) for n in mel)


def spec_dict(stage) -> dict:  # noqa: ANN001 - Stage is a local dataclass
    d = dataclasses.asdict(stage)
    # tuples -> lists for JSON; drop the free-text hint fields' noise-free.
    return {k: (list(v) if isinstance(v, tuple) else v) for k, v in d.items()}


def main() -> None:
    OUT.mkdir(exist_ok=True)

    specs = {
        "priming_singletons": {
            "id": "DP0",
            "title": "Tonic Echo",
            "note": "Single-degree identification against an established tonic; a "
                    "fixed set (a lone note is not a generatable melody).",
            "degrees": [list(m) for m in DICTATION_PRIMING_SINGLETONS],
            "solfege": [solfege_seq(m) for m in DICTATION_PRIMING_SINGLETONS],
        },
        "stages": [spec_dict(s) for s in DICTATION_STAGES],
    }
    (OUT / "dictation_specs.json").write_text(
        json.dumps(specs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    exercises: dict[str, dict[str, object]] = {
        "DP0": {
            "title": "Tonic Echo",
            "exercises": [
                {"degrees": list(m), "solfege": solfege_seq(m)}
                for m in DICTATION_PRIMING_SINGLETONS
            ],
        }
    }
    for stage in DICTATION_STAGES:
        mels = generate_stage(stage)
        exercises[stage.id] = {
            "title": stage.title,
            "length": stage.length,
            "count_target": stage.count,
            "count_generated": len(mels),
            "exercises": [
                {"degrees": list(m), "solfege": solfege_seq(m)} for m in mels
            ],
        }
    (OUT / "dictation_exercises.json").write_text(
        json.dumps(exercises, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    total = sum(len(generate_stage(s)) for s in DICTATION_STAGES)
    print(f"Wrote {OUT/'dictation_specs.json'}")
    print(f"Wrote {OUT/'dictation_exercises.json'}")
    print(f"{len(DICTATION_STAGES)} stages, {total} generated exercises "
          f"(+ {len(DICTATION_PRIMING_SINGLETONS)} priming singletons)")


if __name__ == "__main__":
    main()
