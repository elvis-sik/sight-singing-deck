"""Generate file-backed piano MP3 clips for Anki."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any

from sight_singing.midi_writer import TICKS_PER_QUARTER, write_midi
from sight_singing.melodies import MELODIES
from sight_singing.theory.scales import (
    key as make_key,
)
from sight_singing.theory.scales import (
    midi_from_name,
    note_name,
    parse_note_name,
    realize_note,
    tonic_octave_for,
)

ROOT = Path(__file__).resolve().parents[2]
PCM_SAMPLE_RATE = 44_100
MP3_BITRATE = 64_000
PIANO_PROGRAM = 0
# Tonic-drone patch: an organ sustains cleanly for the whole clip, unlike the
# piano (which decays), so the held tonal centre stays audible while singing.
DRONE_PROGRAM = 16  # Drawbar Organ (General MIDI)
FLUID_GAIN = "0.3"
TRIM_SILENCE_THRESHOLD = 96
TRIM_PAD_SEC = 0.12

QUARTER_SEC = 0.52
MELODY_NOTE_RATIO = 0.90
SINGLE_NOTE_DUR = 0.72
CADENCE_STEP = 0.70
CADENCE_NOTE_RATIO = 0.92
DRONE_DUR = 6.0  # seconds of sustained tonic (doubled at the octave below)

DURATION_BEATS = {
    "8": 0.5,
    "q": 1.0,
    "h": 2.0,
    "w": 4.0,
}

NOTE_TO_MIDI = {
    "C4": 60,
    "D4": 62,
    "E4": 64,
    "F4": 65,
    "G4": 67,
    "A4": 69,
    "B4": 71,
    "C5": 72,
    "D5": 74,
}

PITCH_NAMES = ["C4", "D4", "E4", "F4", "G4", "A4"]
MVP_TONICS = ["C4"]  # tonic(s) that get a sustained drone clip in the MVP deck

# Anki's .apkg importer never overwrites an existing media file that has the
# same name, so clip filenames must change whenever their audible content
# does. Every clip name therefore embeds a hash of its musical content and
# the render parameters. Bump AUDIO_RENDER_VERSION for changes the hash
# inputs cannot see (e.g. a different soundfont policy).
AUDIO_RENDER_VERSION = 2


def _clip_hash(payload: Any) -> str:
    blob = json.dumps(
        {
            "version": AUDIO_RENDER_VERSION,
            "payload": payload,
            "render": {
                "sample_rate": PCM_SAMPLE_RATE,
                "bitrate": MP3_BITRATE,
                "program": PIANO_PROGRAM,
                "gain": FLUID_GAIN,
                "trim": [TRIM_SILENCE_THRESHOLD, TRIM_PAD_SEC],
            },
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:10]


def cadence_chords_for(
    key_name: str, mode: str, clef: str = "treble"
) -> list[list[str]]:
    """A I-IV-V-I (major) / i-iv-V-i (minor) cadence in the given key/clef.

    Minor cadences realize in harmonic minor, so the dominant (V) is a major
    triad with the raised leading tone — a real authentic cadence that lands the
    ear on the minor tonic, not the relative major. Root-position triads on
    scale degrees 1, 4, 5, 1, in the melody's tonic octave for that clef.
    """
    cad_mode = "harmonic_minor" if mode in ("natural_minor", "harmonic_minor") else "major"
    k = make_key(key_name, cad_mode)
    tonic_octave = tonic_octave_for(k, clef)
    chords: list[list[str]] = []
    for root in (0, 3, 4, 0):  # I/i, IV/iv, V, I/i
        chords.append([realize_note(k, tonic_octave, root + off)[0] for off in (0, 2, 4)])
    return chords


def cadence_filename_for(key_name: str, mode: str, clef: str = "treble") -> str:
    chords = cadence_chords_for(key_name, mode, clef)
    digest = _clip_hash(
        {
            "kind": "cadence",
            "chords": chords,
            "step": CADENCE_STEP,
            "ratio": CADENCE_NOTE_RATIO,
            "program": PIANO_PROGRAM,
        }
    )
    safe = key_name.replace("#", "s")
    tag = "maj" if mode == "major" else "min"
    return f"_cadence_{safe}{tag}_{clef}_{digest}.mp3"


# MVP / default cadence (C major, treble). card_data resolves per-card cadences
# via cadence_filename_for, so this stays consistent with the generated tracks.
CADENCE_CHORDS = cadence_chords_for("C", "major", "treble")
CADENCE_FILENAME = cadence_filename_for("C", "major", "treble")


def _tool_path(env_var: str, binary: str, fallback: Path) -> Path:
    configured = os.environ.get(env_var)
    if configured:
        return Path(configured)
    found = shutil.which(binary)
    if found:
        return Path(found)
    return fallback


def _soundfont_path() -> Path:
    configured = os.environ.get("SOUNDFONT_PATH")
    if configured:
        return Path(configured)
    candidates = [
        ROOT / ".render-assets" / "GeneralUser-GS.sf2",
        Path("/usr/share/sounds/sf2/FluidR3_GM.sf2"),
        Path("/usr/share/sounds/sf2/TimGM6mb.sf2"),
        Path("/usr/share/soundfonts/FluidR3_GM.sf2"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def _melody_by_id(melody_id: str) -> dict[str, Any]:
    for melody in MELODIES:
        if str(melody["id"]) == melody_id:
            return melody
    raise KeyError(f"Unknown melody id: {melody_id}")


def melody_clip_notes_durations(melody: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Normalized (notes, durations) exactly as the renderer receives them."""
    notes_raw = melody["notes"]
    if not isinstance(notes_raw, list):
        raise TypeError(f"melody {melody['id']}: notes must be a list")
    durations_raw = melody.get("durations", ["q"] * len(notes_raw))
    if not isinstance(durations_raw, list):
        raise TypeError(f"melody {melody['id']}: durations must be a list")
    notes = [str(item) for item in notes_raw]
    durations = [str(item) for item in durations_raw]
    return notes, durations


