"""Anki note type (genanki) for sight-singing MVP cards."""

from __future__ import annotations

from pathlib import Path

import genanki

# Stable IDs for this deck (change if you fork a separate published deck).
DECK_ID = 2_948_817_001
MODEL_ID = 2_948_817_015
MODEL_NAME = "Sight Singing (MVP v18 engraved editor)"

VEXFLOW_ASSET_NAME = "_vexflow_ss_v1.js"
RENDERER_ASSET_NAME = "_renderer_ss_v3.js"
TRANSCRIPTION_ASSET_NAME = "_transcription_ss_v6.js"

_CSS_PATH = Path(__file__).resolve().parents[2] / "assets" / "card_styles.css"

FIELD_NAMES = [
    "MelodyJSON",
    "StageID",
    "MelodyID",
    "CadenceAudio",
    "FirstNoteAudio",
    "TonicAudio",
    "MelodyAudio",
    "CadenceAudioFile",
    "FirstNoteAudioFile",
    "TonicAudioFile",
    "MelodyAudioFile",
]


def model_css() -> str:
    return _CSS_PATH.read_text(encoding="utf-8").strip()


# Shared audio playback runtime. Inline (not a media file) so playback works
# even before external media scripts load. Uses only `var`/function statements
# because Anki re-evaluates card scripts on both sides.
AUDIO_SCRIPT = """
<script>if (window.Audio == undefined) document.body.className += " no-audio"</script>
<script>
if (window.Audio != undefined) {
  var sightSingingCurrentAudio = null;
  var sightSingingAutoplayToken = 0;

  function sightSingingFileForKey(key) {
    switch (key) {
      case "cadence":
        return window.sightSingingCadenceFile;
      case "first":
        return window.sightSingingFirstNoteFile;
      case "tonic":
        return window.sightSingingTonicFile;
      case "melody":
        return window.sightSingingMelodyFile;
      default:
        return "";
    }
  }

  function stopSightSingingAudio() {
    sightSingingAutoplayToken += 1;
    if (!sightSingingCurrentAudio) return;
    try {
      sightSingingCurrentAudio.onended = null;
      sightSingingCurrentAudio.pause();
      sightSingingCurrentAudio.currentTime = 0;
    } catch (e) {}
    sightSingingCurrentAudio = null;
  }

  function playSightSingingFile(file) {
    file = String(file || "").trim();
    if (!file) return false;
    stopSightSingingAudio();
    sightSingingCurrentAudio = new Audio(file);
    try {
      var pr = sightSingingCurrentAudio.play();
      if (pr !== undefined && pr.then) {
        pr.catch(function () {});
      }
    } catch (e) {}
    return false;
  }

  function playSightSingingKey(key) {
    return playSightSingingFile(sightSingingFileForKey(key));
  }

  function playSightSingingSequence(keys) {
    var list = Array.isArray(keys) ? keys.filter(Boolean) : [];
    if (!list.length) return false;

    stopSightSingingAudio();
    var token = sightSingingAutoplayToken;

    function playAt(index) {
      if (token !== sightSingingAutoplayToken) return;
      if (index >= list.length) return;

      var file = sightSingingFileForKey(list[index]);
      file = String(file || "").trim();
      if (!file) {
        playAt(index + 1);
        return;
      }

      sightSingingCurrentAudio = new Audio(file);
      sightSingingCurrentAudio.onended = function () {
        setTimeout(function () {
          playAt(index + 1);
        }, 120);
      };

      try {
        var pr = sightSingingCurrentAudio.play();
        if (pr !== undefined && pr.then) {
          pr.catch(function () {});
        }
      } catch (e) {}
    }

    playAt(0);
    return false;
  }

  function playCadence() {
    return playSightSingingKey("cadence");
  }

  function playFirstNote() {
    return playSightSingingKey("first");
  }

  function playTonic() {
    return playSightSingingKey("tonic");
  }

  function playMelody() {
    return playSightSingingKey("melody");
  }

  (function () {
    var isBack = !!document.getElementById("back");
    var sequence = isBack
      ? window.sightSingingAutoplayBack
      : window.sightSingingAutoplayFront;
    setTimeout(function () {
      playSightSingingSequence(sequence);
    }, 0);
  })();
}
</script>
""".strip()

