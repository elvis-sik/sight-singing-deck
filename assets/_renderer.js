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

  /* ---- theme ------------------------------------------------------------ */

  function themeVar(name, fallback) {
    try {
      var value = window
        .getComputedStyle(document.body)
        .getPropertyValue(name)
        .trim();
      return value || fallback;
    } catch (e) {
      return fallback;
    }
  }

  function themeInk() {
    return themeVar("--ss-ink", "#221f1c");
  }

  /* ---- fallbacks ---------------------------------------------------------- */

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

  /* ---- meta chips ---------------------------------------------------------- */

  function renderMeta(container, data) {
    if (!container || !data) return;
    container.innerHTML = "";

    var badge = container.getAttribute("data-ss-badge");
    var chips = [];
    if (badge) {
      chips.push({ text: badge, badge: true });
    }
    var mode = data.mode === "minor" ? "minor" : "major";
    chips.push({ text: data.key + " " + mode });
    chips.push({ text: data.timeSig });
    chips.push({
      text: data.clef === "bass" ? "Bass clef" : "Treble clef",
    });

    for (var i = 0; i < chips.length; i++) {
      var chip = document.createElement("span");
      chip.className = "ss-chip" + (chips[i].badge ? " ss-chip-badge" : "");
      chip.textContent = chips[i].text;
      container.appendChild(chip);
    }
  }

  /* ---- scale degrees (Sing back) ------------------------------------------- */

  function renderDegrees(container, data) {
    if (!container || !data || !data.events) return;

    var wrap = document.createElement("div");
    wrap.className = "ss-degrees";

    var label = document.createElement("span");
    label.className = "ss-degrees-label";
    label.textContent = "Scale degrees";
    wrap.appendChild(label);

    var degreeIndex = 0;
    for (var i = 0; i < data.events.length; i++) {
      var event = data.events[i];
      var chip = document.createElement("span");
      chip.className = "ss-degree-chip";
      var num = document.createElement("span");
      num.className = "ss-degree-num";
      var note = document.createElement("span");
      note.className = "ss-degree-note";
      if (event.kind === "rest") {
        chip.className += " ss-degree-rest";
        num.textContent = "–";
        note.textContent = "rest";
      } else {
        num.textContent =
          degreeIndex < data.degrees.length
            ? String(data.degrees[degreeIndex])
            : "–";
        note.textContent = event.pitch;
        degreeIndex += 1;
      }
      chip.appendChild(num);
      chip.appendChild(note);
      wrap.appendChild(chip);
    }

    container.appendChild(wrap);
  }

  /* ---- engraving ------------------------------------------------------------ */

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

  /* Beam consecutive eighth NOTES that sit inside the same quarter beat. */
  function beamGroups(VF, events, notes) {
    var beams = [];
    var unit = 0;
    var group = [];

    function flush() {
      if (group.length >= 2) {
        try {
          beams.push(new VF.Beam(group));
        } catch (e) {}
      }
      group = [];
    }

    for (var i = 0; i < events.length; i++) {
      var event = events[i];
      var units = durationUnits(event.duration);
      var isEighthNote = event.kind === "note" && event.duration === "8";
      var startsBeat = unit % 2 === 0;

      if (isEighthNote) {
        if (startsBeat) flush();
        group.push(notes[i]);
      } else {
        flush();
      }
      unit += units;
      if (isEighthNote && unit % 2 === 0) flush();
    }
    flush();
    return beams;
  }

  /*
   * Draw one bar of events into `notationEl`.
   *
   * options:
   *   ink     - stroke/fill for staff furniture and default notes
   *   styles  - array (aligned with data.events) of per-note style objects
   *             ({ fillStyle, strokeStyle }) or null entries
   *   width   - explicit pixel width
   */
  function drawStaff(notationEl, data, options) {
    if (!notationEl || !data || !data.events || !data.events.length) return false;
    var opts = options || {};
    var VF = window.Vex && window.Vex.Flow;
    if (!VF) {
      fallbackNotation(notationEl, data);
      return false;
    }

    notationEl.innerHTML = "";
    var measured = notationEl.clientWidth || window.innerWidth - 40;
    var width = opts.width || Math.max(260, Math.min(520, measured));
    var height = 134;
    var ink = opts.ink || themeInk();

    var renderer = new VF.Renderer(notationEl, VF.Renderer.Backends.SVG);
    renderer.resize(width, height);
    var ctx = renderer.getContext();
    ctx.setFillStyle(ink);
    ctx.setStrokeStyle(ink);

    var staveW = width - 16;
    var staffInk = opts.staffInk || themeVar("--ss-ink-soft", "#6f6a63");
    var stave = new VF.Stave(8, 14, staveW);
    stave.addClef(data.clef || "treble").addTimeSignature(data.timeSig || "4/4");
    stave.setStyle({ fillStyle: staffInk, strokeStyle: staffInk });
    stave.setContext(ctx).draw();

    var notes = [];
    for (var i = 0; i < data.events.length; i++) {
      var note = vexNoteForEvent(VF, data.clef || "treble", data.events[i]);
      var style = opts.styles && opts.styles[i];
      if (style) {
        note.setStyle(style);
        if (note.setLedgerLineStyle) note.setLedgerLineStyle(style);
        if (note.setStemStyle && !note.isRest()) note.setStemStyle(style);
        if (note.setFlagStyle && !note.isRest()) note.setFlagStyle(style);
      }
      notes.push(note);
    }

    var beams = beamGroups(VF, data.events, notes);

    try {
      VF.Formatter.FormatAndDraw(ctx, stave, notes);
      for (var b = 0; b < beams.length; b++) {
        beams[b].setContext(ctx).draw();
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
    var metaEl = document.getElementById("melody-meta");

    if (metaEl && data) {
      renderMeta(metaEl, data);
    }

    if (notationEl) {
      if (!data) {
        notationEl.textContent = "(Invalid melody data)";
      } else {
        drawStaff(notationEl, data);
      }
    }

    var answerEl = document.getElementById("answer-info");
    if (answerEl && data) {
      answerEl.innerHTML = "";
      renderDegrees(answerEl, data);
    }
  }

  function vexReady() {
    return !!(window.Vex && window.Vex.Flow);
  }

  /*
   * Draw once VexFlow is available. Anki (and AnkiMobile especially)
   * re-executes the card's <script src> tags as dynamically-created
   * nodes, which load ASYNCHRONOUSLY and out of order — so this renderer
   * can run before _vexflow_*.js has finished. Polling for Vex before we
   * draw means the notation still appears regardless of load order,
   * instead of silently falling back to text (or nothing). Falls back
   * after ~5s so a genuinely missing bundle still degrades gracefully.
   */
  function runWhenReady() {
    if (vexReady()) {
      run();
      return;
    }
    var tries = 0;
    var timer = setInterval(function () {
      tries += 1;
      if (vexReady() || tries > 200) {
        clearInterval(timer);
        run();
      }
    }, 25);
  }

  var resizeTimer = null;
  window.addEventListener("resize", function () {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(run, 150);
  });

  window.SightSingingParseData = parseData;
  window.SightSingingNormalizeData = normalizeData;
  window.SightSingingDrawStaff = drawStaff;
  window.SightSingingRenderDegrees = renderDegrees;
  window.SightSingingThemeVar = themeVar;
  window.SightSingingRedraw = runWhenReady;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", runWhenReady);
  } else {
    runWhenReady();
  }
})();
