#!/usr/bin/env python3
"""Build a deck of integration variants for the transcription card."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

import genanki

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sight_singing.audio_assets import CADENCE_FILENAME, build_all_audio, melody_clip_filename
from sight_singing.card_data import melody_to_card_fields
from sight_singing.melodies import MELODIES


DECK_ID = 2_948_817_301
FIELD_NAMES = [
    "Title",
    "VariantID",
    "MelodyJSON",
    "MelodyID",
    "CadenceAudioFile",
    "MelodyAudioFile",
]

BASE_CSS = """
.card {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  font-size: 18px;
  text-align: center;
  color: #18181b;
  background: #fafaf9;
}
.ss-wrap { max-width: 560px; margin: 0 auto; padding: 8px 4px; }
.ss-btn {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  font-size: 14px;
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid rgba(0,0,0,0.15);
  background: #f4f4f5;
  color: #18181b;
  cursor: pointer;
}
.ss-controls { display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0; justify-content: center; }
.ss-transcribe-editor {
  position: relative;
  max-width: 520px;
  height: 176px;
  margin: 16px auto 10px;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 12px;
  background: linear-gradient(180deg, #fff 0%, #fafaf9 100%);
  overflow: hidden;
}
.ss-transcribe-editor.ss-readonly {
  background: linear-gradient(180deg, #fafafa 0%, #f5f5f4 100%);
}
.ss-transcribe-staff-line,
.ss-transcribe-bar-line,
.ss-transcribe-slot-guide,
.ss-transcribe-ledger {
  position: absolute;
  background: rgba(39,39,42,0.72);
}
.ss-transcribe-staff-line { left: 36px; right: 18px; height: 1px; }
.ss-transcribe-bar-line { width: 2px; top: 28px; height: 64px; }
.ss-transcribe-slot-guide {
  top: 24px;
  bottom: 24px;
  width: 1px;
  background: rgba(113,113,122,0.16);
}
.ss-transcribe-slot-guide-beat { background: rgba(113,113,122,0.35); }
.ss-transcribe-slot-index {
  position: absolute;
  bottom: 8px;
  transform: translateX(-50%);
  font-size: 12px;
  color: #71717a;
}
.ss-transcribe-hit {
  position: absolute;
  top: 18px;
  bottom: 28px;
  border: none;
  background: transparent;
  padding: 0;
  margin: 0;
  outline: none;
  cursor: pointer;
}
.ss-transcribe-hit:active { background: rgba(24,24,27,0.05); }
.ss-transcribe-event-span {
  position: absolute;
  top: 122px;
  height: 6px;
  border-radius: 999px;
  background: rgba(24,24,27,0.18);
}
.ss-transcribe-event-rest { background: rgba(87,83,78,0.18); }
.ss-transcribe-duration-tag {
  position: absolute;
  top: 132px;
  transform: translateX(-50%);
  font-size: 11px;
  color: #78716c;
}
.ss-transcribe-note {
  position: absolute;
  width: 15px;
  height: 11px;
  margin-left: -8px;
  margin-top: -6px;
  border-radius: 50%;
  background: #18181b;
  transform: rotate(-18deg);
}
.ss-transcribe-note-h,
.ss-transcribe-note-w {
  background: #fff;
  border: 2px solid #18181b;
  box-sizing: border-box;
}
.ss-transcribe-note-w::after { display: none; }
.ss-transcribe-note-8::before {
  content: "";
  position: absolute;
  right: -2px;
  top: -23px;
  width: 9px;
  height: 9px;
  border-top: 2px solid #18181b;
  border-right: 2px solid #18181b;
  border-radius: 0 8px 0 0;
  transform: rotate(18deg);
}
.ss-transcribe-note::after {
  content: "";
  position: absolute;
  right: 1px;
  top: -26px;
  width: 2px;
  height: 27px;
  background: #18181b;
  border-radius: 1px;
  transform: rotate(18deg);
  transform-origin: bottom right;
}
.ss-transcribe-rest {
  position: absolute;
  transform: translateX(-50%);
}
.ss-transcribe-rest-q,
.ss-transcribe-rest-8 {
  top: 62px;
  width: 22px;
  height: 26px;
  border-radius: 10px;
  background: rgba(68,64,60,0.09);
  border: 1px solid rgba(68,64,60,0.28);
}
.ss-transcribe-rest-q::before,
.ss-transcribe-rest-8::before {
  content: "R";
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #44403c;
}
.ss-transcribe-rest-8::after {
  content: "8";
  position: absolute;
  right: 3px;
  top: 2px;
  font-size: 9px;
  color: #57534e;
}
.ss-transcribe-rest-h,
.ss-transcribe-rest-w {
  width: 18px;
  height: 8px;
  background: #18181b;
}
.ss-transcribe-rest-h { top: 60px; }
.ss-transcribe-rest-w { top: 68px; }
.ss-transcribe-toolbar {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin: 12px 0;
  flex-wrap: wrap;
}
.ss-transcribe-toolbar-compact .ss-btn {
  min-width: 74px;
  padding: 8px 10px;
}
.ss-tool-active {
  background: #18181b;
  color: #fafaf9;
  border-color: #18181b;
}
.ss-transcribe-summary {
  text-align: center;
  font-size: 15px;
  color: #44403c;
  margin-top: 8px;
}
.ss-transcribe-summary strong { color: #18181b; }
.ss-transcribe-proto {
  text-align: center;
  color: #71717a;
  font-size: 13px;
  margin-top: 8px;
}
.debug-title { font-size: 22px; font-weight: 700; margin: 8px 0 2px; }
.debug-subtitle { font-size: 13px; color: #57534e; margin-bottom: 12px; }
""".strip()


def _audio_script(mode: str, add_buttons: bool) -> str:
    lines = [
        "<script>",
        'window.sightSingingCadenceFile = "{{text:CadenceAudioFile}}";',
        'window.sightSingingMelodyFile = "{{text:MelodyAudioFile}}";',
        "window.sightSingingAutoplayFront = [",
    ]
    if mode == "autoplay":
        lines.extend(['  "cadence",', '  "melody",'])
    lines.extend(["];", "window.sightSingingAutoplayBack = [];"])
    if mode in {"functions", "autoplay"}:
        lines.extend(
            [
                "if (window.Audio != undefined) {",
                "  var sightSingingCurrentAudio = null;",
                "  var sightSingingAutoplayToken = 0;",
                "  function sightSingingFileForKey(key) {",
                '    switch (key) { case "cadence": return window.sightSingingCadenceFile; case "melody": return window.sightSingingMelodyFile; default: return ""; }',
                "  }",
                "  function stopSightSingingAudio() {",
                "    sightSingingAutoplayToken += 1;",
                "    if (!sightSingingCurrentAudio) return;",
                "    try { sightSingingCurrentAudio.onended = null; sightSingingCurrentAudio.pause(); sightSingingCurrentAudio.currentTime = 0; } catch (e) {}",
                "    sightSingingCurrentAudio = null;",
                "  }",
                "  function playSightSingingKey(key) {",
                "    var file = String(sightSingingFileForKey(key) || '').trim();",
                "    if (!file) return false;",
                "    stopSightSingingAudio();",
                "    sightSingingCurrentAudio = new Audio(file);",
                "    try { var pr = sightSingingCurrentAudio.play(); if (pr && pr.catch) pr.catch(function () {}); } catch (e) {}",
                "    return false;",
                "  }",
                "  function playCadence() { return playSightSingingKey('cadence'); }",
                "  function playMelody() { return playSightSingingKey('melody'); }",
                "  function playSightSingingSequence(keys) {",
                "    var list = Array.isArray(keys) ? keys.filter(Boolean) : [];",
                "    if (!list.length) return false;",
                "    stopSightSingingAudio();",
                "    var token = sightSingingAutoplayToken;",
                "    function playAt(index) {",
                "      if (token !== sightSingingAutoplayToken) return;",
                "      if (index >= list.length) return;",
                "      var file = String(sightSingingFileForKey(list[index]) || '').trim();",
                "      if (!file) { playAt(index + 1); return; }",
                "      sightSingingCurrentAudio = new Audio(file);",
                "      sightSingingCurrentAudio.onended = function () { setTimeout(function () { playAt(index + 1); }, 120); };",
                "      try { var pr = sightSingingCurrentAudio.play(); if (pr && pr.catch) pr.catch(function () {}); } catch (e) {}",
                "    }",
                "    playAt(0);",
                "    return false;",
                "  }",
            ]
        )
        if mode == "autoplay":
            lines.append(
                "  setTimeout(function () { playSightSingingSequence(window.sightSingingAutoplayFront); }, 0);"
            )
        lines.append("}")
    lines.append("</script>")
    if add_buttons:
        lines.extend(
            [
                '<div class="ss-controls">',
                '  <button type="button" class="ss-btn" onclick="return playCadence();">Cadence</button>',
                '  <button type="button" class="ss-btn" onclick="return playMelody();">Melody</button>',
                "</div>",
            ]
        )
    return "\n".join(lines)


def _transcribe_markup() -> str:
    return """
<div id="melody-data" style="display:none;">{{MelodyJSON}}</div>
<div id="transcribe-editor" class="ss-transcribe-editor"></div>
<div class="ss-transcribe-toolbar">
  <button type="button" id="transcribe-tool-note" data-transcribe-tool="note" class="ss-btn ss-tool-active">Notes</button>
  <button type="button" id="transcribe-tool-rest" data-transcribe-tool="rest" class="ss-btn">Rests</button>
  <button type="button" id="transcribe-tool-erase" data-transcribe-tool="erase" class="ss-btn">Erase</button>
  <button type="button" id="transcribe-reset" class="ss-btn">Reset</button>
</div>
<div class="ss-transcribe-toolbar ss-transcribe-toolbar-compact">
  <button type="button" id="transcribe-duration-8" data-transcribe-duration="8" class="ss-btn">Eighth</button>
  <button type="button" id="transcribe-duration-q" data-transcribe-duration="q" class="ss-btn ss-tool-active">Quarter</button>
  <button type="button" id="transcribe-duration-h" data-transcribe-duration="h" class="ss-btn">Half</button>
  <button type="button" id="transcribe-duration-w" data-transcribe-duration="w" class="ss-btn">Whole</button>
</div>
<div id="transcribe-status" class="ss-transcribe-summary">Waiting for init...</div>
<p class="ss-transcribe-proto">Use this card only to test whether duration selection sticks in Anki.</p>
""".strip()


def _front_template(
    title: str,
    subtitle: str,
    include_renderer: bool,
    audio_mode: str | None,
    add_audio_buttons: bool,
    *,
    renderer_js_name: str,
    transcription_js_name: str,
) -> str:
    parts = [
        '<div class="ss-wrap">',
        f'<div class="debug-title">{title}</div>',
        f'<div class="debug-subtitle">{subtitle}</div>',
        _transcribe_markup(),
    ]
    if audio_mode:
        parts.append(_audio_script(audio_mode, add_audio_buttons))
    if include_renderer:
        parts.append(f'<script src="{renderer_js_name}"></script>')
    parts.append(f'<script src="{transcription_js_name}"></script>')
    parts.append("</div>")
    return "\n".join(parts)


def _back_template() -> str:
    return """
<div id="back">{{FrontSide}}</div>
<hr>
<div class="ss-wrap">
  <div class="debug-subtitle">Report whether the duration highlight changes and whether the placed symbol uses that duration.</div>
  <div class="debug-subtitle">{{VariantID}}</div>
</div>
""".strip()


def make_model(model_id: int, name: str, front: str) -> genanki.Model:
    return genanki.Model(
        model_id=model_id,
        name=name,
        fields=[{"name": n} for n in FIELD_NAMES],
        templates=[{"name": "Card 1", "qfmt": front, "afmt": _back_template()}],
        css=BASE_CSS,
    )


def build(out_path: Path) -> None:
    assets_dir = ROOT / "assets"
    build_all_audio(assets_dir)
    renderer_debug_name = "_renderer_intdebug_v1.js"
    transcription_debug_name = "_transcription_intdebug_v1.js"

    melody_fields = melody_to_card_fields(MELODIES[1])
    variants = [
        (
            2_948_817_311,
            "Transcription Integration - Renderer Only",
            "Variant A: Renderer + Transcription",
            "Current transcription UI plus renderer, but no audio script.",
            True,
            None,
            False,
        ),
        (
            2_948_817_312,
            "Transcription Integration - Audio Globals",
            "Variant B: Audio Globals + Renderer",
            "Adds the audio globals, but not the playback/autoplay functions.",
            True,
            "globals",
            False,
        ),
        (
            2_948_817_313,
            "Transcription Integration - Audio Functions",
            "Variant C: Audio Functions + Renderer",
            "Adds the full audio function block, but no autoplay and no audio buttons.",
            True,
            "functions",
            False,
        ),
        (
            2_948_817_314,
            "Transcription Integration - Audio Buttons",
            "Variant D: Audio Buttons + Renderer",
            "Adds audio functions plus the manual cadence/melody buttons.",
            True,
            "functions",
            True,
        ),
        (
            2_948_817_315,
            "Transcription Integration - Autoplay",
            "Variant E: Autoplay + Renderer",
            "Adds the full autoplay sequence on load, no manual audio buttons.",
            True,
            "autoplay",
            False,
        ),
        (
            2_948_817_316,
            "Transcription Integration - Exact Front",
            "Variant F: Near-Exact Real Front",
            "Closest copy of the real transcription front: renderer, autoplay, and audio buttons together.",
            True,
            "autoplay",
            True,
        ),
    ]

    deck = genanki.Deck(deck_id=DECK_ID, name="Transcription Integration Variants")
    for model_id, model_name, title, subtitle, include_renderer, audio_mode, add_audio_buttons in variants:
        front = _front_template(
            title,
            subtitle,
            include_renderer=include_renderer,
            audio_mode=audio_mode,
            add_audio_buttons=add_audio_buttons,
            renderer_js_name=renderer_debug_name,
            transcription_js_name=transcription_debug_name,
        )
        model = make_model(model_id, model_name, front)
        note = genanki.Note(
            model=model,
            fields=[
                title,
                model_name,
                melody_fields["MelodyJSON"],
                melody_fields["MelodyID"],
                CADENCE_FILENAME,
                melody_clip_filename(str(MELODIES[1]["id"])),
            ],
            tags=["transcription_debug", "integration_variant"],
        )
        deck.add_note(note)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ss-intdebug-media-") as tmp:
        tmp_dir = Path(tmp)
        renderer_copy = tmp_dir / renderer_debug_name
        transcription_copy = tmp_dir / transcription_debug_name
        shutil.copyfile(assets_dir / "_renderer.js", renderer_copy)
        shutil.copyfile(assets_dir / "_transcription.js", transcription_copy)

        pkg = genanki.Package(deck)
        pkg.media_files = [
            str(renderer_copy),
            str(transcription_copy),
            str(assets_dir / CADENCE_FILENAME),
            str(assets_dir / melody_clip_filename(str(MELODIES[1]["id"]))),
        ]
        pkg.write_to_file(str(out_path))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build transcription integration debug deck.")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "out" / "transcription-integration-variants.apkg",
    )
    args = parser.parse_args(argv)
    build(args.out)
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
