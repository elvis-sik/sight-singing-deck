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

  /* A duration may carry a trailing "d" for dotted (e.g. "qd", "hd"). */
  function splitDuration(duration) {
    var s = String(duration || "");
    var dotted = s.charAt(s.length - 1) === "d";
    return { base: dotted ? s.slice(0, -1) : s, dotted: dotted };
  }

  function durationUnits(duration) {
    var d = splitDuration(duration);
    var base = DURATION_UNITS[d.base] || 0;
    return d.dotted ? base * 1.5 : base;
  }

  /* Duration units in one measure of the given time signature (a 4/4 bar is 8
     units: four quarters at 2 units each). Returns 0 for an unparseable sig,
     which the caller reads as "don't split into measures". */
  function measureUnits(timeSig) {
    var parts = String(timeSig || "4/4").split("/");
    var num = parseInt(parts[0], 10);
    var den = parseInt(parts[1], 10);
    if (!num || !den) return 0;
    return num * (8 / den);
  }

  /* Greedy decomposition of `units` into rest durations (largest first), used to
     pad an incomplete final measure so every bar is rhythmically complete. */
  function fillRestDurations(units) {
    var table = [["w", 8], ["hd", 6], ["h", 4], ["qd", 3], ["q", 2], ["8", 1]];
    var out = [];
    var left = units;
    for (var i = 0; i < table.length && left > 0; i++) {
      while (left >= table[i][1]) {
        out.push(table[i][0]);
        left -= table[i][1];
      }
    }
    return out;
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
        tuplet: !!event.tuplet,
      };
    }
    if (!event.pitch) return null;
    return {
      kind: "note",
      pitch: String(event.pitch),
      duration: duration,
      tie: !!event.tie,       // tied to the following note (same pitch)
      tuplet: !!event.tuplet, // member of a 3-in-2 triplet group
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
      gradeMode: data.gradeMode ? String(data.gradeMode) : "",
      keySig: data.keySig ? String(data.keySig) : "",
      keyAcc: data.keyAccidentals && typeof data.keyAccidentals === "object"
        ? data.keyAccidentals
        : {},
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

    // Rhythm cards override the template's badge; otherwise use the card's own.
    var badge =
      data.gradeMode === "rhythm" || data.gradeMode === "sounded"
        ? "Rhythm"
        : container.getAttribute("data-ss-badge");
    var chips = [];
    if (badge) {
      chips.push({ text: badge, badge: true });
    }
    // Modes are "major" / "natural_minor" / "harmonic_minor" — match any minor
    // (the old `=== "minor"` never matched, so minor cards mislabelled as major).
    var mode = /minor/.test(String(data.mode)) ? "minor" : "major";
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
    // Rhythm cards carry no scale degrees — skip the whole section.
    if (!data.degrees || !data.degrees.length) return;

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

  function noteLetter(name) {
    var m = String(name).match(/^([A-Ga-g])/);
    return m ? m[1].toUpperCase() : "";
  }

  function addDot(VF, note) {
    // VexFlow moved the dot API around between versions; try each.
    if (VF.Dot && typeof VF.Dot.buildAndAttach === "function") {
      VF.Dot.buildAndAttach([note], { all: true });
    } else if (typeof note.addDotToAll === "function") {
      note.addDotToAll();
    } else if (typeof note.addDot === "function") {
      note.addDot(0);
    }
  }

  function vexNoteForEvent(VF, clef, event, keyAcc) {
    var d = splitDuration(event.duration);
    if (event.kind === "rest") {
      var rest = new VF.StaveNote({
        clef: clef,
        keys: [restKeyForClef(clef)],
        duration: d.base + "r",
      });
      if (d.dotted) addDot(VF, rest);
      return rest;
    }

    var note = new VF.StaveNote({
      clef: clef,
      keys: [scientificToVexKey(event.pitch)],
      duration: d.base,
    });
    if (d.dotted) addDot(VF, note);
    // Draw an accidental only where the note deviates from the key signature:
    // matching the key sig -> no glyph; a natural against a sharp/flat key ->
    // an explicit natural; anything else -> the sharp/flat glyph.
    var acc = accidentalForPitch(event.pitch); // "", "#", or "b"
    var accVal = acc === "#" ? 1 : acc === "b" ? -1 : 0;
    var keyVal = (keyAcc && keyAcc[noteLetter(event.pitch)]) || 0;
    if (accVal !== keyVal) {
      var glyph = accVal === 0 ? "n" : acc;
      note.addModifier(new VF.Accidental(glyph), 0);
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
      // Triplet members are beamed separately (with their tuplet); skip here.
      var isEighthNote =
        event.kind === "note" && event.duration === "8" && !event.tuplet;
      var startsBeat = unit % 2 === 0;

      if (event.tuplet) {
        flush();
      } else if (isEighthNote) {
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

  /* Group consecutive triplet members into 3-note tuplets (+ their beams). */
  function tupletGroups(VF, events, notes) {
    var tuplets = [];
    var beams = [];
    var group = [];

    function flush() {
      if (group.length) {
        try {
          tuplets.push(new VF.Tuplet(group, { num_notes: 3, notes_occupied: 2 }));
          if (group.length >= 2) beams.push(new VF.Beam(group));
        } catch (e) {}
      }
      group = [];
    }

    for (var i = 0; i < events.length; i++) {
      if (events[i].tuplet) {
        group.push(notes[i]);
        if (group.length === 3) flush();
      } else {
        flush();
      }
    }
    flush();
    return { tuplets: tuplets, beams: beams };
  }

  /* Ties: connect each tied note to the next (same pitch). */
  function tieGroups(VF, events, notes) {
    var ties = [];
    for (var i = 0; i < events.length - 1; i++) {
      if (events[i].tie && events[i].kind === "note") {
        try {
          ties.push(
            new VF.StaveTie({
              first_note: notes[i],
              last_note: notes[i + 1],
              first_indices: [0],
              last_indices: [0],
            })
          );
        } catch (e) {}
      }
    }
    return ties;
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

    // Size height + stave y from the pitch span so high/low notes and their ledger
    // lines aren't clipped (the same fossil the editor had; VexFlow reserves ~40px
    // above the top line). Stays 134px / y=14 for a normal in-staff melody; grows
    // only when notes stray far above/below the staff.
    var _clef = data.clef || "treble";
    function _ord(p) {
      var s = String(p);
      var oc = parseInt(s.replace(/[^0-9-]/g, ""), 10);
      return (isNaN(oc) ? 4 : oc) * 7 + "CDEFGAB".indexOf(s.charAt(0).toUpperCase());
    }
    var _refBot = _clef === "bass" ? _ord("G2") : _ord("E4");
    var _refTop = _clef === "bass" ? _ord("A3") : _ord("F5");
    var _lo = _refBot, _hi = _refTop;
    for (var _e = 0; _e < data.events.length; _e++) {
      var _ev = data.events[_e];
      if (_ev.kind !== "rest" && _ev.pitch) {
        var _o = _ord(_ev.pitch);
        if (_o < _lo) _lo = _o;
        if (_o > _hi) _hi = _o;
      }
    }
    var staveY = 14 + Math.max(0, (_hi - _refTop) * 5 - 6);
    var height = Math.max(134, staveY + 80 + Math.max(0, _refBot - _lo) * 5 + 20);
    var ink = opts.ink || themeInk();

    var renderer = new VF.Renderer(notationEl, VF.Renderer.Backends.SVG);
    renderer.resize(width, height);
    var ctx = renderer.getContext();
    ctx.setFillStyle(ink);
    ctx.setStrokeStyle(ink);

    var staveW = width - 16;
    var staffInk = opts.staffInk || themeVar("--ss-ink-soft", "#6f6a63");
    var stave = new VF.Stave(8, staveY, staveW);
    stave.addClef(data.clef || "treble");
    if (data.keySig) {
      try {
        stave.addKeySignature(data.keySig);
      } catch (e) {}
    }
    stave.addTimeSignature(data.timeSig || "4/4");
    stave.setStyle({ fillStyle: staffInk, strokeStyle: staffInk });
    stave.setContext(ctx).draw();

    var notes = [];
    for (var i = 0; i < data.events.length; i++) {
      var note = vexNoteForEvent(
        VF, data.clef || "treble", data.events[i], data.keyAcc
      );
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
    var tup = tupletGroups(VF, data.events, notes);
    var ties = tieGroups(VF, data.events, notes);

    // Split into complete measures: insert a barline at each measure boundary
    // and pad the final (partial) bar with rests, so a phrase longer than one
    // bar reads as real barred measures and a short phrase never leaves empty
    // beats. Boundaries fall between events for our data (quarter/half notes
    // divide the bar evenly). `notes[i]` still carries per-event styling and is
    // referenced by the beam/tuplet/tie groups, so those are unaffected.
    var barUnits = measureUnits(data.timeSig);
    var tickables = [];
    var acc = 0;
    for (var ti = 0; ti < data.events.length; ti++) {
      if (barUnits && acc > 0 && acc % barUnits === 0) {
        tickables.push(new VF.BarNote());
      }
      tickables.push(notes[ti]);
      acc += durationUnits(data.events[ti].duration);
    }
    if (barUnits && acc % barUnits !== 0) {
      var restDurs = fillRestDurations(barUnits - (acc % barUnits));
      for (var ri = 0; ri < restDurs.length; ri++) {
        tickables.push(
          vexNoteForEvent(VF, data.clef || "treble",
            { kind: "rest", duration: restDurs[ri] }, {})
        );
      }
    }

    try {
      VF.Formatter.FormatAndDraw(ctx, stave, tickables);
      for (var b = 0; b < beams.length; b++) {
        beams[b].setContext(ctx).draw();
      }
      for (var tb = 0; tb < tup.beams.length; tb++) {
        tup.beams[tb].setContext(ctx).draw();
      }
      for (var t = 0; t < tup.tuplets.length; t++) {
        tup.tuplets[t].setContext(ctx).draw();
      }
      for (var y = 0; y < ties.length; y++) {
        ties[y].setContext(ctx).draw();
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
