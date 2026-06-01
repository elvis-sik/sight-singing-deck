"""Anki note type (genanki) for sight-singing MVP cards."""

from __future__ import annotations

import genanki

# Stable IDs for this deck (change if you fork a separate published deck).
DECK_ID = 2_948_817_001
MODEL_ID = 2_948_817_015
MODEL_NAME = "Sight Singing (MVP v14 interval editor)"

VEXFLOW_ASSET_NAME = "_vexflow_ss_v1.js"
RENDERER_ASSET_NAME = "_renderer_ss_v2.js"
TRANSCRIPTION_ASSET_NAME = "_transcription_ss_v2.js"

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

MODEL_CSS = """
.ss-wrap { max-width: 560px; margin: 0 auto; padding: 8px 4px; }
.ss-notation { min-height: 150px; margin: 12px 0; overflow-x: auto; }
.ss-notation svg { display: block; margin: 0 auto; }
.ss-fallback { font-size: 1.4rem; letter-spacing: 0.06em; text-align: center; margin: 24px 0; }
.ss-controls { display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0; justify-content: center; }
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
.ss-btn:active { transform: scale(0.98); }
.ss-prompt { text-align: center; color: #52525b; font-size: 15px; margin-top: 8px; }
.ss-hr { border: none; border-top: 1px solid rgba(0,0,0,0.12); margin: 20px 0; }
.ss-degrees { font-size: 16px; line-height: 1.5; margin-top: 8px; }
.ss-muted { color: #71717a; font-size: 14px; }
.no-audio .ss-if-audio { display: none; }
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
.ss-transcribe-slot-guide-beat {
  background: rgba(113,113,122,0.35);
}
.ss-transcribe-slot-index {
  position: absolute;
  bottom: 8px;
  transform: translateX(-50%);
  font-size: 12px;
  color: #71717a;
}
.ss-transcribe-gap {
  position: absolute;
  top: 102px;
  height: 24px;
  border-radius: 999px;
  border: 1px dashed rgba(113,113,122,0.38);
  background: rgba(244,244,245,0.92);
}
.ss-transcribe-gap-label {
  position: absolute;
  top: 106px;
  transform: translateX(-50%);
  font-size: 11px;
  color: #78716c;
}
.ss-transcribe-hit {
  position: absolute;
  top: 18px;
  bottom: 28px;
  border: none;
  background: rgba(34,197,94,0.07);
  padding: 0;
  margin: 0;
  outline: none;
  cursor: pointer;
}
.ss-transcribe-hit-valid {
  background: rgba(34,197,94,0.07);
}
.ss-transcribe-hit-invalid {
  background: rgba(161,161,170,0.14);
  cursor: default;
}
.ss-transcribe-hit:active {
  background: rgba(24,24,27,0.08);
}
.ss-transcribe-event-span {
  position: absolute;
  top: 122px;
  height: 6px;
  border-radius: 999px;
  background: rgba(24,24,27,0.18);
}
.ss-transcribe-event-rest {
  background: rgba(87,83,78,0.18);
}
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
.ss-transcribe-note-w::after {
  display: none;
}
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
.ss-transcribe-rest-h {
  top: 60px;
}
.ss-transcribe-rest-w {
  top: 68px;
}
.ss-transcribe-placeholder {
  position: absolute;
  width: 9px;
  height: 9px;
  margin-left: -5px;
  margin-top: -5px;
  border-radius: 50%;
  border: 1px dashed rgba(113,113,122,0.4);
  background: rgba(255,255,255,0.6);
}
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
  color: #fafafa;
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
#back .ss-transcribe-toolbar,
#back .ss-transcribe-toolbar-compact,
#back .ss-transcribe-proto {
  display: none;
}
""".strip()

