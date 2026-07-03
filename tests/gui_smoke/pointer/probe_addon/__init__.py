"""Reviewer pointer-input probe for the transcription editor.

Runs inside disposable Anki (Docker/Xvfb). It opens the reviewer on a
Transcribe card, drives the real mouse with xdotool (X11 -> Qt -> Chromium,
the same input path a user exercises), records every pointer event's client
coordinates as the page receives them, clicks to place a note aimed at
AIM_PITCH, and reports whether the placed event matches the aim.

Environment:
- ANKI_ADDON_WORKBENCH_RESULT: where to write the JSON result (contract).
- SS_PROBE_ZOOM: optional webview zoom factor override (e.g. "2.0").
- SS_PROBE_SHOT_DIR: optional directory for a final screenshot.
"""

from __future__ import annotations

import json
import os
import subprocess
import traceback
from pathlib import Path
from typing import Any, Callable

from aqt import gui_hooks, mw
from aqt.qt import (
    QApplication,
    QEvent,
    QMouseEvent,
    QPoint,
    QPointF,
    Qt,
    QTimer,
)

RESULT_ENV = "ANKI_ADDON_WORKBENCH_RESULT"
DECK_NAME = "Sight Singing MVP"
AIM_UNIT = 0
AIM_PITCH = "G4"
READY_POLLS = 60
SETTLE_MS = 1500

_done = {"value": False}
_report: dict[str, Any] = {"probe": "pointer_input", "steps": []}


def _step(name: str, **info: Any) -> None:
    _report["steps"].append({"step": name, **info})


def _write_result(payload: dict[str, Any]) -> None:
    if _done["value"]:
        return
    _done["value"] = True
    path = os.environ.get(RESULT_ENV)
    if path:
        Path(path).write_text(
            json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
        )
    if mw is not None:
        mw.unloadProfileAndExit()


def _fail(error: str, **extra: Any) -> None:
    _write_result({"ok": False, "error": error, **_report, **extra})


def _screenshot() -> str | None:
    shot_dir = os.environ.get("SS_PROBE_SHOT_DIR")
    if not shot_dir or mw is None:
        return None
    try:
        zoom = os.environ.get("SS_PROBE_ZOOM", "1")
        out = Path(shot_dir) / f"pointer-probe-zoom-{zoom}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        mw.grab().save(str(out))
        return str(out)
    except Exception:
        return None


def _xdotool(*args: str) -> str:
    proc = subprocess.run(
        ["xdotool", *args], check=True, timeout=10, capture_output=True, text=True
    )
    return proc.stdout.strip()


def _eval_json(js: str, callback: Callable[[Any], None]) -> None:
    """Evaluate a JS expression that returns a JSON string."""

    def _on_value(value: Any) -> None:
        try:
            callback(json.loads(value) if isinstance(value, str) else value)
        except Exception:
            _fail("callback failed", traceback_text=traceback.format_exc())

    mw.reviewer.web.evalWithCallback(js, _on_value)


JS_READY = """
(function () {
  try {
    var dbg = window.SightSingingTranscriptionDebug;
    if (!dbg) return JSON.stringify({ready: false, why: "no debug api"});
    var p = dbg.clientPoint(%d, "%s");
    if (!p) return JSON.stringify({ready: false, why: "no geometry"});
    return JSON.stringify({ready: true, point: p});
  } catch (e) {
    return JSON.stringify({ready: false, why: String(e)});
  }
})()
""" % (AIM_UNIT, AIM_PITCH)

JS_INSTALL_LOGGER = """
(function () {
  window.__ssPtrLog = [];
  var types = ["pointermove", "pointerdown", "pointerup",
               "mousemove", "mousedown", "mouseup", "click"];
  types.forEach(function (type) {
    document.addEventListener(type, function (e) {
      if (window.__ssPtrLog.length > 400) return;
      var t = e.target;
      window.__ssPtrLog.push({
        type: type,
        clientX: Math.round(e.clientX * 10) / 10,
        clientY: Math.round(e.clientY * 10) / 10,
        target: (t && t.nodeName || "?") +
          (t && t.getAttribute && t.getAttribute("class")
            ? "." + String(t.getAttribute("class")).split(" ")[0]
            : "")
      });
    }, true);
  });
})();
"""

JS_COLLECT = """
(function () {
  var dbg = window.SightSingingTranscriptionDebug;
  var svgs = document.querySelectorAll(".ss-editor-score svg");
  var heads = [];
  if (svgs.length) {
    var nodes = svgs[svgs.length - 1].querySelectorAll(".vf-notehead");
    for (var i = 0; i < nodes.length; i++) {
      var r = nodes[i].getBoundingClientRect();
      heads.push({
        x: Math.round((r.left + r.width / 2) * 10) / 10,
        y: Math.round((r.top + r.height / 2) * 10) / 10
      });
    }
  }
  var refs = {};
  ["C4", "E4", "G4", "C5"].forEach(function (p) {
    var pt = dbg && dbg.clientPoint(0, p);
    refs[p] = pt ? Math.round(pt.y * 10) / 10 : null;
  });
  var stored = null;
  try {
    stored = localStorage.getItem(
      "ss-transcribe:" + String(window.sightSingingMelodyId || "").trim()
    );
  } catch (e) {}
  return JSON.stringify({
    log: window.__ssPtrLog || [],
    state: dbg ? dbg.getState() : null,
    scoreSvgCount: svgs.length,
    editorCount: document.querySelectorAll("#transcribe-editor").length,
    renderedNoteheads: heads,
    pitchRefY: refs,
    storedAnswer: stored
  });
})()
"""