# Small inline SVG icons for the audio buttons.
ICON_PLAY = (
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.1 L18.6 12 L8 18.9 Z"/></svg>'
)
ICON_CHORD = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<rect x="4" y="10" width="3" height="9" rx="1.2"/>'
    '<rect x="10.5" y="6.5" width="3" height="12.5" rx="1.2"/>'
    '<rect x="17" y="3" width="3" height="16" rx="1.2"/></svg>'
)
ICON_NOTE = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<ellipse cx="9" cy="17.5" rx="4.4" ry="3.2" transform="rotate(-16 9 17.5)"/>'
    '<rect x="12.4" y="3.5" width="1.8" height="14.5" rx="0.9"/>'
    '<path d="M14.2 3.5 C 18 6.2, 18.8 9.8, 16.2 13.4 C 17.8 9.4, 16 7.6, 14.2 7.2 Z"/></svg>'
)
ICON_FORK = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M8 3 L10 3 L10 10 C 10 11.2, 11 12, 12 12 C 13 12, 14 11.2, 14 10 L14 3 L16 3 L16 10 '
    'C 16 12, 14.6 13.6, 13 13.9 L13 19 L15.5 19 L15.5 21 L8.5 21 L8.5 19 L11 19 L11 13.9 '
    'C 9.4 13.6, 8 12, 8 10 Z"/></svg>'
)

FRONT_TEMPLATE = """
{{#MelodyAudioFile}}
<script>
window.sightSingingCadenceFile = "{{text:CadenceAudioFile}}";
window.sightSingingFirstNoteFile = "{{text:FirstNoteAudioFile}}";
window.sightSingingTonicFile = "{{text:TonicAudioFile}}";
window.sightSingingMelodyFile = "{{text:MelodyAudioFile}}";
</script>
{{/MelodyAudioFile}}
<script>
/*
  Audio clue configuration — edit these lists to taste.
  Available keys: "cadence", "first", "tonic", "melody".
  Front plays before you sing; Back plays after the answer is shown.
  The buttons under the staff work regardless of this setting.
*/
window.sightSingingAutoplayFront = [
  "tonic",
];
window.sightSingingAutoplayBack = [
  "melody",
];
</script>
<!--
WARNING:
The template below this point should not refer to rendered [sound:...] fields.
This avoids autoplay and keeps the card empty if no filename field is present.
-->
__AUDIO_SCRIPT__

<div class="ss-wrap">
<div id="melody-data" style="display:none;">{{MelodyJSON}}</div>
<div class="ss-meta" id="melody-meta" data-ss-badge="Sing"></div>
<div class="ss-panel">
  <div id="notation" class="ss-notation"></div>
</div>
<div class="ss-controls ss-if-audio">
  <button type="button" class="ss-btn" onclick="return playCadence();">__ICON_CHORD__<span>Cadence</span></button>
  <button type="button" class="ss-btn" onclick="return playFirstNote();">__ICON_NOTE__<span>First note</span></button>
  <button type="button" class="ss-btn" onclick="return playTonic();">__ICON_FORK__<span>Tonic</span></button>
</div>
<p class="ss-prompt">Sing this melody.</p>
</div>
<script src="__VEXFLOW__"></script>
<script src="__RENDERER__"></script>
""".strip()

BACK_TEMPLATE = """
<div id="back">{{FrontSide}}</div>
<hr id="answer" class="ss-hr">
<div class="ss-wrap">
<div id="answer-info"></div>
<div class="ss-controls ss-if-audio">
  <button type="button" class="ss-btn" onclick="return playMelody();">__ICON_PLAY__<span>Play melody</span></button>
</div>
</div>
<script>SightSingingRedraw && SightSingingRedraw();</script>
""".strip()

