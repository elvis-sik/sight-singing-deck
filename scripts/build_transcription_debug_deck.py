#!/usr/bin/env python3
"""Build a deck of transcription UI variants for fast Anki testing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import genanki

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


DECK_ID = 2_948_817_201
FIELD_NAMES = ["Title", "VariantID"]

BASE_CSS = """
.card {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  font-size: 18px;
  text-align: center;
  color: #18181b;
  background: #fafaf9;
}
.debug-wrap {
  max-width: 560px;
  margin: 0 auto;
  padding: 12px 8px 24px;
}
.debug-title {
  font-size: 22px;
  font-weight: 700;
  margin: 8px 0 4px;
}
.debug-subtitle {
  font-size: 13px;
  color: #57534e;
  margin-bottom: 12px;
}
.debug-toolbar {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  margin: 10px 0;
}
.debug-btn {
  font-family: inherit;
  font-size: 14px;
  min-width: 78px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid rgba(0,0,0,0.18);
  background: #f5f5f4;
  color: #1c1917;
}
.debug-active {
  background: #18181b !important;
  color: #fafaf9 !important;
  border-color: #18181b !important;
}
.debug-status {
  font-size: 15px;
  color: #44403c;
  margin: 12px 0;
}
.debug-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 8px;
  margin: 16px 0;
}
.debug-slot {
  min-height: 62px;
  border-radius: 10px;
  border: 1px solid rgba(0,0,0,0.12);
  background: #fff;
  color: #18181b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  padding: 6px 4px;
}
.debug-hint {
  font-size: 13px;
  color: #78716c;
  line-height: 1.45;
}
hr {
  border: 0;
  border-top: 1px solid rgba(0,0,0,0.12);
  margin: 18px 0 12px;
}
""".strip()


def _buttons_html(inline_onclick: bool) -> str:
    def btn(action: str, value: str, label: str, element_id: str) -> str:
        attrs = [
            'type="button"',
            f'id="{element_id}"',
            f'class="debug-btn{" debug-active" if element_id.endswith("-note") or element_id.endswith("-q") else ""}"',
        ]
        if inline_onclick:
            if action == "reset":
                attrs.append('onclick="return debugReset();"')
            elif action == "slot":
                attrs.append(f'onclick="return debugActivateSlot({value});"')
            elif action == "mode":
                attrs.append(f'onclick="return debugSetMode(\'{value}\');"')
            elif action == "duration":
                attrs.append(f'onclick="return debugSetDuration(\'{value}\');"')
        else:
            if action != "slot":
                attrs.append(f'data-action="{action}"')
                if value:
                    attrs.append(f'data-value="{value}"')
        return f"<button {' '.join(attrs)}>{label}</button>"

    top = "\n".join(
        [
            btn("mode", "note", "Notes", "debug-mode-note"),
            btn("mode", "rest", "Rests", "debug-mode-rest"),
            btn("mode", "erase", "Erase", "debug-mode-erase"),
            btn("reset", "", "Reset", "debug-reset"),
        ]
    )
    bottom = "\n".join(
        [
            btn("duration", "8", "Eighth", "debug-duration-8"),
            btn("duration", "q", "Quarter", "debug-duration-q"),
            btn("duration", "h", "Half", "debug-duration-h"),
            btn("duration", "w", "Whole", "debug-duration-w"),
        ]
    )

    slots = []
    for i in range(8):
        if inline_onclick:
            slots.append(
                f'<button type="button" class="debug-slot" onclick="return debugActivateSlot({i});">{i + 1}</button>'
            )
        else:
            slots.append(
                f'<button type="button" class="debug-slot" data-slot="{i}">{i + 1}</button>'
            )

    return f"""
<div class="debug-toolbar">{top}</div>
<div class="debug-toolbar">{bottom}</div>
<div class="debug-status" data-role="status"></div>
<div class="debug-grid">
{''.join(slots)}
</div>
""".strip()


def _base_script(binding_code: str, export_globals: bool) -> str:
    globals_block = """
window.debugSetMode = function (mode) {
  state.mode = mode;
  render();
  return false;
};
window.debugSetDuration = function (duration) {
  state.duration = duration;
  render();
  return false;
};
window.debugReset = function () {
  state.slots = ["", "", "", "", "", "", "", ""];
  render();
  return false;
};
window.debugActivateSlot = function (index) {
  activateSlot(index);
  return false;
};
""".strip()

    return f"""