JS_LOG_LENGTH = "String((window.__ssPtrLog || []).length)"


def _qt_input_target():
    web = mw.reviewer.web
    return web.focusProxy() or web


def _send_qt_mouse(kind: str, widget_x: float, widget_y: float) -> None:
    """Synthesize a mouse event into the webview's input widget.

    This enters QtWebEngine's own event pipeline, so the Qt->Chromium
    coordinate transform (zoom/DPR mapping) is exercised exactly as with
    OS-level input.
    """
    local = QPointF(widget_x, widget_y)
    global_point = QPointF(
        mw.reviewer.web.mapToGlobal(QPoint(int(widget_x), int(widget_y)))
    )
    no_button = Qt.MouseButton.NoButton
    left = Qt.MouseButton.LeftButton
    modifiers = Qt.KeyboardModifier.NoModifier
    if kind == "move":
        event = QMouseEvent(
            QEvent.Type.MouseMove, local, global_point, no_button, no_button, modifiers
        )
    elif kind == "press":
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress, local, global_point, left, left, modifiers
        )
    else:
        event = QMouseEvent(
            QEvent.Type.MouseButtonRelease, local, global_point, left, no_button, modifiers
        )
    QApplication.sendEvent(_qt_input_target(), event)


def _card_template_name() -> str:
    try:
        return str(mw.reviewer.card.template()["name"])
    except Exception:
        return "unknown"


def _start() -> None:
    try:
        if mw is None or mw.col is None:
            _fail("collection unavailable")
            return
        mw.resize(1150, 900)

        sing_ids = mw.col.find_cards("card:Sing")
        mw.col.sched.suspend_cards(sing_ids)
        _step("suspended sing cards", count=len(sing_ids))

        deck_id = mw.col.decks.id_for_name(DECK_NAME)
        if not deck_id:
            _fail(
                "deck not found",
                decks=[d.name for d in mw.col.decks.all_names_and_ids()],
            )
            return
        mw.col.decks.select(deck_id)
        mw.moveToState("review")
        _step("entered review")

        zoom_env = os.environ.get("SS_PROBE_ZOOM")
        if zoom_env:
            mw.reviewer.web.setZoomFactor(float(zoom_env))
            _step("zoom override", zoom=float(zoom_env))

        QTimer.singleShot(800, lambda: _poll_ready(0))
    except Exception:
        _fail("start failed", traceback_text=traceback.format_exc())


def _poll_ready(attempt: int) -> None:
    if attempt >= READY_POLLS:
        _fail(
            "editor never became ready",
            card_template=_card_template_name(),
        )
        return

    def _on_ready(data: Any) -> None:
        if not isinstance(data, dict) or not data.get("ready"):
            QTimer.singleShot(250, lambda: _poll_ready(attempt + 1))
            return
        _step("editor ready", attempts=attempt, point=data.get("point"))
        mw.reviewer.web.eval(JS_INSTALL_LOGGER)
        QTimer.singleShot(150, lambda: _aim_and_click(data["point"]))

    _eval_json(JS_READY, _on_ready)


