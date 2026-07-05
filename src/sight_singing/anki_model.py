"""Anki note type (genanki) for sight-singing MVP cards."""

from __future__ import annotations

from pathlib import Path

import genanki

# Stable IDs for this deck (change if you fork a separate published deck).
DECK_ID = 2_948_817_001
MODEL_ID = 2_948_817_015
MODEL_NAME = "Sight Singing (MVP v24 inline engine)"

# All JavaScript — VexFlow, the renderer, and the transcription editor — is
# INLINED into the note-type templates; the deck ships NO external .js media.
# This is because AnkiDroid intermittently fails to serve freshly-imported
# media over its local HTTP server right after import. VexFlow is the slim
# Bravura-only build (~570 KB vs the ~1 MB full build) so inlining it is
# affordable; being inline it also can never fail to load, on any platform.
_ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
_CSS_PATH = _ASSETS_DIR / "card_styles.css"
_VEXFLOW_PATH = _ASSETS_DIR / "_vexflow.js"
_RENDERER_PATH = _ASSETS_DIR / "_renderer.js"
_TRANSCRIPTION_PATH = _ASSETS_DIR / "_transcription.js"
_ERRORDETECT_PATH = _ASSETS_DIR / "_errordetect.js"

FIELD_NAMES = [
    "MelodyJSON",
    "StageID",
    "MelodyID",
    "CadenceAudio",
    "FirstNoteAudio",
    "TonicAudio",
    "MelodyAudio",
    "DroneAudio",
    "CadenceAudioFile",
    "FirstNoteAudioFile",
    "TonicAudioFile",
    "MelodyAudioFile",
    "DroneAudioFile",
]


def model_css() -> str:
    return _CSS_PATH.read_text(encoding="utf-8").strip()


def _inline_script(path: Path) -> str:
    """Read a JS asset and wrap it in an inline <script> tag for a template.

    The sources contain no `</script>` or Anki `{{ }}` sequences (guarded by a
    repo test), so they embed verbatim.
    """
    js = path.read_text(encoding="utf-8")
    if "</script" in js.lower() or "{{" in js or "}}" in js:
        raise ValueError(f"{path.name} is not safe to inline into a template")
    return "<script>\n" + js.strip() + "\n</script>"


def renderer_inline() -> str:
    return _inline_script(_RENDERER_PATH)


def transcription_inline() -> str:
    return _inline_script(_TRANSCRIPTION_PATH)


def errordetect_inline() -> str:
    return _inline_script(_ERRORDETECT_PATH)


def vexflow_inline() -> str:
    """Inline the (slim, minified) VexFlow bundle as a <script> tag.

    The minified bundle contains a single `{{` (a function body that opens a
    block statement). Anki's `{{field}}` templating would otherwise treat it
    as a field, so split it into `{ {` — whitespace-only in JS, semantically
    identical, and verified to keep the bundle valid.
    """
    js = _VEXFLOW_PATH.read_text(encoding="utf-8")
    if "</script" in js.lower():
        raise ValueError("VexFlow bundle unexpectedly contains </script>")
    js = js.replace("{{", "{ {")
    if "{{" in js:
        raise ValueError("VexFlow bundle still contains {{ after transform")
    return "<script>\n" + js.strip() + "\n</script>"


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
      case "drone":
        return window.sightSingingDroneFile;
      case "written":
        return window.sightSingingWrittenFile;
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

  function playDrone() {
    return playSightSingingKey("drone");
  }

  function playMelody() {
    return playSightSingingKey("melody");
  }

  function playWritten() {
    return playSightSingingKey("written");
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
# Sustained sound waves — the held tonic drone.
ICON_DRONE = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.8" stroke-linecap="round">'
    '<path d="M4 12 H7"/><path d="M17 12 H20"/>'
    '<path d="M9 6 C 11 9, 11 15, 9 18"/>'
    '<path d="M15 6 C 13 9, 13 15, 15 18"/>'
    '<circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none"/></svg>'
)