TRANSCRIBE_FRONT_TEMPLATE = """
{{#MelodyAudioFile}}
<script>
window.sightSingingMelodyId = "{{text:MelodyID}}";
window.sightSingingCadenceFile = "{{text:CadenceAudioFile}}";
window.sightSingingFirstNoteFile = "{{text:FirstNoteAudioFile}}";
window.sightSingingTonicFile = "{{text:TonicAudioFile}}";
window.sightSingingMelodyFile = "{{text:MelodyAudioFile}}";
</script>
{{/MelodyAudioFile}}
<script>
/*
  Audio clue configuration — edit these lists to taste.
  Available keys: "cadence", "first", "tonic", "melody".
  The buttons under the editor work regardless of this setting.
*/
window.sightSingingAutoplayFront = [
  "tonic",
  "melody",
];
window.sightSingingAutoplayBack = [
  "melody",
];
</script>
<!--
WARNING:
The template below this point should not refer to rendered [sound:...] fields.
This avoids autoplay and keeps the card empty if no filename field is present.
-->
__AUDIO_SCRIPT__

<div class="ss-wrap">
<div id="melody-data" style="display:none;">{{MelodyJSON}}</div>
<div class="ss-meta" id="melody-meta" data-ss-badge="Transcribe"></div>
<div class="ss-panel ss-editor-panel">
  <div id="transcribe-editor"></div>
</div>
<div id="transcribe-ui"></div>
<div class="ss-controls ss-if-audio ss-transcribe-front-audio">
  <button type="button" class="ss-btn" onclick="return playCadence();">__ICON_CHORD__<span>Cadence</span></button>
  <button type="button" class="ss-btn" onclick="return playMelody();">__ICON_PLAY__<span>Replay melody</span></button>
</div>
<p class="ss-prompt ss-prompt-transcribe">Write down the melody you hear.</p>
</div>
<script src="__VEXFLOW__"></script>
<script src="__RENDERER__"></script>
<script src="__TRANSCRIPTION__"></script>
""".strip()

TRANSCRIBE_BACK_TEMPLATE = """
<div id="back">{{FrontSide}}</div>
<hr id="answer" class="ss-hr">
<div class="ss-wrap">
<div id="transcribe-result" class="ss-verdict ss-verdict-none"></div>
<div id="transcribe-user-block">
  <div class="ss-compare-label">Your transcription</div>
  <div class="ss-panel">
    <div id="transcribe-user" class="ss-notation"></div>
  </div>
  <div id="transcribe-legend" class="ss-legend">
    <span class="ss-legend-dot ss-legend-dot-good"></span>matches
    <span class="ss-legend-dot ss-legend-dot-bad"></span>different
  </div>
</div>
<div class="ss-compare-label">Target melody</div>
<div class="ss-panel">
  <div id="transcribe-target" class="ss-notation"></div>
</div>
<div class="ss-controls ss-if-audio">
  <button type="button" class="ss-btn" onclick="return playMelody();">__ICON_PLAY__<span>Play melody</span></button>
</div>
</div>
<script>
if (window.SightSingingTranscriptionReview) {
  window.SightSingingTranscriptionReview();
}
</script>
""".strip()


def _fill(template: str) -> str:
    return (
        template.replace("__AUDIO_SCRIPT__", AUDIO_SCRIPT)
        .replace("__ICON_PLAY__", ICON_PLAY)
        .replace("__ICON_CHORD__", ICON_CHORD)
        .replace("__ICON_NOTE__", ICON_NOTE)
        .replace("__ICON_FORK__", ICON_FORK)
        .replace("__VEXFLOW__", VEXFLOW_ASSET_NAME)
        .replace("__RENDERER__", RENDERER_ASSET_NAME)
        .replace("__TRANSCRIPTION__", TRANSCRIPTION_ASSET_NAME)
    )


FRONT_TEMPLATE = _fill(FRONT_TEMPLATE)
BACK_TEMPLATE = _fill(BACK_TEMPLATE)
TRANSCRIBE_FRONT_TEMPLATE = _fill(TRANSCRIBE_FRONT_TEMPLATE)
TRANSCRIBE_BACK_TEMPLATE = _fill(TRANSCRIBE_BACK_TEMPLATE)


def make_model() -> genanki.Model:
    return genanki.Model(
        model_id=MODEL_ID,
        name=MODEL_NAME,
        fields=[{"name": n} for n in FIELD_NAMES],
        templates=[
            {
                "name": "Sing",
                "qfmt": FRONT_TEMPLATE,
                "afmt": BACK_TEMPLATE,
            },
            {
                "name": "Transcribe",
                "qfmt": TRANSCRIBE_FRONT_TEMPLATE,
                "afmt": TRANSCRIBE_BACK_TEMPLATE,
            },
        ],
        css=model_css(),
    )