<script>
(function () {{
  "use strict";
  var root = document.querySelector("[data-debug-root]");
  if (!root) return;
  var state = {{
    mode: "note",
    duration: "q",
    slots: ["", "", "", "", "", "", "", ""],
  }};

  function render() {{
    var buttons = root.querySelectorAll("[data-action], #debug-mode-note, #debug-mode-rest, #debug-mode-erase, #debug-duration-8, #debug-duration-q, #debug-duration-h, #debug-duration-w");
    for (var i = 0; i < buttons.length; i++) {{
      var btn = buttons[i];
      var isMode = btn.id.indexOf("debug-mode-") === 0;
      var isDuration = btn.id.indexOf("debug-duration-") === 0;
      var active = false;
      if (isMode) active = btn.id === "debug-mode-" + state.mode;
      if (isDuration) active = btn.id === "debug-duration-" + state.duration;
      btn.classList.toggle("debug-active", active);
    }}
    var status = root.querySelector("[data-role='status']");
    if (status) {{
      status.textContent = "Selected: " + state.mode + " / " + state.duration;
    }}
    var slots = root.querySelectorAll("[data-slot], .debug-grid .debug-slot");
    for (var j = 0; j < slots.length; j++) {{
      slots[j].textContent = state.slots[j] || String(j + 1);
    }}
  }}

  function activateSlot(index) {{
    if (index < 0 || index >= state.slots.length) return;
    if (state.mode === "erase") state.slots[index] = "";
    else if (state.mode === "rest") state.slots[index] = "R:" + state.duration;
    else state.slots[index] = "N:" + state.duration;
    render();
  }}

  {globals_block if export_globals else ""}

  {binding_code}
  render();
}})();
</script>
""".strip()


def _variant_template(variant: str) -> str:
    if variant == "inline-onclick":
        return _buttons_html(True) + "\n" + _base_script("", True)

    if variant == "inline-bind-click":
        code = """
var controls = root.querySelectorAll("[data-action]");
for (var i = 0; i < controls.length; i++) {
  controls[i].addEventListener("click", function (event) {
    event.preventDefault();
    var t = event.currentTarget;
    if (t.dataset.action === "mode") state.mode = t.dataset.value;
    else if (t.dataset.action === "duration") state.duration = t.dataset.value;
    else if (t.dataset.action === "reset") state.slots = ["", "", "", "", "", "", "", ""];
    render();
  });
}
var slots = root.querySelectorAll("[data-slot]");
for (var j = 0; j < slots.length; j++) {
  slots[j].addEventListener("click", function (event) {
    event.preventDefault();
    activateSlot(Number(event.currentTarget.dataset.slot || -1));
  });
}
""".strip()
        return _buttons_html(False) + "\n" + _base_script(code, False)

    if variant == "delegated-click":
        code = """
root.addEventListener("click", function (event) {
  var actionTarget = event.target.closest("[data-action]");
  if (actionTarget) {
    event.preventDefault();
    if (actionTarget.dataset.action === "mode") state.mode = actionTarget.dataset.value;
    else if (actionTarget.dataset.action === "duration") state.duration = actionTarget.dataset.value;
    else if (actionTarget.dataset.action === "reset") state.slots = ["", "", "", "", "", "", "", ""];
    render();
    return;
  }
  var slotTarget = event.target.closest("[data-slot]");
  if (slotTarget) {
    event.preventDefault();
    activateSlot(Number(slotTarget.dataset.slot || -1));
  }
});
""".strip()
        return _buttons_html(False) + "\n" + _base_script(code, False)

    if variant == "touch-and-click":
        code = """
function bind(el, handler) {
  el.addEventListener("click", handler);
  el.addEventListener("touchstart", handler, { passive: false });
}
var controls = root.querySelectorAll("[data-action]");
for (var i = 0; i < controls.length; i++) {
  bind(controls[i], function (event) {
    event.preventDefault();
    var t = event.currentTarget;
    if (t.dataset.action === "mode") state.mode = t.dataset.value;
    else if (t.dataset.action === "duration") state.duration = t.dataset.value;
    else if (t.dataset.action === "reset") state.slots = ["", "", "", "", "", "", "", ""];
    render();
  });
}
var slots = root.querySelectorAll("[data-slot]");
for (var j = 0; j < slots.length; j++) {
  bind(slots[j], function (event) {
    event.preventDefault();
    activateSlot(Number(event.currentTarget.dataset.slot || -1));
  });
}
""".strip()
        return _buttons_html(False) + "\n" + _base_script(code, False)

    if variant == "delayed-init":
        code = """
function bindAll() {
  var controls = root.querySelectorAll("[data-action]");
  for (var i = 0; i < controls.length; i++) {
    controls[i].addEventListener("click", function (event) {
      event.preventDefault();
      var t = event.currentTarget;
      if (t.dataset.action === "mode") state.mode = t.dataset.value;
      else if (t.dataset.action === "duration") state.duration = t.dataset.value;
      else if (t.dataset.action === "reset") state.slots = ["", "", "", "", "", "", "", ""];
      render();
    });
  }
  var slots = root.querySelectorAll("[data-slot]");
  for (var j = 0; j < slots.length; j++) {
    slots[j].addEventListener("click", function (event) {
      event.preventDefault();
      activateSlot(Number(event.currentTarget.dataset.slot || -1));
    });
  }
}
setTimeout(bindAll, 0);
window.addEventListener("pageshow", function () { setTimeout(bindAll, 0); }, { once: true });
""".strip()
        return _buttons_html(False) + "\n" + _base_script(code, False)

    if variant == "pointerdown":
        code = """