# Runs before the <script src> tags: captures resource/JS load errors so the
# diagnostic tail can report them. Idempotent across card sides.
BOOT_HEAD = """
<script>
(function () {
  if (window.__ssBoot) return;
  window.__ssBoot = { errors: [] };
  window.addEventListener(
    "error",
    function (e) {
      var t = e && e.target;
      if (t && (t.src || t.href)) {
        window.__ssBoot.errors.push("load-fail " + (t.src || t.href));
      } else if (e && e.message) {
        window.__ssBoot.errors.push("err " + e.message);
      }
    },
    true
  );
})();
</script>
""".strip()

# Runs after the <script src> tags. On the two platforms that already work
# this is a no-op (the engine is ready within ~1s). On a platform where the
# external scripts do not load/execute (observed on AnkiDroid, whose media
# uses a file: scheme), it (1) re-injects the scripts as dynamically-created
# nodes — a different load path that can succeed where the static tags did
# not — and (2) if that still fails, prints a visible diagnostic naming the
# exact cause instead of leaving a blank card.
BOOT_TAIL = """
<script>
(function () {
  if (!window.__ssBoot || window.__ssBoot.watching) return;
  window.__ssBoot.watching = true;

  function ready() {
    return (
      typeof window.SightSingingRedraw === "function" &&
      !!(window.Vex && window.Vex.Flow)
    );
  }

  var tries = 0;
  var recovered = false;
  var timer = setInterval(function () {
    tries += 1;
    if (ready()) {
      clearInterval(timer);
      return;
    }
    if (!recovered && tries === 75) {
      recovered = true;
      reinject();
    }
    if (tries >= 150) {
      clearInterval(timer);
      if (!ready()) showDiagnostic();
    }
  }, 40);

  function reinject() {
    var seen = {};
    var tags = document.querySelectorAll("script[src]");
    for (var i = 0; i < tags.length; i++) {
      var url = tags[i].getAttribute("src");
      if (/_vexflow|_renderer|_transcription/.test(url) && !seen[url]) {
        seen[url] = 1;
        var s = document.createElement("script");
        s.src = url;
        s.async = false;
        document.head.appendChild(s);
      }
    }
  }

  function showDiagnostic() {
    if (document.querySelector(".ss-diag")) return;
    var host =
      document.getElementById("notation") ||
      document.getElementById("transcribe-editor") ||
      document.querySelector(".ss-wrap") ||
      document.body;
    var pre = document.createElement("pre");
    pre.className = "ss-diag";
    pre.textContent = [
      "Sight Singing — notation engine did not load.",
      "base: " + document.baseURI,
      "VexFlow: " + (window.Vex && window.Vex.Flow ? "loaded" : "MISSING"),
      "renderer: " + typeof window.SightSingingRedraw,
      "transcription: " + typeof window.SightSingingTranscriptionReview,
      "load errors: " +
        ((window.__ssBoot.errors || []).join(" | ") || "none"),
      "(please screenshot this and send it)",
    ].join("\\n");
    if (host) host.appendChild(pre);
  }
})();
</script>
""".strip()

FRONT_TEMPLATE = """
{{#MelodyAudioFile}}
<script>
window.sightSingingCadenceFile = "{{text:CadenceAudioFile}}";
window.sightSingingFirstNoteFile = "{{text:FirstNoteAudioFile}}";
window.sightSingingTonicFile = "{{text:TonicAudioFile}}";
window.sightSingingMelodyFile = "{{text:MelodyAudioFile}}";
window.sightSingingDroneFile = "{{text:DroneAudioFile}}";
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
__BOOT_HEAD__

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
  <button type="button" class="ss-btn" onclick="return playDrone();">__ICON_DRONE__<span>Drone</span></button>
</div>
<p class="ss-prompt">Sing this melody.</p>
</div>
__VEXFLOW_INLINE__
__RENDERER_INLINE__
__BOOT_TAIL__
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
__BOOT_TAIL__
""".strip()

