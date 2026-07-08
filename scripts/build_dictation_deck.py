#!/usr/bin/env python3
"""Build the melodic-dictation .apkg (its own deck tree and note type).

Dictation is a curriculum in its own right (see DICTATION_CURRICULUM.md): ordered
by phrase length + working memory + interval audibility, with its own pool. These
are the PITCH-ONLY, even-rhythm strands, each a track under a top-level
``Dictation`` deck tree:

  1 · Major       — priming floor (DP0-DP2) then DD1-DD9, C major, treble.
  2 · Minor       — NDP0 then ND1-ND9 (natural minor) + the harmonic-minor
                    capstone ND9h (raised 7 si = G#, needs the editor's accidental
                    input), A minor, treble.
  3 · Intervals   — IVD2-IVD8, hear one interval, C major, treble.
  4 · Bass Clef   — a curated spread on the bass staff (C major / A minor).
  5 · Rhythm      — one-bar rhythms on a single pitch, graded by sounded rhythm.
  6 · Other Keys  — a curated spread transferred to G major / F major (reading
                    the key signature), treble.

Each melody is one Dictate card (hear -> notate) carrying per-stage listen-count
thresholds.

Run:  python scripts/build_dictation_deck.py [--limit N]
"""

from __future__ import annotations

import argparse
import json
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
from sight_singing.anki_model import (
    DICTATION_FIELD_NAMES,
    DICTATION_MODEL_NAME,
    make_dictation_model,
)
from sight_singing.audio_assets import build_library_audio, library_audio_basenames
from sight_singing.build.library import (
    build_library,
    build_rhythm_library,
    realize_stage_melody,
)
from sight_singing.card_data import melody_to_card_fields
from sight_singing.curriculum.stages import (
    DICTATION_INTERVAL_STAGES,
    DICTATION_MINOR_HARMONIC_STAGES,
    DICTATION_MINOR_PRIMING_SINGLETONS,
    DICTATION_MINOR_STAGES,
    DICTATION_PRIMING_SINGLETONS,
    DICTATION_STAGES,
    Stage,
)

# Own deck-id range, well clear of the sight-singing tree.
DICT_DECK_BASE = 2_948_817_900

_DICT_ROOT_DESC = (
    "Melodic dictation — hear a short melody, then notate it. Its OWN curriculum, "
    "ordered by phrase length and memory (not vocal difficulty). Work a track top "
    "to bottom: Major first (priming floor, then the ladder), then Minor; the "
    "Intervals track drills one interval at a time. Every card establishes the key "
    "and the melody is replayable; the <b>listen count</b> on the front is your "
    "effort gauge — grade by how many replays it took."
)
_TRACK_DESCS = {
    "1 · Major": "The core dictation ladder in C major. Start here, top to bottom.",
    "2 · Minor": "The same ladder in (la-based) A minor. After Major feels steady.",
    "3 · Intervals": "Hear one interval, notate it — dip in to reinforce a leap.",
    "4 · Bass Clef::C major": "The dictation ladder read/notated on the bass staff.",
    "4 · Bass Clef::A minor": "Bass-clef dictation in A minor. After treble is fluent.",
    "5 · Rhythm": "Hear a one-bar rhythm on one pitch; notate the rhythm (timing only).",
    "6 · Other Keys::G major": "The same material in G major — read the F♯ in the key "
    "signature (tap the F line; it sounds F♯).",
    "6 · Other Keys::F major": "The same material in F major — read the B♭ in the key "
    "signature (tap the B line; it sounds B♭).",
}


def _priming_carrier(stage_id: str, title: str) -> Stage:
    """A length-1 carrier so the fixed single-degree echoes realize normally.

    A lone note isn't a generatable melody, so DP0/NDP0 aren't Stages; this lets
    us push the singletons through realize_stage_melody in any key/mode/clef.
    """
    return Stage(
        stage_id, title, "dictation",
        pool=(0, 2, 4), start_pool=(0, 2, 4), end_pool=(0, 2, 4),
        max_step=4, count=3, length=1,
        notes="Hear the key, identify one pillar degree.",
    )


@dataclass(frozen=True)
class DictTrack:
    segment: str          # subdeck under Dictation, e.g. "1 · Major"
    tag: str              # stable tag slug
    key_name: str
    mode: str
    clef: str
    priming_id: str       # "DP0" / "NDP0" (empty ⇒ no priming rung)
    priming_title: str
    priming_singletons: tuple[tuple[int, ...], ...]
    stages: list[Stage]
    deck_id_base: int
    per_stage: int | None = None  # cap melodies/stage (bounded transfer tracks)
    kind: str = "melodic"          # "melodic" | "rhythm"
    rhythm_ids: tuple[str, ...] = ()  # rhythm-stage ids when kind == "rhythm"


