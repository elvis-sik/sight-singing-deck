"""Anki note type (genanki) for sight-singing MVP cards."""

from __future__ import annotations

import genanki

# Stable IDs for this deck (change if you fork a separate published deck).
DECK_ID = 2_948_817_001
MODEL_ID = 2_948_817_002
MODEL_NAME = "Sight Singing (MVP v1)"

FIELD_NAMES = ["MelodyJSON", "StageID", "MelodyID"]

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
""".strip()

FRONT_TEMPLATE = """
<div class="ss-wrap">
<div id="melody-data" style="display:none;">{{MelodyJSON}}</div>
<div id="notation" class="ss-notation"></div>
<div class="ss-controls">
  <button type="button" class="ss-btn" onclick="playCadence();">Cadence</button>
  <button type="button" class="ss-btn" onclick="playFirstNote();">First note</button>
  <button type="button" class="ss-btn" onclick="playTonic();">Tonic</button>
</div>
<p class="ss-prompt">Sing this melody.</p>
</div>
<script src="_vexflow.js"></script>
<script src="_player.js"></script>
<script src="_renderer.js"></script>
""".strip()

BACK_TEMPLATE = """
{{FrontSide}}
<hr id="answer" class="ss-hr">
<div class="ss-wrap">
<div id="answer-info"></div>
<div class="ss-controls">
  <button type="button" class="ss-btn" onclick="playMelody();">Play melody</button>
</div>
</div>
<script>SightSingingRedraw && SightSingingRedraw();</script>
""".strip()


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
            }
        ],
        css=MODEL_CSS,
    )