TRANSCRIBE_FRONT_TEMPLATE = """
{{#MelodyAudioFile}}
<script>
window.sightSingingMelodyId = "{{text:MelodyID}}";
window.sightSingingCadenceFile = "{{text:CadenceAudioFile}}";
window.sightSingingFirstNoteFile = "{{text:FirstNoteAudioFile}}";
window.sightSingingTonicFile = "{{text:TonicAudioFile}}";
window.sightSingingMelodyFile = "{{text:MelodyAudioFile}}";
window.sightSingingDroneFile = "{{text:DroneAudioFile}}";
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
__BOOT_HEAD__

<div class="ss-wrap">
<div id="melody-data" style="display:none;">{{MelodyJSON}}</div>
<div class="ss-meta" id="melody-meta" data-ss-badge="Transcribe"></div>
<div class="ss-panel ss-editor-panel">
  <div id="transcribe-editor"></div>
</div>
<div id="transcribe-ui"></div>
<div class="ss-controls ss-if-audio ss-transcribe-front-audio">
  <button type="button" class="ss-btn" onclick="return playCadence();">__ICON_CHORD__<span>Cadence</span></button>
  <button type="button" class="ss-btn" onclick="return playDrone();">__ICON_DRONE__<span>Drone</span></button>
  <button type="button" class="ss-btn" onclick="return playMelody();">__ICON_PLAY__<span>Replay melody</span></button>
</div>
<p class="ss-prompt ss-prompt-transcribe">Write down the melody you hear.</p>
</div>
__VEXFLOW_INLINE__
__RENDERER_INLINE__
__TRANSCRIPTION_INLINE__
__BOOT_TAIL__
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
__BOOT_TAIL__
""".strip()


def _fill(template: str) -> str:
    return (
        template.replace("__AUDIO_SCRIPT__", AUDIO_SCRIPT)
        .replace("__BOOT_HEAD__", BOOT_HEAD)
        .replace("__BOOT_TAIL__", BOOT_TAIL)
        .replace("__ICON_PLAY__", ICON_PLAY)
        .replace("__ICON_CHORD__", ICON_CHORD)
        .replace("__ICON_NOTE__", ICON_NOTE)
        .replace("__ICON_FORK__", ICON_FORK)
        .replace("__ICON_DRONE__", ICON_DRONE)
        .replace("__VEXFLOW_INLINE__", vexflow_inline())
        .replace("__RENDERER_INLINE__", renderer_inline())
        .replace("__TRANSCRIPTION_INLINE__", transcription_inline())
        .replace("__ERRORDETECT_INLINE__", errordetect_inline())
    )


# --- Error-detection note type ------------------------------------------------
# Its own model (a separate note type) so it never turns the Sing/Transcribe
# notes into extra cards. One card: hear the played (altered) melody against the
# written score, find the wrong note.
ERROR_MODEL_ID = 2_948_817_016
ERROR_MODEL_NAME = "Sight Singing — Error Detection (v1)"

ERROR_FIELD_NAMES = [
    "MelodyJSON",       # the WRITTEN melody (notation)
    "StageID",
    "MelodyID",
    "ErrorIndex",       # 0-based index of the wrong note
    "ErrorLabel",       # human reveal, e.g. "Note 2: written mi (E4), played re (D4)"
    "CadenceAudioFile",
    "FirstNoteAudioFile",
    "TonicAudioFile",
    "DroneAudioFile",
    "MelodyAudioFile",  # the PLAYED (altered) clip — the wrong performance
    "WrittenAudioFile",  # the correct clip — "play as written"
]

ERROR_FRONT_TEMPLATE = """
{{#MelodyAudioFile}}
<script>
window.sightSingingCadenceFile = "{{text:CadenceAudioFile}}";
window.sightSingingFirstNoteFile = "{{text:FirstNoteAudioFile}}";
window.sightSingingTonicFile = "{{text:TonicAudioFile}}";
window.sightSingingDroneFile = "{{text:DroneAudioFile}}";
window.sightSingingMelodyFile = "{{text:MelodyAudioFile}}";
window.sightSingingWrittenFile = "{{text:WrittenAudioFile}}";
</script>
{{/MelodyAudioFile}}
<script>
window.sightSingingAutoplayFront = [
  "tonic",
  "melody",
];
window.sightSingingAutoplayBack = [
  "melody",
];
</script>
__AUDIO_SCRIPT__
__BOOT_HEAD__

<div class="ss-wrap">
<div id="melody-data" style="display:none;">{{MelodyJSON}}</div>
<div id="error-index" style="display:none;">{{ErrorIndex}}</div>
<div class="ss-meta" id="melody-meta" data-ss-badge="Find the error"></div>
<div class="ss-panel">
  <div id="notation" class="ss-notation"></div>
</div>
<div class="ss-controls ss-if-audio">
  <button type="button" class="ss-btn" onclick="return playCadence();">__ICON_CHORD__<span>Cadence</span></button>
  <button type="button" class="ss-btn" onclick="return playTonic();">__ICON_FORK__<span>Tonic</span></button>
  <button type="button" class="ss-btn" onclick="return playMelody();">__ICON_PLAY__<span>Play (has 1 wrong note)</span></button>
</div>
<p class="ss-prompt">One note is played differently from the score. Tap the wrong note.</p>
</div>
__VEXFLOW_INLINE__
__RENDERER_INLINE__
__ERRORDETECT_INLINE__
__BOOT_TAIL__
""".strip()