def _pick(stages: list[Stage], ids: tuple[str, ...]) -> list[Stage]:
    by_id = {s.id: s for s in stages}
    return [by_id[i] for i in ids if i in by_id]


# Bounded bass-clef transfer: read/notate the same dictation material on the lower
# staff. A curated spread (triad → steps → upper scale → thirds → 4ths/5ths →
# capstone), capped per stage, in C major and A minor — not the whole ladder again.
_BASS_MAJOR = _pick(DICTATION_STAGES, ("DD1", "DD3", "DD5", "DD6", "DD7", "DD9"))
_BASS_MINOR = _pick(DICTATION_MINOR_STAGES, ("ND1", "ND3", "ND5", "ND6", "ND7", "ND9"))

# Bounded transfer to sharp/flat keys: the SAME curated spread, realized in G major
# (one sharp) and F major (one flat). Diatonic — the key signature supplies the
# accidental, so the student reads it rather than typing it (that is the skill).
_XFER_MAJOR = _pick(DICTATION_STAGES, ("DD1", "DD3", "DD5", "DD6", "DD7", "DD9"))

# The minor track's natural-minor ladder plus the harmonic-minor capstone (ND9h),
# whose si (raised 7 = G#) is now spellable in the editor.
_MINOR_TRACK_STAGES = DICTATION_MINOR_STAGES + DICTATION_MINOR_HARMONIC_STAGES

TRACKS: list[DictTrack] = [
    DictTrack(
        "1 · Major", "dictation_major", "C", "major", "treble",
        "DP0", "Tonic Echo", DICTATION_PRIMING_SINGLETONS, DICTATION_STAGES,
        DICT_DECK_BASE + 10,
    ),
    DictTrack(
        "2 · Minor", "dictation_minor", "A", "natural_minor", "treble",
        "NDP0", "Tonic Echo (minor)", DICTATION_MINOR_PRIMING_SINGLETONS,
        _MINOR_TRACK_STAGES, DICT_DECK_BASE + 40,
    ),
    DictTrack(
        "3 · Intervals", "dictation_intervals", "C", "major", "treble",
        "", "", (), DICTATION_INTERVAL_STAGES, DICT_DECK_BASE + 70,
    ),
    DictTrack(
        "4 · Bass Clef::C major", "dictation_bass_c", "C", "major", "bass",
        "", "", (), _BASS_MAJOR, DICT_DECK_BASE + 100, per_stage=6,
    ),
    DictTrack(
        "4 · Bass Clef::A minor", "dictation_bass_a", "A", "natural_minor", "bass",
        "", "", (), _BASS_MINOR, DICT_DECK_BASE + 130, per_stage=6,
    ),
    # Rhythm dictation: hear a one-bar rhythm on a single pitch, notate the rhythm
    # (graded by sounded rhythm, pitch-agnostic). The full ladder R1-R9: pulse/rests/
    # eighth-pairs/mixed/offbeat, dotted (dot modifier), syncopation (offbeat quarters
    # ≡ tied eighths), triplets (triplet tool on the sextuplet grid), and a mixed
    # capstone.
    DictTrack(
        "5 · Rhythm", "dictation_rhythm", "C", "major", "treble",
        "", "", (), [], DICT_DECK_BASE + 160,
        kind="rhythm",
        rhythm_ids=("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9"),
    ),
    DictTrack(
        "6 · Other Keys::G major", "dictation_key_g", "G", "major", "treble",
        "", "", (), _XFER_MAJOR, DICT_DECK_BASE + 190, per_stage=6,
    ),
    DictTrack(
        "6 · Other Keys::F major", "dictation_key_f", "F", "major", "treble",
        "", "", (), _XFER_MAJOR, DICT_DECK_BASE + 220, per_stage=6,
    ),
]


def _listen_targets(length: int) -> dict[str, int]:
    """Per-stage listen-count thresholds, scaling with phrase length."""
    good = max(1, length - 2)
    hard = max(good + 1, length)
    return {"good": good, "hard": hard}