def melody_clip_filename_for(
    melody_id: str, notes: list[str], durations: list[str]
) -> str:
    """Content-hashed melody clip name from explicit notes/durations.

    Use this for generated melodies (not in the hardcoded MELODIES list).
    """
    notes = [str(n) for n in notes]
    durations = [str(d) for d in durations]
    digest = _clip_hash(
        {
            "kind": "melody",
            "notes": notes,
            "durations": durations,
            "quarter_sec": QUARTER_SEC,
            "ratio": MELODY_NOTE_RATIO,
        }
    )
    return f"_m_{melody_id}_{digest}.mp3"


def melody_clip_filename(melody_id: str) -> str:
    notes, durations = melody_clip_notes_durations(_melody_by_id(melody_id))
    return melody_clip_filename_for(melody_id, notes, durations)


def note_clip_filename(note_name: str) -> str:
    safe = note_name.replace("#", "s")
    digest = _clip_hash(
        {
            "kind": "note",
            "pitch": str(note_name),
            "duration_sec": SINGLE_NOTE_DUR,
        }
    )
    return f"_n_{safe}_{digest}.mp3"


def drone_clip_filename(tonic_name: str) -> str:
    """Sustained-tonic drone clip name (organ, doubled at the octave below)."""
    safe = tonic_name.replace("#", "s")
    digest = _clip_hash(
        {
            "kind": "drone",
            "pitch": str(tonic_name),
            "duration_sec": DRONE_DUR,
            "program": DRONE_PROGRAM,
        }
    )
    return f"_d_{safe}_{digest}.mp3"


def _drone_pitches(tonic_name: str) -> list[str]:
    """The tonic plus the same pitch an octave below, for a fuller drone."""
    letter, acc, octave = parse_note_name(tonic_name)
    lower = note_name(letter, acc, octave - 1)
    return [tonic_name, lower]


def _build_drone_clip(temp_dir: Path, tonic_name: str) -> tuple[Path, Path]:
    safe = tonic_name.replace("#", "s")
    midi_path = temp_dir / f"drone_{safe}.mid"
    wav_path = temp_dir / f"drone_{safe}.wav"
    duration_ticks = _seconds_to_ticks(DRONE_DUR, QUARTER_SEC)
    note_events = [
        _note_event(pitch, start_tick=0, duration_ticks=duration_ticks, velocity=78)
        for pitch in _drone_pitches(tonic_name)
    ]
    _write_clip_midi(
        midi_path,
        quarter_seconds=QUARTER_SEC,
        note_events=note_events,
        program=DRONE_PROGRAM,
    )
    return midi_path, wav_path


def _seconds_to_ticks(seconds: float, quarter_seconds: float) -> int:
    return max(1, round((seconds / quarter_seconds) * TICKS_PER_QUARTER))


def _microseconds_per_quarter(quarter_seconds: float) -> int:
    return round(quarter_seconds * 1_000_000)