def _aim_and_click(css_point: dict[str, float]) -> None:
    try:
        web = mw.reviewer.web
        zoom = float(web.zoomFactor())
        widget_x = round(float(css_point["x"]) * zoom)
        widget_y = round(float(css_point["y"]) * zoom)
        global_point = web.mapToGlobal(QPoint(widget_x, widget_y))
        gx, gy = global_point.x(), global_point.y()
        _report["aim"] = {
            "unit": AIM_UNIT,
            "pitch": AIM_PITCH,
            "css_point": css_point,
            "zoom": zoom,
            "widget_point": [widget_x, widget_y],
            "global_point": [gx, gy],
        }
        _report["qt_window"] = {
            "pos": [mw.pos().x(), mw.pos().y()],
            "size": [mw.width(), mw.height()],
        }
        try:
            window_ids = _xdotool("search", "--name", "Anki").splitlines()
            geometries = {}
            for window_id in window_ids[:6]:
                try:
                    geometries[window_id] = _xdotool(
                        "getwindowgeometry", "--shell", window_id
                    )
                except Exception as exc:
                    geometries[window_id] = f"error: {exc}"
            _report["x11_windows"] = geometries
        except Exception as exc:
            _report["x11_windows"] = f"error: {exc}"

        # Preferred path: real X11 input. Approach with cursor moves so
        # pointermove events fire on the overlay, then click in place.
        _xdotool("mousemove", "--sync", str(gx - 90), str(gy - 45))

        def _move2() -> None:
            _xdotool("mousemove", "--sync", str(gx - 30), str(gy - 15))
            QTimer.singleShot(80, _move3)

        def _move3() -> None:
            _xdotool("mousemove", "--sync", str(gx), str(gy))
            try:
                _report["cursor_after_moves"] = _xdotool(
                    "getmouselocation", "--shell"
                )
            except Exception as exc:
                _report["cursor_after_moves"] = f"error: {exc}"
            QTimer.singleShot(250, _check_x11_delivery)

        def _check_x11_delivery() -> None:
            def _on_count(value: Any) -> None:
                if isinstance(value, str) and value.isdigit() and int(value) > 0:
                    _report["input_method"] = "x11-xtest (xdotool)"
                    _xdotool("click", "1")
                    QTimer.singleShot(500, _collect)
                else:
                    # No WM in Xvfb: X delivers input, but QtWebEngine never
                    # processes it. Fall back to Qt-synthesized mouse events,
                    # which still exercise the Qt->Chromium coord transform.
                    _report["input_method"] = (
                        "qt-synthesized (x11 events not delivered to page)"
                    )
                    _qt_sequence()

            mw.reviewer.web.evalWithCallback(JS_LOG_LENGTH, _on_count)

        def _qt_sequence() -> None:
            _send_qt_mouse("move", widget_x - 90, widget_y - 45)
            QTimer.singleShot(
                60, lambda: _send_qt_mouse("move", widget_x - 30, widget_y - 15)
            )
            QTimer.singleShot(
                120, lambda: _send_qt_mouse("move", widget_x, widget_y)
            )
            QTimer.singleShot(
                220, lambda: _send_qt_mouse("press", widget_x, widget_y)
            )
            QTimer.singleShot(
                300, lambda: _send_qt_mouse("release", widget_x, widget_y)
            )
            QTimer.singleShot(800, _collect)

        QTimer.singleShot(80, _move2)
    except Exception:
        _fail("aim/click failed", traceback_text=traceback.format_exc())


def _collect() -> None:
    def _on_data(data: Any) -> None:
        try:
            log = data.get("log", []) if isinstance(data, dict) else []
            state = data.get("state") if isinstance(data, dict) else None
            events = (state or {}).get("events", [])

            moves = [e for e in log if e["type"] == "pointermove"]
            downs = [e for e in log if e["type"] == "pointerdown"]
            ups = [e for e in log if e["type"] == "pointerup"]

            placed_ok = (
                len(events) == 1
                and events[0].get("kind") == "note"
                and events[0].get("pitch") == AIM_PITCH
                and events[0].get("startUnit") == AIM_UNIT
            )

            coord_consistency = None
            if moves and downs:
                coord_consistency = {
                    "last_move": moves[-1],
                    "down": downs[0],
                    "up": ups[0] if ups else None,
                    "down_matches_move": abs(
                        moves[-1]["clientY"] - downs[0]["clientY"]
                    )
                    < 2.0,
                }

            heads = data.get("renderedNoteheads") or []
            refs = data.get("pitchRefY") or {}
            rendered_ok = False
            rendered_detail: dict[str, Any] = {}
            if heads and refs.get(AIM_PITCH) is not None:
                # The placed note is the leftmost notehead; ghost rests sit
                # further right.
                placed_head = min(heads, key=lambda h: h["x"])
                expected_y = float(refs[AIM_PITCH])
                rendered_ok = abs(float(placed_head["y"]) - expected_y) < 3.0
                rendered_detail = {
                    "notehead_y": placed_head["y"],
                    "expected_y": expected_y,
                    "pitch_ref_y": refs,
                }

            checks = [
                {"name": "pointermove events observed", "ok": len(moves) >= 2,
                 "count": len(moves)},
                {"name": "pointerdown and pointerup observed",
                 "ok": bool(downs and ups)},
                {"name": f"placed exactly one {AIM_PITCH} note at unit {AIM_UNIT}",
                 "ok": placed_ok, "events": events},
                {"name": f"rendered notehead sits on the {AIM_PITCH} line",
                 "ok": rendered_ok, **rendered_detail},
            ]

            extra_keys = (
                "renderedNoteheads",
                "pitchRefY",
                "scoreSvgCount",
                "editorCount",
                "storedAnswer",
            )
            introspection = {
                key: data.get(key)
                for key in extra_keys
                if isinstance(data, dict)
            }
            _write_result(
                {
                    "ok": all(c["ok"] for c in checks),
                    "checks": checks,
                    "pointer_log": log,
                    "coord_consistency": coord_consistency,
                    "editor_state": state,
                    "introspection": introspection,
                    "card_template": _card_template_name(),
                    "screenshot": _screenshot(),
                    **_report,
                }
            )
        except Exception:
            _fail("collect failed", traceback_text=traceback.format_exc())

    _eval_json(JS_COLLECT, _on_data)


def _boot() -> None:
    QTimer.singleShot(120_000, lambda: _fail("probe timed out"))
    QTimer.singleShot(SETTLE_MS, _start)


gui_hooks.main_window_did_init.append(_boot)