FRONT_TEMPLATE = """
{{#MelodyAudioFile}}
<script>
window.sightSingingCadenceFile = "{{text:CadenceAudioFile}}";
window.sightSingingFirstNoteFile = "{{text:FirstNoteAudioFile}}";
window.sightSingingTonicFile = "{{text:TonicAudioFile}}";
window.sightSingingMelodyFile = "{{text:MelodyAudioFile}}";
window.sightSingingAutoplayFront = [
  "cadence",
  "first",
  "tonic",
];
window.sightSingingAutoplayBack = [
  "melody",
];
</script>
{{/MelodyAudioFile}}
<!--
WARNING:
The template below this point should not refer to rendered [sound:...] fields.
This avoids autoplay and keeps the card empty if no filename field is present.
-->
<script>if (window.Audio == undefined) document.body.className += " no-audio"</script>

<div class="ss-wrap">
<div id="melody-data" style="display:none;">{{MelodyJSON}}</div>
<div id="notation" class="ss-notation"></div>
<div class="ss-controls ss-if-audio">
  <button type="button" class="ss-btn" onclick="return playCadence();">Cadence</button>
  <button type="button" class="ss-btn" onclick="return playFirstNote();">First note</button>
  <button type="button" class="ss-btn" onclick="return playTonic();">Tonic</button>
</div>
<p class="ss-prompt">Sing this melody.</p>
</div>
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
<script src="%s"></script>
<script src="%s"></script>
""".strip()

BACK_TEMPLATE = """
<div id="back">{{FrontSide}}</div>
<hr id="answer" class="ss-hr">
<div class="ss-wrap">
<div id="answer-info"></div>
<div class="ss-controls ss-if-audio">
  <button type="button" class="ss-btn" onclick="return playMelody();">Play melody</button>
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
window.sightSingingAutoplayFront = [
  "cadence",
  "melody",
];
window.sightSingingAutoplayBack = [
  "melody",
];
</script>
{{/MelodyAudioFile}}
<!--
WARNING:
The template below this point should not refer to rendered [sound:...] fields.
This avoids autoplay and keeps the card empty if no filename field is present.
-->
<script>if (window.Audio == undefined) document.body.className += " no-audio"</script>

<div class="ss-wrap">
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
  <button type="button" id="transcribe-duration-q" data-transcribe-duration="q" class="ss-btn">Quarter</button>
  <button type="button" id="transcribe-duration-h" data-transcribe-duration="h" class="ss-btn">Half</button>
  <button type="button" id="transcribe-duration-w" data-transcribe-duration="w" class="ss-btn ss-tool-active">Whole</button>
</div>
<div id="transcribe-status" class="ss-transcribe-summary">The bar starts as one whole-note interval. Select a value and tap a valid area.</div>
<div class="ss-controls ss-if-audio">
  <button type="button" class="ss-btn" onclick="return playCadence();">Cadence</button>
  <button type="button" class="ss-btn" onclick="return playMelody();">Melody</button>
</div>
<p class="ss-transcribe-proto">Prototype: one 4/4 bar with eighth, quarter, half, and whole values.</p>
</div>
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
<script src="%s"></script>
<script src="%s"></script>
<script src="%s"></script>
""".strip()

TRANSCRIBE_BACK_TEMPLATE = """
<div id="back">{{FrontSide}}</div>
<hr id="answer" class="ss-hr">
<div class="ss-wrap">
<div id="transcribe-result" class="ss-transcribe-summary"></div>
<div class="ss-transcribe-summary"><strong>Your transcription</strong></div>
<div id="transcribe-user" class="ss-notation"></div>
<div class="ss-transcribe-summary"><strong>Target notation</strong></div>
<div id="transcribe-target" class="ss-notation"></div>
<div class="ss-controls ss-if-audio">
  <button type="button" class="ss-btn" onclick="return playMelody();">Play melody</button>
</div>
</div>
<script>
if (window.SightSingingTranscriptionReview) {
  window.SightSingingTranscriptionReview();
}
</script>
""".strip()

FRONT_TEMPLATE = FRONT_TEMPLATE % (VEXFLOW_ASSET_NAME, RENDERER_ASSET_NAME)
TRANSCRIBE_FRONT_TEMPLATE = TRANSCRIBE_FRONT_TEMPLATE % (
    VEXFLOW_ASSET_NAME,
    RENDERER_ASSET_NAME,
    TRANSCRIPTION_ASSET_NAME,
)


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
        css=MODEL_CSS,
    )