var controls = root.querySelectorAll("[data-action]");
for (var i = 0; i < controls.length; i++) {
  controls[i].addEventListener("pointerdown", function (event) {
    event.preventDefault();
    var t = event.currentTarget;
    if (t.dataset.action === "mode") state.mode = t.dataset.value;
    else if (t.dataset.action === "duration") state.duration = t.dataset.value;
    else if (t.dataset.action === "reset") state.slots = ["", "", "", "", "", "", "", ""];
    render();
  });
}
var slots = root.querySelectorAll("[data-slot]");
for (var j = 0; j < slots.length; j++) {
  slots[j].addEventListener("pointerdown", function (event) {
    event.preventDefault();
    activateSlot(Number(event.currentTarget.dataset.slot || -1));
  });
}
""".strip()
        return _buttons_html(False) + "\n" + _base_script(code, False)

    if variant == "external-script":
        return (
            _buttons_html(False)
            + """
<script>
var root = document.querySelector("[data-debug-root]");
if (root) root.dataset.bindEvent = "click";
</script>
<script src="_transcription_debug_external.js"></script>
""".strip()
        )

    raise ValueError(f"Unknown variant: {variant}")


def _front_template(title: str, variant: str, hint: str) -> str:
    return f"""
<div class="debug-wrap" data-debug-root="1">
  <div class="debug-title">{title}</div>
  <div class="debug-subtitle">{hint}</div>
  {_variant_template(variant)}
  <div class="debug-hint">Expected behavior: selecting a duration changes the dark button, and tapping a slot places that duration. This card is only for interaction testing.</div>
</div>
""".strip()


def _back_template() -> str:
    return """
<div id="back">{{FrontSide}}</div>
<hr>
<div class="debug-wrap">
  <div class="debug-hint">If this one works in Anki, note the variant name. If it fails, note exactly what failed: selection highlight, slot output, or both.</div>
  <div class="debug-hint">{{VariantID}}</div>
</div>
""".strip()


def make_model(model_id: int, name: str, title: str, variant: str, hint: str) -> genanki.Model:
    return genanki.Model(
        model_id=model_id,
        name=name,
        fields=[{"name": n} for n in FIELD_NAMES],
        templates=[
            {
                "name": "Card 1",
                "qfmt": _front_template(title, variant, hint),
                "afmt": _back_template(),
            }
        ],
        css=BASE_CSS,
    )


def build(out_path: Path) -> None:
    variants = [
        (
            2_948_817_211,
            "Transcription Debug - Inline Onclick",
            "Variant 1: Inline Onclick",
            "inline-onclick",
            "Buttons call global functions directly from inline onclick attributes.",
        ),
        (
            2_948_817_212,
            "Transcription Debug - Inline Bind Click",
            "Variant 2: Direct Click Bind",
            "inline-bind-click",
            "Each button gets an addEventListener('click') binding during init.",
        ),
        (
            2_948_817_213,
            "Transcription Debug - Delegated Click",
            "Variant 3: Delegated Click",
            "delegated-click",
            "One click listener on the root handles all toolbar and slot interaction.",
        ),
        (
            2_948_817_214,
            "Transcription Debug - Touch And Click",
            "Variant 4: Touch + Click",
            "touch-and-click",
            "Buttons listen to both touchstart and click.",
        ),
        (
            2_948_817_215,
            "Transcription Debug - Delayed Init",
            "Variant 5: Delayed Init",
            "delayed-init",
            "Bindings attach after a timeout, plus a pageshow rebind.",
        ),
        (
            2_948_817_216,
            "Transcription Debug - Pointerdown",
            "Variant 6: Pointerdown",
            "pointerdown",
            "Buttons and slots use pointerdown instead of click.",
        ),
        (
            2_948_817_217,
            "Transcription Debug - External Script",
            "Variant 7: External Script",
            "external-script",
            "Same data-attribute UI, but binding happens from a packaged external JS asset.",
        ),
    ]

    deck = genanki.Deck(deck_id=DECK_ID, name="Transcription Debug Variants")
    for index, (model_id, model_name, title, variant, hint) in enumerate(variants, start=1):
        model = make_model(model_id, model_name, title, variant, hint)
        note = genanki.Note(
            model=model,
            fields=[title, variant],
            tags=["transcription_debug", f"variant_{index}"],
        )
        deck.add_note(note)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pkg = genanki.Package(deck)
    pkg.media_files = [str(ROOT / "assets" / "_transcription_debug_external.js")]
    pkg.write_to_file(str(out_path))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build transcription debug variant deck.")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "out" / "transcription-debug-variants.apkg",
    )
    args = parser.parse_args(argv)
    build(args.out)
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