def _track_stage_order(track: DictTrack) -> list[tuple[str, str, int]]:
    """(stage_id, title, length) in ladder order, priming rung first if present."""
    if track.kind == "rhythm":
        from sight_singing.generate.rhythm import RHYTHM_STAGES_BY_ID
        # length=3 is a listen-count budget proxy, not a note count.
        return [(rid, RHYTHM_STAGES_BY_ID[rid].title, 3) for rid in track.rhythm_ids]
    out: list[tuple[str, str, int]] = []
    if track.priming_id:
        out.append((track.priming_id, track.priming_title, 1))
    out += [(s.id, s.title, s.length) for s in track.stages]
    return out


def _track_records(track: DictTrack) -> list[tuple[str, dict[str, object]]]:
    """(stage_id, realized record) for a whole track."""
    if track.kind == "rhythm":
        return [
            (str(rec["stage_id"]), rec)
            for rec in build_rhythm_library(
                track.clef, stage_ids=track.rhythm_ids, grade_mode="rhythm"
            )
        ]
    records: list[tuple[str, dict[str, object]]] = []
    if track.priming_id:
        carrier = _priming_carrier(track.priming_id, track.priming_title)
        for degrees in track.priming_singletons:
            rec = realize_stage_melody(
                carrier, degrees,
                key_name=track.key_name, mode=track.mode, clef=track.clef,
            )
            records.append((track.priming_id, rec))
    for stage in track.stages:
        lib = build_library(
            [stage], key_name=track.key_name, mode=track.mode, clef=track.clef,
            per_stage=track.per_stage,
        )
        for rec in lib:
            records.append((stage.id, rec))
    return records


def build(out_path: Path, base_deck_name: str, assets_dir: Path, limit: int | None) -> int:
    track_records: list[tuple[DictTrack, list[tuple[str, dict[str, object]]]]] = []
    for track in TRACKS:
        recs = _track_records(track)
        if limit is not None:
            by_stage: dict[str, int] = {}
            trimmed = []
            for sid, rec in recs:
                n = by_stage.get(sid, 0)
                if n < limit:
                    trimmed.append((sid, rec))
                    by_stage[sid] = n + 1
            recs = trimmed
        track_records.append((track, recs))

    audio_library = [rec for _, recs in track_records for _, rec in recs]
    print(f"Rendering audio for {len(audio_library)} dictation melodies …", flush=True)
    build_library_audio(assets_dir, audio_library)

    model = make_dictation_model()
    umbrella = genanki.Deck(
        deck_id=DICT_DECK_BASE, name=base_deck_name, description=_DICT_ROOT_DESC
    )
    ordered_decks: list[genanki.Deck] = [umbrella]

    for off, (track, recs) in enumerate(track_records):
        order = {sid: i for i, (sid, _t, _l) in enumerate(_track_stage_order(track))}
        length_by = {sid: length for sid, _t, length in _track_stage_order(track)}
        title_by = {sid: title for sid, title, _l in _track_stage_order(track)}
        # Per-track umbrella carries its how-to text.
        ordered_decks.append(
            genanki.Deck(
                deck_id=DICT_DECK_BASE + 1 + off,
                name=f"{base_deck_name}::{track.segment}",
                description=_TRACK_DESCS.get(track.segment, ""),
            )
        )
        decks: dict[str, genanki.Deck] = {}
        for sid, rec in recs:
            if sid not in decks:
                idx = order.get(sid, 99)
                name = f"{base_deck_name}::{track.segment}::{idx:02d} {sid} · {title_by.get(sid, sid)}"
                decks[sid] = genanki.Deck(deck_id=track.deck_id_base + idx, name=name)
            fields = melody_to_card_fields(rec)
            fields["ListenTargets"] = json.dumps(
                _listen_targets(length_by.get(sid, 4)), separators=(",", ":")
            )
            tags = rec.get("tags", [])
            assert isinstance(tags, list)
            note = genanki.Note(
                model=model,
                fields=[fields[f] for f in DICTATION_FIELD_NAMES],
                tags=[str(t) for t in tags if not str(t).startswith("track::")]
                + [f"track::{track.tag}"],
            )
            decks[sid].add_note(note)
        ordered_decks.extend(
            decks[sid] for sid, _t, _l in _track_stage_order(track) if sid in decks
        )

    pkg = genanki.Package(ordered_decks)
    media_files: list[str] = []
    for bn in library_audio_basenames(audio_library):
        clip = assets_dir / bn
        if not clip.is_file():
            raise FileNotFoundError(f"Missing generated audio {clip}")
        media_files.append(str(clip))
    pkg.media_files = media_files

    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_package(pkg, out_path)
    return len(audio_library)


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
