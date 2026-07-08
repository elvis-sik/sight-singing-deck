/* global window, document, localStorage, Vex */
(function () {
  "use strict";

  /* ---- music model ------------------------------------------------------- */

  // The editor works in letter+octave STAFF POSITIONS (no accidentals — the key
  // signature supplies those). `PITCHES` is the placeable range; it is rebuilt
  // per melody from the target's span (and the clef) in initFront/renderSummary,
  // so the editor is no longer locked to one treble octave. Default keeps the
  // historical treble C4–C5 window.
  var PITCHES = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"];
  var clef = "treble";
  // Tonal/metric context of the current target, captured in applyPitchContext so
  // the editor staff and the back-side answer staff match the target instead of a
  // hardcoded C-major/4-4. (No-op for the all-natural x/4 cards shipped today.)
  var curKey = "C";
  var curMode = "major";
  var curTimeSig = "4/4";
  var curKeySig = "";
  var LETTERS = "CDEFGAB";

  // Diatonic ordinal: octave*7 + letter index, ignoring any accidental. Adjacent
  // ordinals are adjacent staff positions (a line/space step).
  function ordinalOf(pitch) {
    var p = String(pitch);
    var oct = parseInt(p.replace(/[^0-9-]/g, ""), 10);
    return (isNaN(oct) ? 4 : oct) * 7 + LETTERS.indexOf(p.charAt(0).toUpperCase());
  }
  function pitchFromOrdinal(ord) {
    return LETTERS.charAt(((ord % 7) + 7) % 7) + Math.floor(ord / 7);
  }
  // Staff bottom line (VexFlow line 4) and top line (line 0) pitch, per clef.
  function clefBottomOrdinal() {
    return clef === "bass" ? ordinalOf("G2") : ordinalOf("E4");
  }
  function clefTopOrdinal() {
    return clef === "bass" ? ordinalOf("A3") : ordinalOf("F5");
  }
  // Build the placeable pitch list spanning the target melody (padded a step),
  // always covering the staff itself so an empty staff still looks normal.
  function buildPitches(events, cl) {
    var prev = clef;
    clef = cl;
    var lo = clefBottomOrdinal();
    var hi = clefTopOrdinal();
    for (var i = 0; i < events.length; i++) {
      if (events[i].kind === "note" && events[i].pitch) {
        var o = ordinalOf(events[i].pitch);
        if (o < lo) lo = o;
        if (o > hi) hi = o;
      }
    }
    lo -= 1;
    hi += 1;
    clef = prev;
    var out = [];
    for (var ord = lo; ord <= hi; ord++) out.push(pitchFromOrdinal(ord));
    return out;
  }
  // Neutral rest staff position (middle line) per clef, as a VexFlow key.
  function restKey() {
    return clef === "bass" ? "d/3" : "b/4";
  }

  var BAR_UNITS = 8; // eighth-note units in one 4/4 bar
  // The editor's working length in eighth-units. It equals the target melody's
  // total length (beat-aligned), so a 4-quarter melody keeps the historical
  // single-bar behaviour (capacity === BAR_UNITS) while a 5-/6-note phrase lays
  // out as one longer staff. Set from the target in initFront/renderSummary.
  var capacity = BAR_UNITS;
  var DURATION_UNITS = { "8": 1, q: 2, h: 4, w: 8 };
  var DURATION_ORDER = ["w", "h", "q", "8"];
  var DURATION_LABELS = { "8": "Eighth", q: "Quarter", h: "Half", w: "Whole" };

  var state = {
    mode: "note", // note | rest | erase
    duration: "q",
    events: [],
    history: [],
  };

  /* Geometry captured after each VexFlow render. */
  var geo = null;
  var hover = null;

  function isBack() {
    return !!document.getElementById("back");
  }

  function parseData() {
    if (window.SightSingingParseData) {
      return window.SightSingingParseData();
    }
    return null;
  }

  function themeVar(name, fallback) {
    if (window.SightSingingThemeVar) {
      return window.SightSingingThemeVar(name, fallback);
    }
    return fallback;
  }

  function melodyId() {
    var explicit = String(window.sightSingingMelodyId || "").trim();
    if (explicit) return explicit;
    // Fall back to a hash of the melody data so two id-less cards don't collide
    // on the same "ss-transcribe:unknown" saved-answer key (djb2).
    var el = document.getElementById("melody-data");
    var raw = el ? el.textContent : "";
    var h = 5381;
    for (var i = 0; i < raw.length; i++) h = ((h << 5) + h + raw.charCodeAt(i)) | 0;
    return "auto" + (h >>> 0).toString(36);
  }

  function storageKey() {
    return "ss-transcribe:" + melodyId();
  }

  function durationUnits(duration) {
    return DURATION_UNITS[String(duration || "")] || 0;
  }

  function eventUnits(event) {
    return durationUnits(event.duration);
  }

  function eventEndUnit(event) {
    return event.startUnit + eventUnits(event);
  }

  function occupiedUnits(events) {
    var occupied = [];
    for (var u = 0; u < capacity; u++) occupied.push(false);
    for (var i = 0; i < events.length; i++) {
      var end = eventEndUnit(events[i]);
      for (var unit = events[i].startUnit; unit < end; unit++) {
        if (unit >= 0 && unit < capacity) occupied[unit] = true;
      }
    }
    return occupied;
  }

  function durationFitsAt(startUnit, duration, occupied) {
    var units = durationUnits(duration);
    if (!units) return false;
    if (startUnit < 0 || startUnit + units > capacity) return false;
    if (startUnit % units !== 0) return false;
    for (var i = startUnit; i < startUnit + units; i++) {
      if (occupied[i]) return false;
    }
    return true;
  }

  function cloneEvent(event) {
    if (!event) return null;
    return {
      kind: event.kind === "rest" ? "rest" : "note",
      duration: String(event.duration || "q"),
      startUnit: Number(event.startUnit || 0),
      pitch: event.kind === "rest" ? null : String(event.pitch || "C4"),
    };
  }

  function normalizedEvent(event) {
    var cloned = cloneEvent(event);
    if (!cloned) return null;
    var empty = occupiedUnits([]);
    if (!durationFitsAt(cloned.startUnit, cloned.duration, empty)) return null;
    if (cloned.kind === "note" && PITCHES.indexOf(cloned.pitch) < 0) return null;
    return cloned;
  }

  function normalizeStoredEvents(value) {
    if (!Array.isArray(value)) return [];
    var out = [];
    for (var i = 0; i < value.length; i++) {
      var event = normalizedEvent(value[i]);
      if (event) out.push(event);
    }
    out.sort(function (a, b) {
      return a.startUnit - b.startUnit;
    });
    return out;
  }

  function loadSavedEvents() {
    try {
      var raw = localStorage.getItem(storageKey());
      if (!raw) return [];
      return normalizeStoredEvents(JSON.parse(raw));
    } catch (e) {
      return [];
    }
  }

  function saveEvents() {
    try {
      localStorage.setItem(storageKey(), JSON.stringify(state.events));
    } catch (e) {}
  }

  function clearSavedEvents() {
    try {
      localStorage.removeItem(storageKey());
    } catch (e) {}
  }

  function sortEvents() {
    state.events.sort(function (a, b) {
      return a.startUnit - b.startUnit;
    });
  }

  function usedUnits() {
    var total = 0;
    for (var i = 0; i < state.events.length; i++) {
      total += eventUnits(state.events[i]);
    }
    return total;
  }

  function eventIndexAtUnit(unit) {
    for (var i = 0; i < state.events.length; i++) {
      if (
        state.events[i].startUnit <= unit &&
        eventEndUnit(state.events[i]) > unit
      ) {
        return i;
      }
    }
    return -1;
  }

  /* Decompose the free space into displayable placeholder chunks. */
  function freeChunks() {
    var occupied = occupiedUnits(state.events);
    var cursor = 0;
    var out = [];
    while (cursor < capacity) {
      if (occupied[cursor]) {
        cursor += 1;
        continue;
      }
      var chosen = "8";
      for (var i = 0; i < DURATION_ORDER.length; i++) {
        if (durationFitsAt(cursor, DURATION_ORDER[i], occupied)) {
          chosen = DURATION_ORDER[i];
          break;
        }
      }
      out.push({ startUnit: cursor, duration: chosen });
      cursor += durationUnits(chosen);
    }
    return out;
  }

  /* Valid start units for the currently selected duration. */
  function validStarts() {
    var occupied = occupiedUnits(state.events);
    var step = durationUnits(state.duration);
    var out = [];
    for (var start = 0; start + step <= capacity; start += step) {
      if (durationFitsAt(start, state.duration, occupied)) out.push(start);
    }
    return out;
  }

  function pushHistory() {
    state.history.push(state.events.map(cloneEvent));
    if (state.history.length > 60) state.history.shift();
  }

  /* ---- target / validation ------------------------------------------------ */

  function targetEventsFromData(data) {
    if (!data || !Array.isArray(data.events)) return [];
    var cursor = 0;
    var out = [];
    for (var i = 0; i < data.events.length; i++) {
      var source = data.events[i];
      var units = durationUnits(source.duration);
      if (!units) return [];
      out.push({
        kind: source.kind === "rest" ? "rest" : "note",
        pitch: source.kind === "rest" ? null : source.pitch,
        duration: String(source.duration),
        startUnit: cursor,
      });
      cursor += units;
    }
    // Any well-formed melody is accepted (was: exactly one 4/4 bar). Longer
    // phrases lay out across more beats; `capacity` (set below) sizes the grid.
    return out;
  }

  // The editor grid spans the target melody's full length, beat-aligned. A
  // 4-quarter melody keeps capacity === BAR_UNITS (unchanged single-bar layout);
  // a 5-/6-note phrase gets a proportionally longer staff. Falls back to one bar
  // for an empty/absent target.
  function capacityForData(data) {
    var events = targetEventsFromData(data);
    var total = 0;
    for (var i = 0; i < events.length; i++) {
      total += durationUnits(events[i].duration);
    }
    if (total <= 0) return BAR_UNITS;
    if (total % 2 === 1) total += 1; // keep a whole number of beats
    return total;
  }

  function supportedData(data) {
    if (!data) return false;
    if (["treble", "bass"].indexOf(String(data.clef || "treble")) < 0) return false;
    return targetEventsFromData(data).length > 0;
  }

  // Size the pitch window + clef from the target before rendering/loading, so the
  // editor covers the melody (any octave, treble or bass) rather than a fixed
  // treble C4–C5.
  function applyPitchContext(data) {
    clef = String((data && data.clef) || "treble");
    curKey = String((data && data.key) || "C");
    curMode = String((data && data.mode) || "major");
    curTimeSig = String((data && data.timeSig) || "4/4");
    curKeySig = String((data && data.keySig) || "");
    PITCHES = buildPitches(targetEventsFromData(data), clef);
  }

  function buildAnswerData() {
    return {
      version: 2,
      clef: clef,
      key: curKey,
      mode: curMode,
      timeSig: curTimeSig,
      keySig: curKeySig,
      events: state.events.map(function (event) {
        if (event.kind === "rest") {
          return { kind: "rest", duration: event.duration };
        }
        return { kind: "note", pitch: event.pitch, duration: event.duration };
      }),
    };
  }

  function eventsMatch(userEvent, targetEvent) {
    return (
      !!targetEvent &&
      userEvent.kind === targetEvent.kind &&
      userEvent.startUnit === targetEvent.startUnit &&
      userEvent.duration === targetEvent.duration &&
      // Compare by STAFF POSITION, not pitch string: the editor only lets the
      // student express a letter+octave line/space (the key signature supplies
      // the accidental), so a target of "F#4" must match a placed "F4" on the F
      // line. ordinalOf strips accidentals to the diatonic position. (For the
      // all-natural melodies shipped today this is identical to === .)
      (userEvent.kind === "rest" ||
        ordinalOf(userEvent.pitch) === ordinalOf(targetEvent.pitch))
    );
  }

  /* ---- svg helpers --------------------------------------------------------- */

  var SVG_NS = "http://www.w3.org/2000/svg";

  function svgEl(tag, attrs, parent) {
    var el = document.createElementNS(SVG_NS, tag);
    for (var key in attrs) {
      if (Object.prototype.hasOwnProperty.call(attrs, key)) {
        el.setAttribute(key, String(attrs[key]));
      }
    }
    if (parent) parent.appendChild(el);
    return el;
  }

  /* ---- toolbar icons -------------------------------------------------------- */

  function noteIconSvg(duration) {
    var stem =
      duration === "w"
        ? ""
        : '<rect x="15.1" y="5" width="1.9" height="17.5" rx="0.9"/>';
    var flag =
      duration === "8"
        ? '<path d="M17 5 C 20.8 8.2, 21.6 12.4, 18.6 16.6 C 20.4 11.8, 18.6 9.6, 17 9.2 Z"/>'
        : "";
    var head;
    if (duration === "w") {
      head =
        '<ellipse cx="12" cy="22.4" rx="6.4" ry="4.3" fill="none" stroke-width="2.6" stroke="currentColor"/>';
    } else if (duration === "h") {
      head =
        '<ellipse cx="11" cy="22.6" rx="5.1" ry="3.7" fill="none" stroke-width="2.4" stroke="currentColor" transform="rotate(-16 11 22.6)"/>';
    } else {
      head =
        '<ellipse cx="11" cy="22.6" rx="5.2" ry="3.8" transform="rotate(-16 11 22.6)"/>';
    }
    return (
      '<svg viewBox="0 0 24 30" aria-hidden="true">' + head + stem + flag + "</svg>"
    );
  }

  function restIconSvg(duration) {
    var body;
    if (duration === "w") {
      body =
        '<rect x="4.5" y="12.4" width="15" height="1.7" rx="0.8"/>' +
        '<rect x="7.6" y="14.1" width="8.8" height="4.6" rx="1"/>';
    } else if (duration === "h") {
      body =
        '<rect x="4.5" y="16.4" width="15" height="1.7" rx="0.8"/>' +
        '<rect x="7.6" y="11.8" width="8.8" height="4.6" rx="1"/>';
    } else if (duration === "q") {
      body =
        '<path d="M10.2 5.5 L15.2 11.4 C 12.8 13.4, 12.6 15.2, 15.4 18.2 C 11.2 17.2, 10 19.4, 12.4 22.8 C 7.6 21, 7.6 17, 10.8 15.6 C 8.2 12.8, 8.4 9.6, 10.2 5.5 Z"/>';
    } else {
      body =
        '<circle cx="9.2" cy="11.2" r="2.5"/>' +
        '<path d="M9.4 13.4 C 12.4 14.8, 14.6 14.2, 16.6 12.2 L 13.2 24.6 L 11.4 24.6 L 14.4 15.4 C 12.6 16.2, 10.6 15.8, 9.4 13.4 Z"/>';
    }
    return '<svg viewBox="0 0 24 30" aria-hidden="true">' + body + "</svg>";
  }

  function undoIconSvg() {
    return (
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12.5 4.5 C 17 4.5, 20.5 8, 20.5 12.4 C 20.5 16.9, 17 20.4, 12.5 20.4 L 10 20.4 L 10 18 L 12.5 18 C 15.7 18, 18.1 15.5, 18.1 12.4 C 18.1 9.3, 15.7 6.9, 12.5 6.9 L 8.6 6.9 L 11.4 9.7 L 9.7 11.4 L 4 5.7 L 9.7 0 L 11.4 1.7 L 8.6 4.5 Z" transform="translate(0 2)"/></svg>'
    );
  }

  function clearIconSvg() {
    return (
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3 L15 3 L15 5 L20 5 L20 7 L4 7 L4 5 L9 5 Z"/><path d="M6 9 L18 9 L17 21 L7 21 Z"/></svg>'
    );
  }

  function eraseIconSvg() {
    return (
      '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15.5 3.5 L21 9 L12.5 17.5 L7 17.5 L3 13.5 L11.5 5 Z M6.2 12.4 L9.1 15.3 L11 13.4 L8.1 10.5 Z"/><rect x="3" y="19.5" width="18" height="2" rx="1"/></svg>'
    );
  }

  /* ---- UI construction -------------------------------------------------------- */

  function buildButton(id, className, html, onTap) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.id = id;
    btn.className = className;
    btn.innerHTML = html;
    btn.addEventListener("click", function (event) {
      event.preventDefault();
      onTap();
    });
    return btn;
  }

  function buildUI() {
    var ui = document.getElementById("transcribe-ui");
    if (!ui) return;
    ui.innerHTML = "";

    var durbar = document.createElement("div");
    durbar.className = "ss-toolbar ss-durbar";
    durbar.id = "transcribe-durbar";
    var durations = ["8", "q", "h", "w"];
    for (var i = 0; i < durations.length; i++) {
      (function (duration) {
        var btn = buildButton(
          "transcribe-duration-" + duration,
          "ss-btn ss-btn-duration",
          "",
          function () {
            window.SightSingingTranscriptionSetDuration(duration);
          }
        );
        btn.setAttribute("data-transcribe-duration", duration);
        durbar.appendChild(btn);
      })(durations[i]);
    }
    ui.appendChild(durbar);

    var tools = document.createElement("div");
    tools.className = "ss-toolbar";

    var seg = document.createElement("div");
    seg.className = "ss-segmented";
    var segDefs = [
      { tool: "note", label: "Notes", icon: noteIconSvg("q") },
      { tool: "rest", label: "Rests", icon: restIconSvg("q") },
      { tool: "erase", label: "Erase", icon: eraseIconSvg() },
    ];
    for (var j = 0; j < segDefs.length; j++) {
      (function (def) {
        var btn = buildButton(
          "transcribe-tool-" + def.tool,
          "ss-btn",
          def.icon + "<span>" + def.label + "</span>",
          function () {
            window.SightSingingTranscriptionSetTool(def.tool);
          }
        );
        btn.setAttribute("data-transcribe-tool", def.tool);
        seg.appendChild(btn);
      })(segDefs[j]);
    }
    tools.appendChild(seg);

    tools.appendChild(
      buildButton(
        "transcribe-undo",
        "ss-btn",
        undoIconSvg() + "<span>Undo</span>",
        function () {
          window.SightSingingTranscriptionUndo();
        }
      )
    );
    tools.appendChild(
      buildButton(
        "transcribe-reset",
        "ss-btn",
        clearIconSvg() + "<span>Clear</span>",
        function () {
          window.SightSingingTranscriptionReset();
        }
      )
    );
    ui.appendChild(tools);

    var statusRow = document.createElement("div");
    statusRow.className = "ss-status-row";
    var beatbar = document.createElement("div");
    beatbar.className = "ss-beatbar";
    beatbar.id = "transcribe-beatbar";
    var nbeats = Math.max(1, Math.ceil(capacity / 2));
    for (var b = 0; b < nbeats; b++) {
      var beat = document.createElement("div");
      beat.className = "ss-beat";
      var fill = document.createElement("div");
      fill.className = "ss-beat-fill";
      beat.appendChild(fill);
      beatbar.appendChild(beat);
    }
    statusRow.appendChild(beatbar);
    var status = document.createElement("div");
    status.className = "ss-status";
    status.id = "transcribe-status";
    statusRow.appendChild(status);
    ui.appendChild(statusRow);
  }

  function updateToolbar() {
    var tools = ["note", "rest", "erase"];
    for (var i = 0; i < tools.length; i++) {
      var toolBtn = document.getElementById("transcribe-tool-" + tools[i]);
      if (toolBtn) {
        toolBtn.className =
          "ss-btn" + (state.mode === tools[i] ? " ss-tool-active" : "");
      }
    }

    var durbar = document.getElementById("transcribe-durbar");
    if (durbar) {
      durbar.className =
        "ss-toolbar ss-durbar" +
        (state.mode === "erase" ? " ss-durbar-disabled" : "");
    }

    var durations = ["8", "q", "h", "w"];
    for (var j = 0; j < durations.length; j++) {
      var duration = durations[j];
      var btn = document.getElementById("transcribe-duration-" + duration);
      if (!btn) continue;
      btn.className =
        "ss-btn ss-btn-duration" +
        (state.duration === duration ? " ss-tool-active" : "");
      var icon =
        state.mode === "rest" ? restIconSvg(duration) : noteIconSvg(duration);
      btn.innerHTML =
        icon +
        '<span class="ss-btn-caption">' +
        DURATION_LABELS[duration] +
        "</span>";
    }

    var undoBtn = document.getElementById("transcribe-undo");
    if (undoBtn) undoBtn.disabled = !state.history.length;
    var resetBtn = document.getElementById("transcribe-reset");
    if (resetBtn) resetBtn.disabled = !state.events.length;
  }

  /* ---- status + beat bar --------------------------------------------------------- */

  function beatsLabel(units) {
    var whole = Math.floor(units / 2);
    var half = units % 2 === 1;
    if (whole === 0 && half) return "½";
    return String(whole) + (half ? "½" : "");
  }

  function updateStatus() {
    var el = document.getElementById("transcribe-status");
    var used = usedUnits();

    var nbeats = Math.max(1, Math.ceil(capacity / 2));
    if (el) {
      if (!state.events.length) {
        el.innerHTML = "Listen, then tap the staff to enter what you hear.";
      } else if (used >= capacity) {
        el.innerHTML =
          "<strong>All " +
          nbeats +
          " beats filled.</strong> Check it against the melody, then show the answer.";
      } else {
        el.innerHTML =
          "<strong>" +
          beatsLabel(used) +
          " of " +
          nbeats +
          " beats</strong> filled · " +
          DURATION_LABELS[state.duration].toLowerCase() +
          (state.mode === "rest" ? " rest" : "") +
          " selected";
      }
    }

    var beatbar = document.getElementById("transcribe-beatbar");
    if (beatbar) {
      beatbar.className =
        "ss-beatbar" + (used >= capacity ? " ss-beatbar-full" : "");
      var occupied = occupiedUnits(state.events);
      var fills = beatbar.getElementsByClassName("ss-beat-fill");
      for (var b = 0; b < fills.length && b < nbeats; b++) {
        var count = (occupied[b * 2] ? 1 : 0) + (occupied[b * 2 + 1] ? 1 : 0);
        fills[b].style.width = count * 50 + "%";
      }
    }
  }

  /* ---- VexFlow editor rendering ---------------------------------------------------- */

  function stageEls() {
    var editor = document.getElementById("transcribe-editor");
    if (!editor) return null;
    var stage = editor.querySelector(".ss-editor-stage");
    if (!stage) return null;
    return {
      editor: editor,
      stage: stage,
      score: stage.querySelector(".ss-editor-score"),
      overlay: stage.querySelector(".ss-editor-overlay"),
      ghostLabel: stage.querySelector(".ss-ghost-label"),
    };
  }

  function buildStage(readonly) {
    var editor = document.getElementById("transcribe-editor");
    if (!editor) return null;
    editor.innerHTML = "";
    editor.className = readonly ? "ss-editor-readonly" : "";

    var stage = document.createElement("div");
    stage.className = "ss-editor-stage";

    var score = document.createElement("div");
    score.className = "ss-editor-score";
    stage.appendChild(score);

    var overlay = document.createElementNS(SVG_NS, "svg");
    overlay.setAttribute("class", "ss-editor-overlay");
    stage.appendChild(overlay);

    var ghostLabel = document.createElement("div");
    ghostLabel.className = "ss-ghost-label";
    ghostLabel.style.display = "none";
    stage.appendChild(ghostLabel);

    editor.appendChild(stage);
    if (!readonly) attachPointerHandlers(overlay);
    return stageEls();
  }

  /* Build the display list: placed events plus faint placeholders. */
  function displaySlots() {
    var slots = [];
    for (var i = 0; i < state.events.length; i++) {
      slots.push({
        kind: "event",
        eventIndex: i,
        startUnit: state.events[i].startUnit,
        units: eventUnits(state.events[i]),
        event: state.events[i],
      });
    }
    var chunks = freeChunks();
    for (var j = 0; j < chunks.length; j++) {
      slots.push({
        kind: "free",
        startUnit: chunks[j].startUnit,
        units: durationUnits(chunks[j].duration),
        duration: chunks[j].duration,
      });
    }
    slots.sort(function (a, b) {
      return a.startUnit - b.startUnit;
    });
    return slots;
  }

  function renderScore() {
    var els = stageEls();
    if (!els || !els.score) return;
    var VF = window.Vex && window.Vex.Flow;
    if (!VF) {
      els.score.innerHTML =
        '<div class="ss-editor-message">Notation engine failed to load.</div>';
      geo = null;
      return;
    }

    var measured = els.editor.clientWidth || 520;
    // Give longer phrases more room: ~46px per beat plus clef/time margins,
    // but never below the historical single-bar width and capped so a wide
    // card doesn't stretch a short melody. A 4-beat melody stays ≈260–560px.
    var perBeat = Math.max(1, Math.ceil(capacity / 2)) * 46;
    var wanted = Math.max(measured, 110 + perBeat);
    var width = Math.max(260, Math.min(720, wanted));

    // Vertical layout adapts to the pitch range so high (minor) or low (bass)
    // notes and their stems/ledger lines aren't clipped. VexFlow's default line
    // spacing is 10px (one diatonic step = 5px) and it reserves ~40px of space
    // ABOVE the top staff line (getYForLine(0) = staveY + PAD_TOP), which the
    // canvas height and stave y must both account for or low notes fall off the
    // bottom (and real pointer events then miss the overlay). PITCHES already
    // spans the melody (padded) and the staff.
    var STEP_PX = 5;
    var PAD_TOP = 40; // VexFlow space_above_staff: getYForLine(0) - stave.y
    var STAFF_H = 40; // line 0 → line 4
    var aboveTop = Math.max(0, ordinalOf(PITCHES[PITCHES.length - 1]) - clefTopOrdinal());
    var belowBot = Math.max(0, clefBottomOrdinal() - ordinalOf(PITCHES[0]));
    // Keep the highest placeable note ~34px from the top (room for stem + label).
    var staveY = Math.max(0, aboveTop * STEP_PX - 6);
    var height = staveY + PAD_TOP + STAFF_H + belowBot * STEP_PX + 24;
    var ink = themeVar("--ss-ink", "#221f1c");
    var faint = themeVar("--ss-ink-faint", "#aca69d");

    els.stage.style.width = width + "px";
    els.score.innerHTML = "";

    var renderer = new VF.Renderer(els.score, VF.Renderer.Backends.SVG);
    renderer.resize(width, height);
    var ctx = renderer.getContext();
    ctx.setFillStyle(ink);
    ctx.setStrokeStyle(ink);

    var stave = new VF.Stave(4, staveY, width - 10);
    stave.addClef(clef).addTimeSignature(curTimeSig);
    stave.setStyle({
      fillStyle: themeVar("--ss-ink-soft", "#6f6a63"),
      strokeStyle: themeVar("--ss-ink-soft", "#6f6a63"),
    });
    stave.setContext(ctx).draw();

    var slots = displaySlots();
    var notes = [];
    var faintStyle = { fillStyle: faint, strokeStyle: faint };

    for (var i = 0; i < slots.length; i++) {
      var slot = slots[i];
      var note;
      if (slot.kind === "event") {
        if (slot.event.kind === "rest") {
          note = new VF.StaveNote({
            clef: clef,
            keys: [restKey()],
            duration: slot.event.duration + "r",
          });
        } else {
          /* "G4" -> "g/4" (letter + octave; editor pitches carry no accidentals) */
          note = new VF.StaveNote({
            clef: clef,
            keys: [
              slot.event.pitch.charAt(0).toLowerCase() +
                "/" +
                slot.event.pitch.slice(1),
            ],
            duration: slot.event.duration,
          });
        }
      } else {
        note = new VF.StaveNote({
          clef: clef,
          keys: [restKey()],
          duration: slot.duration + "r",
          align_center: slot.duration === "w" && !state.events.length,
        });
        note.setStyle(faintStyle);
      }
      slot.note = note;
      notes.push(note);
    }

    /* Beam adjacent placed eighth notes inside the same beat. */
    var beams = [];
    var beamRecords = [];
    var group = [];
    var groupIdx = [];
    function flushBeam() {
      if (group.length >= 2) {
        try {
          beams.push(new VF.Beam(group));
          beamRecords.push({
            beam: beams[beams.length - 1],
            eventIndexes: groupIdx.slice(),
          });
        } catch (e) {}
      }
      group = [];
      groupIdx = [];
    }
    for (var s = 0; s < slots.length; s++) {
      var sl = slots[s];
      var isPlacedEighthNote =
        sl.kind === "event" &&
        sl.event.kind === "note" &&
        sl.event.duration === "8";
      if (isPlacedEighthNote) {
        if (sl.startUnit % 2 === 0) flushBeam();
        group.push(sl.note);
        groupIdx.push(sl.eventIndex);
        if ((sl.startUnit + 1) % 2 === 0) flushBeam();
      } else {
        flushBeam();
      }
    }
    flushBeam();

    try {
      VF.Formatter.FormatAndDraw(ctx, stave, notes);
      for (var b = 0; b < beams.length; b++) {
        beams[b].setContext(ctx).draw();
      }
    } catch (err) {
      els.score.innerHTML =
        '<div class="ss-editor-message">Could not render this bar.</div>';
      geo = null;
      return;
    }

    /* ---- capture element handles for hover treatments ----
       VexFlow renders each element as an svg group with id "vf-<attrs.id>". */
    function vexElementFor(element) {
      if (!element || !element.attrs) return null;
      return document.getElementById("vf-" + element.attrs.id);
    }
    for (var e2 = 0; e2 < slots.length; e2++) {
      slots[e2].el = vexElementFor(slots[e2].note);
    }
    for (var b2 = 0; b2 < beamRecords.length; b2++) {
      beamRecords[b2].el = vexElementFor(beamRecords[b2].beam);
    }

    /* ---- capture geometry for the input overlay ---- */
    var anchors = [];
    var endX = stave.getX() + stave.getWidth() - 14;
    if (!state.events.length) {
      /* Empty bar shows one centered whole rest; use a uniform unit grid. */
      anchors.push({ unit: 0, x: stave.getNoteStartX() + 14 });
    } else {
      for (var a = 0; a < slots.length; a++) {
        anchors.push({
          unit: slots[a].startUnit,
          x: slots[a].note.getAbsoluteX(),
        });
      }
    }
    anchors.push({ unit: capacity, x: endX });

    var yBottom = stave.getYForLine(4); // staff line 4 == clefBottomOrdinal()
    var halfStep = (stave.getYForLine(4) - stave.getYForLine(3)) / 2;
    var refOrdinal = clefBottomOrdinal();

    /*
     * Uniform pixel grid over the bar. Block selection and the ghost
     * highlight both use this grid (not VexFlow's proportional glyph
     * spacing) so the visible edge of the purple box is exactly the
     * point where hovering flips to the next block.
     */
    var gridLeft = stave.getNoteStartX();
    var gridRight = stave.getX() + stave.getWidth() - 10;
    var unitPx = (gridRight - gridLeft) / capacity;

    geo = {
      width: width,
      height: height,
      anchors: anchors,
      slots: slots,
      beamRecords: beamRecords,
      staveTopY: stave.getYForLine(0),
      staveBottomY: yBottom,
      yBottom: yBottom,
      halfStep: halfStep,
      refOrdinal: refOrdinal,
      gridLeft: gridLeft,
      gridRight: gridRight,
      unitPx: unitPx,
      leftX: gridLeft - 14,
      rightX: gridRight,
    };

    var overlay = els.overlay;
    overlay.setAttribute("width", String(width));
    overlay.setAttribute("height", String(height));
    overlay.setAttribute("viewBox", "0 0 " + width + " " + height);
  }

  function unitToX(unit) {
    if (!geo) return 0;
    var anchors = geo.anchors;
    if (unit <= anchors[0].unit) return anchors[0].x;
    for (var i = 0; i < anchors.length - 1; i++) {
      var a = anchors[i];
      var b = anchors[i + 1];
      if (unit >= a.unit && unit <= b.unit) {
        if (b.unit === a.unit) return a.x;
        return a.x + ((unit - a.unit) / (b.unit - a.unit)) * (b.x - a.x);
      }
    }
    return anchors[anchors.length - 1].x;
  }

  function xToUnit(x) {
    if (!geo) return 0;
    var anchors = geo.anchors;
    if (x <= anchors[0].x) return anchors[0].unit;
    for (var i = 0; i < anchors.length - 1; i++) {
      var a = anchors[i];
      var b = anchors[i + 1];
      if (x >= a.x && x <= b.x) {
        if (b.x === a.x) return a.unit;
        return a.unit + ((x - a.x) / (b.x - a.x)) * (b.unit - a.unit);
      }
    }
    return capacity;
  }

  /* Uniform grid: pixel x for a unit boundary, used by the ghost box. */
  function gridX(unit) {
    return geo.gridLeft + unit * geo.unitPx;
  }

  /* Which duration-sized tile the pointer sits in, on the uniform grid. */
  function tileStartForX(x, units) {
    var maxTile = Math.floor(capacity / units) - 1;
    var tile = Math.floor((x - geo.gridLeft) / (geo.unitPx * units));
    if (tile < 0) tile = 0;
    if (tile > maxTile) tile = maxTile;
    return tile * units;
  }

  // geo.yBottom is the y of staff line 4, which is the pitch clefBottomOrdinal()
  // (E4 treble / G2 bass). A note that many diatonic steps higher sits that many
  // half-steps up (smaller y). PITCHES is a contiguous ordinal run, so the index
  // is just the offset from PITCHES[0].
  function yForPitchIndex(index) {
    var steps = ordinalOf(PITCHES[index]) - geo.refOrdinal;
    return geo.yBottom - steps * geo.halfStep;
  }

  function pitchIndexFromY(y) {
    var ord = Math.round(geo.refOrdinal + (geo.yBottom - y) / geo.halfStep);
    var index = ord - ordinalOf(PITCHES[0]);
    if (index < 0) return 0;
    if (index >= PITCHES.length) return PITCHES.length - 1;
    return index;
  }

  /* ---- ghost computation ---------------------------------------------------------- */

  function computeGhost(x, y) {
    if (!geo) return null;
    if (x < geo.leftX - 8 || x > geo.rightX + 8) return null;
    if (y < -14 || y > geo.height + 14) return null;

    if (state.mode === "erase") {
      var unit = Math.floor(xToUnit(x));
      var idx = eventIndexAtUnit(unit);
      if (idx < 0) {
        return { type: "erase-miss" };
      }
      return { type: "erase", eventIndex: idx };
    }

    /*
     * Placement snaps to the uniform-grid tile the pointer is over, so
     * the selection flips exactly when the pointer crosses the visible
     * edge of the highlight box. Painting over existing events replaces
     * them, so no eraser round-trip is needed for corrections.
     */
    var units = durationUnits(state.duration);
    var best = tileStartForX(x, units);

    var replaces = [];
    for (var i = 0; i < state.events.length; i++) {
      var ev = state.events[i];
      if (ev.startUnit < best + units && eventEndUnit(ev) > best) {
        replaces.push(i);
      }
    }

    var ghost = {
      type: state.mode === "rest" ? "rest" : "note",
      startUnit: best,
      units: units,
      replaces: replaces,
    };
    if (ghost.type === "note") {
      ghost.pitchIndex = pitchIndexFromY(y);
      ghost.pitch = PITCHES[ghost.pitchIndex];
    }
    return ghost;
  }

  /* ---- overlay rendering ------------------------------------------------------------ */

  /* Dim the score glyphs (and beams) that the hovered action would remove. */
  function setDoomed(eventIndexes) {
    if (!geo) return;
    var lookup = {};
    for (var i = 0; i < eventIndexes.length; i++) {
      lookup[eventIndexes[i]] = true;
    }
    for (var s = 0; s < geo.slots.length; s++) {
      var slot = geo.slots[s];
      if (slot.kind !== "event" || !slot.el) continue;
      slot.el.classList.toggle("ss-doomed", !!lookup[slot.eventIndex]);
    }
    var beamRecords = geo.beamRecords || [];
    for (var b = 0; b < beamRecords.length; b++) {
      var record = beamRecords[b];
      if (!record.el) continue;
      var allDoomed = record.eventIndexes.length > 0;
      for (var k = 0; k < record.eventIndexes.length; k++) {
        if (!lookup[record.eventIndexes[k]]) allDoomed = false;
      }
      record.el.classList.toggle("ss-doomed", allDoomed);
    }
  }

  function clearOverlay() {
    var els = stageEls();
    if (!els) return;
    while (els.overlay.firstChild) {
      els.overlay.removeChild(els.overlay.firstChild);
    }
    if (els.ghostLabel) els.ghostLabel.style.display = "none";
    setDoomed([]);
  }

  function showGhostLabel(text, x, y, variant) {
    var els = stageEls();
    if (!els || !els.ghostLabel) return;
    var label = els.ghostLabel;
    label.textContent = text;
    label.className =
      "ss-ghost-label" + (variant ? " ss-ghost-label-" + variant : "");
    label.style.display = "block";
    var half = (label.offsetWidth || 96) / 2 + 4;
    var maxX = geo ? Math.max(half, geo.width - half) : x;
    var clamped = Math.max(half, Math.min(maxX, x));
    label.style.left = clamped + "px";
    label.style.top = Math.max(4, y) + "px";
  }

  function renderOverlay() {
    clearOverlay();
    if (!hover || !geo) return;
    var els = stageEls();
    if (!els) return;
    var overlay = els.overlay;
    var accent = themeVar("--ss-accent", "#4f46e5");
    var bad = themeVar("--ss-bad", "#b91c1c");
    var ghost = hover.ghost;
    if (!ghost) return;

    if (ghost.type === "erase-miss") {
      showGhostLabel(
        "Tap a note or rest to remove it",
        geo.width / 2,
        geo.staveTopY - 12,
        "erase"
      );
      return;
    }

    if (ghost.type === "erase") {
      var target = state.events[ghost.eventIndex];
      if (!target) return;
      setDoomed([ghost.eventIndex]);
      var ex0 = unitToX(target.startUnit) - 12;
      var ex1 = unitToX(eventEndUnit(target)) - 6;
      svgEl(
        "rect",
        {
          x: ex0,
          y: geo.staveTopY - 18,
          width: Math.max(24, ex1 - ex0),
          height: geo.staveBottomY - geo.staveTopY + 44,
          rx: 9,
          fill: bad,
          "fill-opacity": 0.13,
          stroke: bad,
          "stroke-opacity": 0.5,
          "stroke-width": 1.4,
          "stroke-dasharray": "4 3",
        },
        overlay
      );
      var labelText =
        target.kind === "rest"
          ? "Remove " + DURATION_LABELS[target.duration].toLowerCase() + " rest"
          : "Remove " + target.pitch;
      showGhostLabel(labelText, (ex0 + ex1) / 2, geo.staveTopY - 24, "erase");
      return;
    }

    /* note / rest placement ghost */
    var replacing = ghost.replaces && ghost.replaces.length;
    if (replacing) setDoomed(ghost.replaces);

    /*
     * The box is exactly the pointer's uniform-grid tile: its width is
     * constant per duration and its edges are the selection boundaries,
     * so nudging the pointer past the visible edge flips to the next
     * block. The ghost notehead sits at the start of the tile.
     */
    var spanX = gridX(ghost.startUnit);
    var spanW = ghost.units * geo.unitPx;
    var x0 = spanX + Math.min(geo.unitPx, spanW) * 0.5;

    var spanAttrs = {
      x: spanX,
      y: geo.staveTopY - 18,
      width: spanW,
      height: geo.staveBottomY - geo.staveTopY + 44,
      rx: 9,
      fill: accent,
      "fill-opacity": replacing ? 0.15 : 0.1,
      stroke: accent,
      "stroke-opacity": replacing ? 0.7 : 0.45,
      "stroke-width": 1.4,
      "data-ss": "ghost-span",
    };
    if (!replacing) spanAttrs["stroke-dasharray"] = "4 3";
    svgEl("rect", spanAttrs, overlay);

    var beatText = DURATION_LABELS[state.duration].toLowerCase();

    if (ghost.type === "rest") {
      var midLineY = geo.yBottom - 4 * geo.halfStep; // middle staff line
      var restY = ghost.units >= 8 ? midLineY + 1.5 : midLineY - 6.5;
      svgEl(
        "rect",
        {
          x: spanX + spanW / 2 - 7.5,
          y: restY,
          width: 15,
          height: 5.5,
          rx: 1.5,
          fill: accent,
          "fill-opacity": 0.85,
        },
        overlay
      );
      showGhostLabel(
        DURATION_LABELS[state.duration] + " rest",
        spanX + spanW / 2,
        geo.staveTopY - 24,
        null
      );
      return;
    }

    var noteY = yForPitchIndex(ghost.pitchIndex);
    var headX = x0;

    /* Ledger lines for a note above/below the staff (preview only; the committed
       note gets exact ledgers from VexFlow). One at each line position between the
       staff edge and the note, derived from the pitch's staff ordinal — not a
       fixed index, which was wrong once the pitch window became clef/range-driven. */
    var noteOrd = ordinalOf(ghost.pitch);
    var topLineOrd = geo.refOrdinal + 8;
    var ledgerOrds = [];
    for (var lo = geo.refOrdinal - 2; lo >= noteOrd; lo -= 2) ledgerOrds.push(lo);
    for (var hi = topLineOrd + 2; hi <= noteOrd; hi += 2) ledgerOrds.push(hi);
    for (var li = 0; li < ledgerOrds.length; li++) {
      svgEl(
        "rect",
        {
          x: headX - 10,
          y: geo.yBottom - (ledgerOrds[li] - geo.refOrdinal) * geo.halfStep - 0.9,
          width: 20,
          height: 1.8,
          fill: accent,
          "fill-opacity": 0.9,
        },
        overlay
      );
    }

    var head = svgEl(
      "ellipse",
      {
        cx: headX,
        cy: noteY,
        rx: 6.1,
        ry: 4.5,
        fill: accent,
        "fill-opacity": 0.85,
        transform: "rotate(-16 " + headX + " " + noteY + ")",
      },
      overlay
    );
    if (state.duration === "h" || state.duration === "w") {
      head.setAttribute("fill-opacity", "0.28");
      head.setAttribute("stroke", accent);
      head.setAttribute("stroke-width", "2.4");
    }

    if (state.duration !== "w") {
      var stemUp = ordinalOf(ghost.pitch) < geo.refOrdinal + 4; // below middle line
      svgEl(
        "rect",
        {
          x: stemUp ? headX + 4.6 : headX - 6.2,
          y: stemUp ? noteY - 32 : noteY,
          width: 1.7,
          height: 32,
          rx: 0.8,
          fill: accent,
          "fill-opacity": 0.85,
        },
        overlay
      );
      if (state.duration === "8") {
        var fx = stemUp ? headX + 6.3 : headX - 4.5;
        var fy = stemUp ? noteY - 32 : noteY + 32;
        var dir = stemUp ? 1 : -1;
        svgEl(
          "path",
          {
            d:
              "M " + fx + " " + fy +
              " C " + (fx + 7) + " " + (fy + 5 * dir) +
              ", " + (fx + 8) + " " + (fy + 12 * dir) +
              ", " + (fx + 4) + " " + (fy + 18 * dir) +
              " C " + (fx + 6.5) + " " + (fy + 10 * dir) +
              ", " + (fx + 4) + " " + (fy + 7 * dir) +
              ", " + fx + " " + (fy + 6 * dir) + " Z",
            fill: accent,
            "fill-opacity": 0.85,
          },
          overlay
        );
      }
    }

    showGhostLabel(
      ghost.pitch + " · " + beatText,
      headX,
      geo.staveTopY - 24,
      null
    );
  }

  /* ---- pointer handling ---------------------------------------------------------------- */

  function pointerPos(event, overlay) {
    var rect = overlay.getBoundingClientRect();
    return { x: event.clientX - rect.left, y: event.clientY - rect.top };
  }

  function attachPointerHandlers(overlay) {
    var active = false;
    var lastMove = null;

    /*
     * Aim exclusively with pointermove positions. In Anki's Qt webview,
     * button events (pointerdown/pointerup) can report coordinates in a
     * different space than moves, which used to re-aim the ghost at the
     * bottom pitch right before the commit. Button events only fall back
     * to their own coordinates when no move was ever seen (first touch).
     */
    function update(event, isMove) {
      var pos = pointerPos(event, overlay);
      if (isMove) lastMove = pos;
      var aim = isMove || !lastMove ? pos : lastMove;
      hover = {
        x: aim.x,
        y: aim.y,
        ghost: computeGhost(aim.x, aim.y),
      };
      renderOverlay();
    }

    overlay.addEventListener("pointermove", function (event) {
      update(event, true);
    });
    overlay.addEventListener("pointerdown", function (event) {
      active = true;
      if (overlay.setPointerCapture) {
        try {
          overlay.setPointerCapture(event.pointerId);
        } catch (e) {}
      }
      update(event, false);
      event.preventDefault();
    });
    overlay.addEventListener("pointerup", function (event) {
      if (!active) return;
      active = false;
      /*
       * Commit exactly what the ghost preview showed for the last
       * move/down event. Release coordinates are deliberately ignored:
       * some webviews (Anki's Qt WebEngine) report pointerup positions
       * in a different coordinate space, which used to snap every
       * placement to the bottom pitch. Dragging off the staff hides the
       * ghost (computeGhost returns null), so releasing there cancels.
       */
      var ghost = hover && hover.ghost;
      if (ghost) {
        commitGhost(ghost);
      }
      hover = null;
      renderOverlay();
      event.preventDefault();
    });
    overlay.addEventListener("pointercancel", function () {
      active = false;
      hover = null;
      renderOverlay();
    });
    overlay.addEventListener("pointerleave", function () {
      if (active) return;
      hover = null;
      renderOverlay();
    });
  }

  function commitGhost(ghost) {
    if (ghost.type === "note" || ghost.type === "rest") {
      pushHistory();
      if (ghost.replaces && ghost.replaces.length) {
        for (var r = ghost.replaces.length - 1; r >= 0; r--) {
          state.events.splice(ghost.replaces[r], 1);
        }
      }
      state.events.push(
        ghost.type === "rest"
          ? {
              kind: "rest",
              duration: state.duration,
              startUnit: ghost.startUnit,
            }
          : {
              kind: "note",
              pitch: ghost.pitch,
              duration: state.duration,
              startUnit: ghost.startUnit,
            }
      );
      sortEvents();
      saveEvents();
      renderAll();
      return;
    }
    if (ghost.type === "erase") {
      pushHistory();
      state.events.splice(ghost.eventIndex, 1);
      saveEvents();
      renderAll();
    }
  }

  function renderAll() {
    renderScore();
    renderOverlay();
    updateToolbar();
    updateStatus();
  }

  /* ---- review (back side) ----------------------------------------------------------------- */

  function verdictIcon(kind) {
    if (kind === "good") {
      return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 C 6.5 2, 2 6.5, 2 12 C 2 17.5, 6.5 22, 12 22 C 17.5 22, 22 17.5, 22 12 C 22 6.5, 17.5 2, 12 2 Z M 10.4 16.4 L 5.9 11.9 L 7.6 10.2 L 10.4 13 L 16.4 7 L 18.1 8.7 Z"/></svg>';
    }
    if (kind === "none") {
      return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 C 6.5 2, 2 6.5, 2 12 C 2 17.5, 6.5 22, 12 22 C 17.5 22, 22 17.5, 22 12 C 22 6.5, 17.5 2, 12 2 Z M 11 6 L 13 6 L 13 13 L 11 13 Z M 11 15 L 13 15 L 13 17 L 11 17 Z"/></svg>';
    }
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2 C 6.5 2, 2 6.5, 2 12 C 2 17.5, 6.5 22, 12 22 C 17.5 22, 22 17.5, 22 12 C 22 6.5, 17.5 2, 12 2 Z M 7 11 L 17 11 L 17 13 L 7 13 Z"/></svg>';
  }

  function renderSummary(data) {
    var resultEl = document.getElementById("transcribe-result");
    var targetEl = document.getElementById("transcribe-target");
    var userEl = document.getElementById("transcribe-user");
    var userBlock = document.getElementById("transcribe-user-block");
    var legendEl = document.getElementById("transcribe-legend");
    if (!resultEl || !targetEl) return;

    capacity = capacityForData(data);
    applyPitchContext(data);

    if (!supportedData(data)) {
      resultEl.className = "ss-verdict ss-verdict-none";
      resultEl.innerHTML =
        verdictIcon("none") +
        "<span>This melody is outside the transcription exercise scope.</span>";
      return;
    }

    var targetEvents = targetEventsFromData(data);
    var good = themeVar("--ss-good", "#16803c");
    var bad = themeVar("--ss-bad", "#b91c1c");

    var targetByStart = {};
    for (var t = 0; t < targetEvents.length; t++) {
      targetByStart[targetEvents[t].startUnit] = targetEvents[t];
    }

    var styles = [];
    var correct = 0;
    for (var i = 0; i < state.events.length; i++) {
      var match = eventsMatch(
        state.events[i],
        targetByStart[state.events[i].startUnit]
      );
      if (match) correct += 1;
      styles.push(
        match
          ? { fillStyle: good, strokeStyle: good }
          : { fillStyle: bad, strokeStyle: bad }
      );
    }

    if (window.SightSingingDrawStaff) {
      window.SightSingingDrawStaff(targetEl, data);
      if (state.events.length && userEl) {
        window.SightSingingDrawStaff(userEl, buildAnswerData(), {
          styles: styles,
        });
      }
    }

    var total = targetEvents.length;
    var perfect =
      correct === total && state.events.length === total && total > 0;

    if (!state.events.length) {
      resultEl.className = "ss-verdict ss-verdict-none";
      resultEl.innerHTML =
        verdictIcon("none") +
        "<span>No answer was entered — study the target below.</span>";
      if (userBlock) userBlock.style.display = "none";
      if (legendEl) legendEl.style.display = "none";
      return;
    }

    if (perfect) {
      resultEl.className = "ss-verdict ss-verdict-good";
      resultEl.innerHTML =
        verdictIcon("good") +
        "<span>Perfect — every pitch and rhythm matches.</span>";
      if (legendEl) legendEl.style.display = "none";
    } else {
      resultEl.className = "ss-verdict ss-verdict-partial";
      resultEl.innerHTML =
        verdictIcon("partial") +
        "<span>" +
        correct +
        " of " +
        total +
        " events match — differences are marked red.</span>";
      if (legendEl) legendEl.style.display = "";
    }
  }

  /* ---- init ---------------------------------------------------------------------------------- */

  function initFront() {
    var editor = document.getElementById("transcribe-editor");
    if (!editor) return;

    var data = parseData();
    capacity = capacityForData(data);
    applyPitchContext(data);
    clearSavedEvents();
    state.events = [];
    state.history = [];
    state.mode = "note";
    state.duration = "q";

    if (!supportedData(data)) {
      editor.innerHTML =
        '<div class="ss-editor-message">This melody is outside the current transcription exercise scope.</div>';
      return;
    }

    buildStage(false);
    buildUI();
    renderAll();
  }

  var resizeTimer = null;
  window.addEventListener("resize", function () {
    if (isBack()) return;
    if (!document.getElementById("transcribe-editor")) return;
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      if (stageEls()) renderAll();
    }, 150);
  });

  function init() {
    if (isBack()) return;
    initFront();
  }

  function depsReady() {
    return !!(
      window.Vex &&
      window.Vex.Flow &&
      window.SightSingingParseData &&
      window.SightSingingDrawStaff
    );
  }

  /*
   * Boot once both VexFlow and the renderer API are available, then drive
   * the correct side ourselves. Anki re-executes the card's <script src>
   * tags as async, out-of-order nodes (pronounced on AnkiMobile/iOS), so
   * this file can run before _vexflow_*.js or _renderer_*.js finish, and
   * the template's trailing SightSingingTranscriptionReview() call can
   * fire before this file defines it. Self-triggering after deps are
   * ready makes rendering independent of load order and call timing.
   */
  function boot() {
    if (!depsReady()) {
      var tries = 0;
      var timer = setInterval(function () {
        tries += 1;
        if (depsReady() || tries > 200) {
          clearInterval(timer);
          boot();
        }
      }, 25);
      return;
    }
    if (isBack()) {
      window.SightSingingTranscriptionReview();
    } else {
      init();
    }
  }

  /* ---- public API ------------------------------------------------------------------------------ */

  window.SightSingingTranscriptionSetTool = function (tool) {
    state.mode = tool === "erase" ? "erase" : tool === "rest" ? "rest" : "note";
    hover = null;
    renderAll();
    return false;
  };

  window.SightSingingTranscriptionSetDuration = function (duration) {
    if (durationUnits(duration)) {
      state.duration = String(duration);
      if (state.mode === "erase") state.mode = "note";
      hover = null;
      renderAll();
    }
    return false;
  };

  window.SightSingingTranscriptionUndo = function () {
    if (state.history.length) {
      state.events = state.history.pop();
      saveEvents();
      hover = null;
      renderAll();
    }
    return false;
  };

  window.SightSingingTranscriptionReset = function () {
    if (state.events.length) {
      pushHistory();
      state.events = [];
      saveEvents();
      hover = null;
      renderAll();
    }
    return false;
  };

  window.SightSingingTranscriptionRefresh = function () {
    if (!isBack() && stageEls()) renderAll();
    return false;
  };

  window.SightSingingTranscriptionReview = function () {
    var data = parseData();
    // Size the grid + pitch window before loading the saved answer: a multi-bar
    // or out-of-treble-octave answer would otherwise be filtered out.
    capacity = capacityForData(data);
    applyPitchContext(data);
    state.events = loadSavedEvents();
    renderSummary(data);
  };

  /* Test/debug hooks: stable coordinates for Playwright and agents. */
  window.SightSingingTranscriptionDebug = {
    getState: function () {
      return {
        mode: state.mode,
        duration: state.duration,
        events: state.events.map(cloneEvent),
        historyDepth: state.history.length,
      };
    },
    validStarts: validStarts,
    clientPoint: function (unit, pitch) {
      var els = stageEls();
      if (!els || !geo) return null;
      var rect = els.overlay.getBoundingClientRect();
      // Center of the uniform-grid cell at `unit`, which lands inside the
      // selection tile for any duration that can start there.
      var x = gridX(Number(unit) + 0.5);
      var index = pitch ? PITCHES.indexOf(String(pitch)) : 4;
      if (index < 0) index = 4;
      return {
        x: rect.left + x,
        y: rect.top + yForPitchIndex(index),
      };
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
