/* global window, document, Vex */
(function () {
  "use strict";

  var DURATION_UNITS = {
    "8": 1,
    q: 2,
    h: 4,
    w: 8,
  };

  function scientificToVexKey(name) {
    var m = String(name).match(/^([A-Ga-g])([#b]?)(\d+)$/);
    if (!m) return "c/4";
    var letter = m[1].toLowerCase();
    var acc = m[2] || "";
    var oct = m[3];
    var accVex = acc === "#" ? "#" : acc === "b" ? "b" : "";
    return letter + accVex + "/" + oct;
  }

  function accidentalForPitch(name) {
    var m = String(name).match(/^([A-Ga-g])([#b]?)(\d+)$/);
    return m ? m[2] || "" : "";
  }

  function durationUnits(duration) {
    return DURATION_UNITS[String(duration || "")] || 0;
  }

  function normalizeEvent(event) {
    if (!event || typeof event !== "object") return null;
    var kind = event.kind === "rest" ? "rest" : "note";
    var duration = String(event.duration || "q");
    if (!durationUnits(duration)) return null;
    if (kind === "rest") {
      return {
        kind: "rest",
        duration: duration,
      };
    }
    if (!event.pitch) return null;
    return {
      kind: "note",
      pitch: String(event.pitch),
      duration: duration,
    };
  }

  function eventsFromBars(data) {
    if (!data || !Array.isArray(data.bars) || !data.bars.length) return [];
    var bar = data.bars[0];
    if (!bar || !Array.isArray(bar.events)) return [];
    var out = [];
    for (var i = 0; i < bar.events.length; i++) {
      var event = normalizeEvent(bar.events[i]);
      if (event) out.push(event);
    }
    return out;
  }

  function eventsFromLegacy(data) {
    var notes = (data && data.notes) || [];
    var durations = (data && data.durations) || [];
    var out = [];
    for (var i = 0; i < notes.length; i++) {
      var note = notes[i];
      var duration = String(durations[i] || "q");
      if (!durationUnits(duration)) continue;
      if (!note || note === "rest") {
        out.push({ kind: "rest", duration: duration });
      } else {
        out.push({
          kind: "note",
          pitch: String(note),
          duration: duration,
        });
      }
    }
    return out;
  }

  function normalizeData(data) {
    if (!data) return null;
    var events = eventsFromBars(data);
    if (!events.length) {
      events = eventsFromLegacy(data);
    }
    return {
      version: data.version || 1,
      clef: String(data.clef || "treble"),
      key: String(data.key || "C"),
      mode: String(data.mode || "major"),
      timeSig: String(data.timeSig || "4/4"),
      degrees: Array.isArray(data.degrees) ? data.degrees.slice() : [],
      events: events,
      notes: events
        .filter(function (event) {
          return event.kind === "note";
        })
        .map(function (event) {
          return event.pitch;
        }),
    };
  }

  function parseData() {
    var el = document.getElementById("melody-data");
    if (!el) return null;
    try {
      return normalizeData(JSON.parse(el.textContent.trim()));
    } catch (e) {
      return null;
    }
  }

  function fallbackNotation(container, data) {
    if (!container || !data || !data.events) return;
    var p = document.createElement("p");
    p.className = "ss-fallback";
    p.textContent = data.events
      .map(function (event) {
        if (event.kind === "rest") {
          return "rest-" + event.duration;
        }
        return event.pitch + "-" + event.duration;
      })
      .join(" ");
    container.appendChild(p);
  }

  function renderDegrees(container, data) {
    if (!container || !data || !data.degrees || !data.notes) return;
    var row = document.createElement("div");
    row.className = "ss-degrees";
    row.innerHTML =
      "<span class='ss-muted'>Scale degrees:</span> " +
      data.degrees.join(", ") +
      "<br><span class='ss-muted'>Notes:</span> " +
      data.notes.join(" ");
    container.appendChild(row);
  }

  function restKeyForClef(clef) {
    return clef === "bass" ? "d/3" : "b/4";
  }

  function vexNoteForEvent(VF, clef, event) {
    if (event.kind === "rest") {
      return new VF.StaveNote({
        clef: clef,
        keys: [restKeyForClef(clef)],
        duration: event.duration + "r",
      });
    }

    var note = new VF.StaveNote({
      clef: clef,
      keys: [scientificToVexKey(event.pitch)],
      duration: event.duration,
    });
    var accidental = accidentalForPitch(event.pitch);
    if (accidental) {
      note.addModifier(new VF.Accidental(accidental), 0);
    }
    return note;
  }

  function drawStaff(notationEl, data) {
    if (!notationEl || !data || !data.events || !data.events.length) return false;
    var VF = window.Vex && window.Vex.Flow;
    if (!VF) {
      fallbackNotation(notationEl, data);
      return false;
    }

    notationEl.innerHTML = "";
    var width = Math.min(520, window.innerWidth - 32);
    var height = 160;

    var renderer = new VF.Renderer(notationEl, VF.Renderer.Backends.SVG);
    renderer.resize(width, height);
    var ctx = renderer.getContext();

    var staveW = width - 24;
    var stave = new VF.Stave(12, 20, staveW);
    stave.addClef(data.clef || "treble").addTimeSignature(data.timeSig || "4/4");
    stave.setContext(ctx).draw();

    var notes = [];
    for (var i = 0; i < data.events.length; i++) {
      notes.push(vexNoteForEvent(VF, data.clef || "treble", data.events[i]));
    }

    try {
      if (VF.Formatter && VF.Formatter.FormatAndDraw) {
        VF.Formatter.FormatAndDraw(ctx, stave, notes);
      } else {
        var voice = new VF.Voice({ num_beats: 4, beat_value: 4 });
        voice.addTickables(notes);
        new VF.Formatter().joinVoices([voice]).format([voice], staveW - 30);
        voice.draw(ctx, stave);
      }
    } catch (err) {
      notationEl.innerHTML = "";
      fallbackNotation(notationEl, data);
      return false;
    }
    return true;
  }

  function run() {
    var data = parseData();
    var notationEl = document.getElementById("notation");
    if (!notationEl) return;

    if (!data) {
      notationEl.textContent = "(Invalid melody data)";
      return;
    }

    drawStaff(notationEl, data);

    var answerEl = document.getElementById("answer-info");
    if (answerEl) {
      answerEl.innerHTML = "";
      renderDegrees(answerEl, data);
    }
  }

  window.SightSingingParseData = parseData;
  window.SightSingingNormalizeData = normalizeData;
  window.SightSingingDrawStaff = drawStaff;
  window.SightSingingRenderDegrees = renderDegrees;
  window.SightSingingRedraw = run;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
})();