def _note_event(
    pitch_name: str,
    *,
    start_tick: int,
    duration_ticks: int,
    velocity: int = 96,
) -> dict[str, int]:
    pitch = NOTE_TO_MIDI.get(pitch_name)
    if pitch is None:
        # Any pitch (arbitrary key/octave) — compute MIDI from the note name.
        from sight_singing.theory.scales import midi_from_name

        pitch = midi_from_name(pitch_name)
    return {
        "pitch": pitch,
        "start_tick": start_tick,
        "duration_ticks": duration_ticks,
        "velocity": velocity,
    }


def _write_clip_midi(
    midi_path: Path,
    *,
    quarter_seconds: float,
    note_events: list[dict[str, int]],
    program: int = PIANO_PROGRAM,
) -> None:
    write_midi(
        midi_path,
        microseconds_per_quarter=_microseconds_per_quarter(quarter_seconds),
        notes=note_events,
        program=program,
    )


def _encode_mp3(src_pcm: Path, dest_mp3: Path) -> None:
    lame_bin = _tool_path("LAME_BIN", "lame", Path("/opt/homebrew/bin/lame"))
    subprocess.run(
        [
            str(lame_bin),
            "--silent",
            "-m",
            "m",
            "-b",
            str(MP3_BITRATE // 1000),
            str(src_pcm),
            str(dest_mp3),
        ],
        check=True,
    )


def _render_wav_with_fluidsynth(midi_path: Path, wav_path: Path) -> None:
    fluidsynth_bin = _tool_path(
        "FLUIDSYNTH_BIN",
        "fluidsynth",
        Path("/opt/homebrew/bin/fluidsynth"),
    )
    subprocess.run(
        [
            str(fluidsynth_bin),
            "-ni",
            "-q",
            "-R",
            "0",
            "-C",
            "0",
            "-g",
            FLUID_GAIN,
            "-F",
            str(wav_path),
            "-T",
            "wav",
            "-r",
            str(PCM_SAMPLE_RATE),
            str(_soundfont_path()),
            str(midi_path),
        ],
        check=True,
    )


def _trim_rendered_wav(wav_path: Path) -> None:
    with wave.open(str(wav_path), "rb") as reader:
        params = reader.getparams()
        if params.sampwidth != 2:
            return
        frame_rate = params.framerate
        channels = params.nchannels
        frames = reader.readframes(params.nframes)

    samples = memoryview(frames).cast("h")
    last_non_silent_frame = -1
    for frame_index in range(params.nframes - 1, -1, -1):
        start = frame_index * channels
        frame_peak = max(abs(samples[start + channel]) for channel in range(channels))
        if frame_peak > TRIM_SILENCE_THRESHOLD:
            last_non_silent_frame = frame_index
            break

    if last_non_silent_frame < 0:
        return

    pad_frames = int(frame_rate * TRIM_PAD_SEC)
    keep_frames = min(params.nframes, last_non_silent_frame + 1 + pad_frames)
    if keep_frames >= params.nframes:
        return

    trimmed = frames[: keep_frames * channels * params.sampwidth]
    with wave.open(str(wav_path), "wb") as writer:
        writer.setparams(params)
        writer.writeframes(trimmed)


def _build_note_clip(temp_dir: Path, note_name: str) -> tuple[Path, Path]:
    midi_path = temp_dir / f"{note_name}.mid"
    wav_path = temp_dir / f"{note_name}.wav"
    duration_ticks = _seconds_to_ticks(SINGLE_NOTE_DUR, QUARTER_SEC)
    _write_clip_midi(
        midi_path,
        quarter_seconds=QUARTER_SEC,
        note_events=[
            _note_event(
                note_name,
                start_tick=0,
                duration_ticks=duration_ticks,
                velocity=100,
            )
        ],
    )
    return midi_path, wav_path


def _build_cadence_clip(
    temp_dir: Path, chords: list[list[str]] | None = None, stem: str = "cadence"
) -> tuple[Path, Path]:
    chords = CADENCE_CHORDS if chords is None else chords
    midi_path = temp_dir / f"{stem}.mid"
    wav_path = temp_dir / f"{stem}.wav"
    note_duration_ticks = _seconds_to_ticks(CADENCE_STEP * CADENCE_NOTE_RATIO, CADENCE_STEP)
    note_events: list[dict[str, int]] = []
    for chord_index, chord in enumerate(chords):
        start_tick = chord_index * TICKS_PER_QUARTER
        velocity = 92 if chord_index < 3 else 98
        for pitch_name in chord:
            note_events.append(
                _note_event(
                    pitch_name,
                    start_tick=start_tick,
                    duration_ticks=note_duration_ticks,
                    velocity=velocity,
                )
            )
    _write_clip_midi(
        midi_path,
        quarter_seconds=CADENCE_STEP,
        note_events=note_events,
    )
    return midi_path, wav_path


def _build_melody_clip(
    temp_dir: Path,
    melody_id: str,
    notes: list[str],
    durations: list[str],
) -> tuple[Path, Path]:
    midi_path = temp_dir / f"{melody_id}.mid"
    wav_path = temp_dir / f"{melody_id}.wav"
    beat_cursor = 0.0
    note_events = []
    for pitch_name, duration_name in zip(notes, durations):
        beats = DURATION_BEATS.get(str(duration_name), 1.0)
        start_tick = round(beat_cursor * TICKS_PER_QUARTER)
        duration_ticks = max(
            1,
            round(beats * TICKS_PER_QUARTER * MELODY_NOTE_RATIO),
        )
        if pitch_name not in (None, "rest"):
            note_events.append(
                _note_event(
                    str(pitch_name),
                    start_tick=start_tick,
                    duration_ticks=duration_ticks,
                    velocity=96,
                )
            )
        beat_cursor += beats
    _write_clip_midi(
        midi_path,
        quarter_seconds=QUARTER_SEC,
        note_events=note_events,
    )
    return midi_path, wav_path


def build_all_audio(assets_dir: Path) -> list[Path]:
    """Write MP3s under assets_dir; return paths in stable order for packaging."""
    out: list[Path] = []
    assets_dir.mkdir(parents=True, exist_ok=True)

    fluidsynth_bin = _tool_path(
        "FLUIDSYNTH_BIN",
        "fluidsynth",
        Path("/opt/homebrew/bin/fluidsynth"),
    )
    lame_bin = _tool_path("LAME_BIN", "lame", Path("/opt/homebrew/bin/lame"))
    soundfont = _soundfont_path()
    if not fluidsynth_bin.is_file():
        raise FileNotFoundError(f"Missing FluidSynth binary: {fluidsynth_bin}")
    if not lame_bin.is_file():
        raise FileNotFoundError(f"Missing LAME binary: {lame_bin}")
    if not soundfont.is_file():
        raise FileNotFoundError(f"Missing soundfont: {soundfont}")

    with tempfile.TemporaryDirectory(prefix="ss-piano-render-") as tmp:
        temp_dir = Path(tmp)
        render_targets: list[tuple[Path, Path, Path]] = []

        cadence_midi, cadence_wav = _build_cadence_clip(temp_dir)
        render_targets.append((cadence_midi, cadence_wav, assets_dir / CADENCE_FILENAME))

        for pitch_name in PITCH_NAMES:
            midi_path, wav_path = _build_note_clip(temp_dir, pitch_name)
            render_targets.append(
                (midi_path, wav_path, assets_dir / note_clip_filename(pitch_name))
            )

        for tonic_name in MVP_TONICS:
            midi_path, wav_path = _build_drone_clip(temp_dir, tonic_name)
            render_targets.append(
                (midi_path, wav_path, assets_dir / drone_clip_filename(tonic_name))
            )

        for melody in MELODIES:
            melody_id = str(melody["id"])
            notes, durations = melody_clip_notes_durations(melody)
            midi_path, wav_path = _build_melody_clip(
                temp_dir,
                melody_id,
                notes,
                durations,
            )
            render_targets.append((midi_path, wav_path, assets_dir / melody_clip_filename(melody_id)))

        for midi_path, wav_path, dest_path in render_targets:
            _render_wav_with_fluidsynth(midi_path, wav_path)
            _trim_rendered_wav(wav_path)
            _encode_mp3(wav_path, dest_path)
            out.append(dest_path)

    return out


def media_audio_basenames() -> list[str]:
    """Basenames expected in the apkg (for validation)."""
    names = [CADENCE_FILENAME]
    for pn in PITCH_NAMES:
        names.append(note_clip_filename(pn))
    for tonic_name in MVP_TONICS:
        names.append(drone_clip_filename(tonic_name))
    for melody in MELODIES:
        names.append(melody_clip_filename(str(melody["id"])))
    return names


def library_note_pitches(library: list[dict[str, Any]]) -> list[str]:
    """Distinct sounded pitches across the library plus every tonic (sorted)."""
    pitches: set[str] = set()
    for mel in library:
        for note in mel["notes"]:
            if note not in (None, "rest"):
                pitches.add(str(note))
        tonic = mel.get("tonic")
        if tonic:
            pitches.add(str(tonic))
    return sorted(pitches, key=midi_from_name)


def library_tonics(library: list[dict[str, Any]]) -> list[str]:
    """Distinct tonic pitches across the library (for drone clips), sorted."""
    tonics = {str(mel["tonic"]) for mel in library if mel.get("tonic")}
    return sorted(tonics, key=midi_from_name)


def library_cadences(library: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    """Distinct (key, mode, clef) contexts needing their own cadence clip."""
    seen: set[tuple[str, str, str]] = set()
    for mel in library:
        seen.add(
            (
                str(mel.get("key", "C")),
                str(mel.get("mode", "major")),
                str(mel.get("clef", "treble")),
            )
        )
    return sorted(seen)


def library_audio_basenames(library: list[dict[str, Any]]) -> list[str]:
    """Every audio basename an arbitrary generated library needs."""
    names = [CADENCE_FILENAME]
    for key_name, mode, clef in library_cadences(library):
        names.append(cadence_filename_for(key_name, mode, clef))
    for pitch in library_note_pitches(library):
        names.append(note_clip_filename(pitch))
    for tonic in library_tonics(library):
        names.append(drone_clip_filename(tonic))
    for mel in library:
        names.append(
            melody_clip_filename_for(
                str(mel["id"]),
                [str(n) for n in mel["notes"]],
                [str(d) for d in mel["durations"]],
            )
        )
    # Dedup while preserving order (two melodies can share a clip).
    seen: set[str] = set()
    out: list[str] = []
    for name in names:
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def build_library_audio(assets_dir: Path, library: list[dict[str, Any]]) -> list[Path]:
    """Render every clip an arbitrary generated melody library needs.

    Renders the shared C-major cadence, one note clip per distinct sounded
    pitch (covering first-note and tonic clues), and one clip per melody.
    Melody clips are deduplicated by content hash, so identical melodies in
    different keys/stages render once.
    """
    assets_dir.mkdir(parents=True, exist_ok=True)
    _require_render_tools()

    with tempfile.TemporaryDirectory(prefix="ss-piano-render-") as tmp:
        temp_dir = Path(tmp)
        render_targets: dict[str, tuple[Path, Path]] = {}

        for key_name, mode, clef in library_cadences(library):
            dest = cadence_filename_for(key_name, mode, clef)
            if dest not in render_targets:
                render_targets[dest] = _build_cadence_clip(
                    temp_dir, cadence_chords_for(key_name, mode, clef), dest[:-4]
                )

        for pitch in library_note_pitches(library):
            dest = note_clip_filename(pitch)
            if dest not in render_targets:
                render_targets[dest] = _build_note_clip(temp_dir, pitch)

        for tonic in library_tonics(library):
            dest = drone_clip_filename(tonic)
            if dest not in render_targets:
                render_targets[dest] = _build_drone_clip(temp_dir, tonic)

        for mel in library:
            notes = [str(n) for n in mel["notes"]]
            durations = [str(d) for d in mel["durations"]]
            dest = melody_clip_filename_for(str(mel["id"]), notes, durations)
            if dest not in render_targets:
                # Name the temp files by dest stem to avoid collisions across
                # melodies that happen to share an id prefix.
                render_targets[dest] = _build_melody_clip(
                    temp_dir, dest[:-4], notes, durations
                )

        out: list[Path] = []
        for dest_name, (midi_path, wav_path) in render_targets.items():
            _render_wav_with_fluidsynth(midi_path, wav_path)
            _trim_rendered_wav(wav_path)
            dest_path = assets_dir / dest_name
            _encode_mp3(wav_path, dest_path)
            out.append(dest_path)
    return out


def _require_render_tools() -> None:
    fluidsynth_bin = _tool_path(
        "FLUIDSYNTH_BIN", "fluidsynth", Path("/opt/homebrew/bin/fluidsynth")
    )
    lame_bin = _tool_path("LAME_BIN", "lame", Path("/opt/homebrew/bin/lame"))
    soundfont = _soundfont_path()
    if not fluidsynth_bin.is_file():
        raise FileNotFoundError(f"Missing FluidSynth binary: {fluidsynth_bin}")
    if not lame_bin.is_file():
        raise FileNotFoundError(f"Missing LAME binary: {lame_bin}")
    if not soundfont.is_file():
        raise FileNotFoundError(f"Missing soundfont: {soundfont}")