ERROR_BACK_TEMPLATE = """
<div id="error-back">{{FrontSide}}</div>
<hr id="answer" class="ss-hr">
<div class="ss-wrap">
<div id="error-verdict" class="ss-verdict ss-verdict-none"></div>
<div id="answer-info" class="ss-answer-info">{{ErrorLabel}}</div>
<div class="ss-controls ss-if-audio">
  <button type="button" class="ss-btn" onclick="return playWritten();">__ICON_NOTE__<span>As written</span></button>
  <button type="button" class="ss-btn" onclick="return playMelody();">__ICON_PLAY__<span>As heard</span></button>
</div>
</div>
<script>window.SightSingingErrorDetect && window.SightSingingErrorDetect();</script>
__BOOT_TAIL__
""".strip()


# Rhythm-first cards reuse the Sing card verbatim (one repeated pitch, all the
# information is in the durations) — only the badge and prompt change. Sing-only
# (a Transcribe/pitch-dictation card on a single repeated pitch is pointless), so
# it gets its own note type.
RHYTHM_MODEL_ID = 2_948_817_017
RHYTHM_MODEL_NAME = "Sight Singing — Rhythm (v1)"
RHYTHM_FRONT_TEMPLATE = FRONT_TEMPLATE.replace(
    'data-ss-badge="Sing"', 'data-ss-badge="Rhythm"'
).replace("Sing this melody.", "Read and clap this rhythm (one pitch — it's all timing).")
RHYTHM_BACK_TEMPLATE = BACK_TEMPLATE

FRONT_TEMPLATE = _fill(FRONT_TEMPLATE)
BACK_TEMPLATE = _fill(BACK_TEMPLATE)
TRANSCRIBE_FRONT_TEMPLATE = _fill(TRANSCRIBE_FRONT_TEMPLATE)
TRANSCRIBE_BACK_TEMPLATE = _fill(TRANSCRIBE_BACK_TEMPLATE)
ERROR_FRONT_TEMPLATE = _fill(ERROR_FRONT_TEMPLATE)
ERROR_BACK_TEMPLATE = _fill(ERROR_BACK_TEMPLATE)
RHYTHM_FRONT_TEMPLATE = _fill(RHYTHM_FRONT_TEMPLATE)
RHYTHM_BACK_TEMPLATE = _fill(RHYTHM_BACK_TEMPLATE)


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


def make_rhythm_model() -> genanki.Model:
    return genanki.Model(
        model_id=RHYTHM_MODEL_ID,
        name=RHYTHM_MODEL_NAME,
        fields=[{"name": n} for n in FIELD_NAMES],
        templates=[
            {
                "name": "Rhythm",
                "qfmt": RHYTHM_FRONT_TEMPLATE,
                "afmt": RHYTHM_BACK_TEMPLATE,
            },
        ],
        css=model_css(),
    )


def make_error_model() -> genanki.Model:
    return genanki.Model(
        model_id=ERROR_MODEL_ID,
        name=ERROR_MODEL_NAME,
        fields=[{"name": n} for n in ERROR_FIELD_NAMES],
        templates=[
            {
                "name": "FindError",
                "qfmt": ERROR_FRONT_TEMPLATE,
                "afmt": ERROR_BACK_TEMPLATE,
            },
        ],
        css=model_css(),
    )
