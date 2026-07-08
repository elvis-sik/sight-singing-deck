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
  // Key-signature accidental per letter (e.g. G major -> {F:1}), from the target's
  // keyAccidentals. A placed note with no explicit accidental inherits this, so in
  // G major tapping the F line means F♯ without the student adding a glyph.
  var curKeyAcc = {};
  // "rhythm"/"sounded" ⇒ grade by sounded rhythm (pitch-agnostic, rest-spelling
  // equivalent); "" ⇒ exact pitch+rhythm match (the melodic default).
  var curGradeMode = "";
  var LETTERS = "CDEFGAB";
  var LETTER_SEMITONE = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };

  // Modes whose melodies can carry a note spelled OUTSIDE the key signature, so
  // the editor must offer accidental input. Harmonic minor's raised 7 (si) is the
  // shipped case; melodic minor's raised 6/7 would join here.
  function modeAllowsAccidentals(mode) {
    return String(mode) === "harmonic_minor";
  }

  // Chromatic pitch number (octave*12 + semitone) for match grading. `accOverride`
  // is the student's explicit accidental ("#"/"b"/"n", "" ⇒ none); when absent, an
  // accidental spelled into `pitchStr` wins, else the key-signature default. Targets
  // are fully spelled (e.g. "G#4"), so their string accidental is authoritative;
  // the student places bare letters and carries the accidental separately.
  function pitchChroma(pitchStr, accOverride, keyAcc) {
    var m = String(pitchStr).match(/^([A-Ga-g])([#b]?)(-?\d+)$/);
    if (!m) return null;
    var letter = m[1].toUpperCase();
    var oct = parseInt(m[3], 10);
    var semis;
    if (accOverride) {
      semis = accOverride === "#" ? 1 : accOverride === "b" ? -1 : 0;
    } else if (m[2]) {
      semis = m[2] === "#" ? 1 : -1;
    } else {
      semis = (keyAcc && keyAcc[letter]) || 0;
    }
    return oct * 12 + LETTER_SEMITONE[letter] + semis;
  }

  // A note's placeable pitch string fully SPELLED for the back-side renderer (which
  // reads accidentals from the pitch string and draws a glyph only where it deviates
  // from the key signature). An explicit accidental wins; an explicit natural ("n")
  // stays a bare letter (so it draws ♮ against a sharp/flat key); a diatonic note
  // inherits the key-signature accidental — so a bare F in G major is spelled "F#"
  // and matches the target's spelling instead of drawing a spurious natural.
  function pitchWithAcc(event) {
    var letter = event.pitch.charAt(0);
    var octave = event.pitch.slice(1);
    var acc;
    if (event.acc === "#" || event.acc === "b") {
      acc = event.acc;
    } else if (event.acc === "n") {
      acc = "";
    } else {
      var k = curKeyAcc && curKeyAcc[letter.toUpperCase()];
      acc = k === 1 ? "#" : k === -1 ? "b" : "";
    }
    return letter + acc + octave;
  }

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

  // The rhythmic grid resolution: units per quarter-note beat. 2 = eighth grid (the
  // default — everything divides the beat in halves), 6 = sextuplet grid, used ONLY
  // for cards whose target contains triplets (a triplet eighth is 1/3 of a beat, so
  // 6 makes it an integer 2 units while an eighth stays 3). Set per card in
  // applyPitchContext; it stays 2 for every existing melodic/duple-rhythm card, so
  // their unit math (and the tests pinned to it) is unchanged.
  var UNITS_PER_BEAT = 2;
  var BAR_UNITS = 4 * UNITS_PER_BEAT; // units in one 4/4 bar (reference)
  // Editor working length in grid units = the target melody's total length
  // (beat-aligned). Set from the target in initFront/renderSummary.
  var capacity = BAR_UNITS;
  // Duration → fraction of a beat. Units = fraction × UNITS_PER_BEAT (× 1.5 dotted).
  var BEAT_FRACTION = { "8": 0.5, q: 1, h: 2, w: 4, "8t": 1 / 3 };
  var DURATION_ORDER = ["w", "h", "q", "8"];
  var DURATION_LABELS = {
    "8": "Eighth", q: "Quarter", h: "Half", w: "Whole",
    qd: "Dotted quarter", hd: "Dotted half", "8t": "Triplet eighth",
  };
  // Where a note of each duration may START, in grid units, on MELODIC cards (which
  // are always UNITS_PER_BEAT === 2). Binary values align to their own length (a
  // half only on units 0/4); DOTTED values align to the beat (2) — a dotted quarter
  // is 3 units, so `% units` would wrongly forbid a beat-2 start (4 % 3 ≠ 0). Rhythm
  // cards ignore this table (see durationAlign). Only quarter/half are dottable.
  var DURATION_ALIGN = { "8": 1, q: 2, h: 4, w: 8, qd: 2, hd: 2 };
  // Which base durations the dot modifier applies to (integer-unit only).
  var DOTTABLE = { q: true, h: true };

  var state = {
    mode: "note", // note | rest | erase
    duration: "q",
    dotted: false, // dot modifier (rhythm cards) — applies to quarter/half
    triplet: false, // triplet tool (triplet cards) — one tap fills a beat with 3
    accidental: "", // "" (diatonic, follows key sig) | "#" | "b" | "n"
    events: [],
    history: [],
  };

  // The duration actually placed: the base value, dotted when the dot modifier is
  // on AND the base is dottable (quarter/half). Used everywhere placement happens.
  function effectiveDuration() {
    return state.dotted && DOTTABLE[state.duration]
      ? state.duration + "d"
      : state.duration;
  }

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

  // Grid units for a duration at the current UNITS_PER_BEAT, honouring a trailing
  // "d" (dotted = 1.5x). At the default grid (2): "8"→1, q→2, h→4, w→8, qd→3, hd→6
  // — identical to before. At the triplet grid (6): "8"→3, q→6, "8t"→2 (a triplet
  // eighth), all integers. Math.round guards the 1/3 float.
  function durationUnits(duration) {
    var s = String(duration || "");
    var dotted = s.charAt(s.length - 1) === "d";
    var frac = BEAT_FRACTION[dotted ? s.slice(0, -1) : s];
    if (frac === undefined) return 0;
    return Math.round(frac * UNITS_PER_BEAT * (dotted ? 1.5 : 1) * 1e6) / 1e6;
  }

  // Start-position granularity for a duration (see DURATION_ALIGN). Rhythm cards
  // relax to the EIGHTH grid (UNITS_PER_BEAT / 2) so syncopation is enterable — an
  // offbeat quarter starts on an off-beat eighth and, by sounded rhythm, equals the
  // two tied eighths the target draws; triplet notes come from the triplet tool, not
  // free placement. Melodic cards keep beat/length alignment so placement stays
  // snappy. A correct on-beat answer is unaffected either way.
  function durationAlign(duration) {
    if (curGradeMode === "rhythm" || curGradeMode === "sounded") {
      // Triplet eighths sit on the triplet subdivision (a third of a beat); every
      // other value snaps to the eighth grid (offbeats allowed for syncopation).
      if (String(duration) === "8t") return Math.max(1, UNITS_PER_BEAT / 3);
      return Math.max(1, UNITS_PER_BEAT / 2);
    }
    return DURATION_ALIGN[String(duration || "")] || 1;
  }

  function isDotted(duration) {
    var s = String(duration || "");
    return s.charAt(s.length - 1) === "d";
  }
  // The bare VexFlow note value: strip a triplet marker ("8t" → "8", the tuplet
  // bracket conveys the 3-in-2) then a dot ("qd" → "q").
  function baseDuration(duration) {
    var s = String(duration || "");
    if (s.charAt(s.length - 1) === "t") s = s.slice(0, -1);
    if (s.charAt(s.length - 1) === "d") s = s.slice(0, -1);
    return s;
  }
  // Attach an augmentation dot to a VexFlow note (the API moved between versions).
  function addDot(note) {
    var VF = window.Vex && window.Vex.Flow;
    if (VF && VF.Dot && typeof VF.Dot.buildAndAttach === "function") {
      VF.Dot.buildAndAttach([note], { all: true });
    } else if (typeof note.addDotToAll === "function") {
      note.addDotToAll();
    } else if (typeof note.addDot === "function") {
      note.addDot(0);
    }
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
    if (startUnit % durationAlign(duration) !== 0) return false;
    for (var i = startUnit; i < startUnit + units; i++) {
      if (occupied[i]) return false;
    }
    return true;
  }

  function cloneEvent(event) {
    if (!event) return null;
    var out = {
      kind: event.kind === "rest" ? "rest" : "note",
      duration: String(event.duration || "q"),
      startUnit: Number(event.startUnit || 0),
      pitch: event.kind === "rest" ? null : String(event.pitch || "C4"),
    };
    // Only carry an accidental when the note actually has one, so diatonic
    // (C-major / natural-minor) events serialize exactly as before.
    if (out.kind === "note" && event.acc) out.acc = String(event.acc);
    // Carry the tuplet flag (triplet members) for the "3" bracket + round-trips.
    if (out.kind === "note" && event.tuplet) out.tuplet = true;
    return out;
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

  /* Valid start units for the currently selected (possibly dotted) duration. */
  function validStarts() {
    var occupied = occupiedUnits(state.events);
    var dur = effectiveDuration();
    var step = durationAlign(dur); // step by the alignment grid, not the length
    var out = [];
    for (var start = 0; start + durationUnits(dur) <= capacity; start += step) {
      if (durationFitsAt(start, dur, occupied)) out.push(start);
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
      // The card encodes a triplet eighth as duration "8" + tuplet:true (the
      // renderer's convention); the editor grid needs the distinct 2-unit value
      // "8t", so translate on the way in. Any other tuplet base is left as-is.
      var dur = String(source.duration);
      if (source.tuplet === true && dur === "8") dur = "8t";
      var units = durationUnits(dur);
      if (!units) return [];
      out.push({
        kind: source.kind === "rest" ? "rest" : "note",
        pitch: source.kind === "rest" ? null : source.pitch,
        duration: dur,
        startUnit: cursor,
        // Preserve tie/tuplet so the target's sounded-rhythm grid is correct: a tie
        // suppresses the tied-into note's onset (syncopation reads as one attack).
        tie: source.tie === true,
        tuplet: source.tuplet === true,
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
    var rem = total % UNITS_PER_BEAT;
    if (rem !== 0) total += UNITS_PER_BEAT - rem; // pad up to a whole beat
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
    // Grid resolution FIRST — everything below (targetEventsFromData, buildPitches,
    // capacity) goes through durationUnits, which depends on UNITS_PER_BEAT. Use the
    // sextuplet grid only when the target actually contains triplets.
    var hasTriplet =
      !!(data && Array.isArray(data.events)) &&
      data.events.some(function (e) {
        return e && e.tuplet === true;
      });
    UNITS_PER_BEAT = hasTriplet ? 6 : 2;
    BAR_UNITS = 4 * UNITS_PER_BEAT;
    clef = String((data && data.clef) || "treble");
    curKey = String((data && data.key) || "C");
    curMode = String((data && data.mode) || "major");
    curTimeSig = String((data && data.timeSig) || "4/4");
    curKeySig = String((data && data.keySig) || "");
    // SightSingingParseData already normalizes keyAccidentals -> keyAcc.
    curKeyAcc =
      data && data.keyAcc && typeof data.keyAcc === "object" ? data.keyAcc : {};
    curGradeMode = String((data && data.gradeMode) || "");
    PITCHES = buildPitches(targetEventsFromData(data), clef);
  }

  /* ---- sounded-rhythm grading (rhythm cards) --------------------------------
   * What you HEAR: a per-eighth-unit grid — 0 silence, 1 attack, 2 held. A note
   * is one attack then (units-1) helds; a rest/gap is silence. So a half-rest and
   * two quarter-rests reduce identically, while q+q (two attacks) stays distinct
   * from a held half. Pitch is ignored (rhythm cards are notated on any one line).
   *
   * Ties: a note with `tie === true` is tied INTO the following note, so it is the
   * *next* note's onset that is suppressed (the pair sounds as one attack held
   * across both) — an offbeat quarter written as two tied eighths reduces to the
   * same grid as the quarter itself. (Earlier this suppressed the tie-flagged
   * note's own onset, which put the attack on the wrong unit for syncopation.)
   */
  function soundedRhythm(events, totalUnits) {
    var evs = (events || []).slice().sort(function (a, b) {
      return a.startUnit - b.startUnit;
    });
    var end = 0;
    for (var i = 0; i < evs.length; i++) {
      var u = evs[i].startUnit + durationUnits(evs[i].duration);
      if (u > end) end = u;
    }
    var length = typeof totalUnits === "number" && totalUnits > end ? totalUnits : end;
    var grid = [];
    for (var g = 0; g < length; g++) grid.push(0);
    for (var j = 0; j < evs.length; j++) {
      var e = evs[j];
      var units = durationUnits(e.duration);
      if (!units || e.kind === "rest") continue;
      var prev = j > 0 ? evs[j - 1] : null;
      var tiedInto =
        !!prev &&
        prev.kind === "note" &&
        prev.tie === true &&
        prev.startUnit + durationUnits(prev.duration) === e.startUnit;
      for (var k = 0; k < units; k++) {
        var pos = e.startUnit + k;
        if (pos >= 0 && pos < length) grid[pos] = k === 0 && !tiedInto ? 1 : 2;
      }
    }
    return grid;
  }

  function rhythmsMatch(a, b) {
    if (!a || !b || a.length !== b.length) return false;
    for (var i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
    return true;
  }

  /* Per-event correctness for the red/green tinting (best-effort; the verdict is
     the whole-grid rhythmsMatch). */
  function eventFitsSounded(ev, grid) {
    var units = durationUnits(ev.duration);
    if (!units) return false;
    for (var k = 0; k < units; k++) {
      var pos = ev.startUnit + k;
      var cell = pos >= 0 && pos < grid.length ? grid[pos] : -1;
      if (ev.kind === "rest") {
        if (cell !== 0) return false;
      } else if (cell !== (k === 0 ? 1 : 2)) {
        return false;
      }
    }
    return true;
  }

  function buildAnswerData() {
    return {
      version: 2,
      clef: clef,
      key: curKey,
      mode: curMode,
      timeSig: curTimeSig,
      keySig: curKeySig,
      keyAcc: curKeyAcc,
      events: state.events.map(function (event) {
        if (event.kind === "rest") {
          return { kind: "rest", duration: event.duration };
        }
        // Bake any explicit accidental into the pitch string; the renderer reads
        // accidentals from the string and draws a glyph where it deviates from the
        // key signature (a bare letter in a sharp/flat key -> ♮).
        var out = {
          kind: "note",
          pitch: pitchWithAcc(event),
          duration: event.duration,
        };
        // Translate the editor's internal triplet eighth ("8t") back to the
        // renderer's convention: an eighth flagged tuplet (it draws the "3").
        if (event.duration === "8t") {
          out.duration = "8";
          out.tuplet = true;
        }
        return out;
      }),
    };
  }

  function eventsMatch(userEvent, targetEvent) {
    return (
      !!targetEvent &&
      userEvent.kind === targetEvent.kind &&
      userEvent.startUnit === targetEvent.startUnit &&
      userEvent.duration === targetEvent.duration &&
      // A pitch matches when it is both on the same STAFF POSITION (line/space,
      // so E♯ can't pass for F) AND at the same CHROMATIC pitch. In a diatonic
      // key the key signature supplies the accidental, so tapping the F line in
      // G major already reads as F♯ (matches a target "F#4") with no glyph. Where
      // a note is spelled outside the key signature — harmonic-minor si = G♯ in A
      // minor — the student must add the ♯: a bare G is then a genuine miss. For
      // all-natural C-major melodies both checks reduce to the old position test.
      (userEvent.kind === "rest" ||
        (ordinalOf(userEvent.pitch) === ordinalOf(targetEvent.pitch) &&
          pitchChroma(userEvent.pitch, userEvent.acc || "", curKeyAcc) ===
            pitchChroma(targetEvent.pitch, "", curKeyAcc)))
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
    // Dot modifier — only for rhythm cards (the melodic spine is even-rhythm, so it
    // would be dead weight there). Applies to the quarter/half; inert (dimmed) on
    // eighth/whole, whose dotted values don't land on the integer grid.
    if (curGradeMode === "rhythm" || curGradeMode === "sounded") {
      var dotBtn = buildButton(
        "transcribe-dot",
        "ss-btn ss-btn-duration ss-btn-dot",
        '<span class="ss-dot-glyph" aria-hidden="true">♩.</span>' +
          '<span class="ss-btn-caption">Dotted</span>',
        function () {
          window.SightSingingTranscriptionToggleDot();
        }
      );
      dotBtn.setAttribute("aria-label", "dotted note");
      durbar.appendChild(dotBtn);
    }
    // Triplet tool — only on triplet cards (target contains triplets ⇒ the
    // sextuplet grid). One tap fills the pointed-at beat with three equal notes.
    if (UNITS_PER_BEAT === 6) {
      var tripBtn = buildButton(
        "transcribe-triplet",
        "ss-btn ss-btn-duration ss-btn-triplet",
        '<span class="ss-dot-glyph" aria-hidden="true">♪³</span>' +
          '<span class="ss-btn-caption">Triplet</span>',
        function () {
          window.SightSingingTranscriptionToggleTriplet();
        }
      );
      tripBtn.setAttribute("aria-label", "triplet");
      durbar.appendChild(tripBtn);
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

    // Accidental palette — only for modes that spell notes outside the key
    // signature (harmonic minor's raised 7). Diatonic keys never show it: the key
    // signature supplies every accidental, so it would be dead weight (and a
    // spoiler-free, category-level cue rather than a per-melody one).
    if (modeAllowsAccidentals(curMode)) {
      var accSeg = document.createElement("div");
      accSeg.className = "ss-segmented ss-accbar";
      accSeg.id = "transcribe-accbar";
      var accDefs = [
        { acc: "b", label: "♭" },
        { acc: "n", label: "♮" },
        { acc: "#", label: "♯" },
      ];
      for (var ai = 0; ai < accDefs.length; ai++) {
        (function (def) {
          var btn = buildButton(
            "transcribe-acc-" + (def.acc === "#" ? "sharp" : def.acc === "b" ? "flat" : "natural"),
            "ss-btn ss-btn-acc",
            "<span>" + def.label + "</span>",
            function () {
              window.SightSingingTranscriptionSetAccidental(def.acc);
            }
          );
          btn.setAttribute("data-transcribe-acc", def.acc);
          btn.setAttribute("aria-label", "accidental " + def.label);
          accSeg.appendChild(btn);
        })(accDefs[ai]);
      }
      tools.appendChild(accSeg);
    }

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
    var nbeats = Math.max(1, Math.ceil(capacity / UNITS_PER_BEAT));
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

    var dotBtn = document.getElementById("transcribe-dot");
    if (dotBtn) {
      // Active when the dot is on; dimmed when the current base can't take a dot
      // (eighth/whole) — a no-op there, and while the triplet tool is engaged.
      var dottable = !!DOTTABLE[state.duration] && !state.triplet;
      dotBtn.className =
        "ss-btn ss-btn-duration ss-btn-dot" +
        (state.dotted && dottable ? " ss-tool-active" : "") +
        (dottable ? "" : " ss-btn-dot-disabled");
    }

    var tripBtn = document.getElementById("transcribe-triplet");
    if (tripBtn) {
      tripBtn.className =
        "ss-btn ss-btn-duration ss-btn-triplet" +
        (state.triplet && state.mode === "note" ? " ss-tool-active" : "");
    }

    var accbar = document.getElementById("transcribe-accbar");
    if (accbar) {
      // Accidentals apply to notes only — dim in rest/erase mode.
      accbar.className =
        "ss-segmented ss-accbar" +
        (state.mode === "note" ? "" : " ss-accbar-disabled");
      var accs = ["b", "n", "#"];
      for (var a = 0; a < accs.length; a++) {
        var slug = accs[a] === "#" ? "sharp" : accs[a] === "b" ? "flat" : "natural";
        var accBtn = document.getElementById("transcribe-acc-" + slug);
        if (accBtn) {
          accBtn.className =
            "ss-btn ss-btn-acc" +
            (state.mode === "note" && state.accidental === accs[a]
              ? " ss-tool-active"
              : "");
        }
      }
    }

    var undoBtn = document.getElementById("transcribe-undo");
    if (undoBtn) undoBtn.disabled = !state.history.length;
    var resetBtn = document.getElementById("transcribe-reset");
    if (resetBtn) resetBtn.disabled = !state.events.length;
  }

  /* ---- status + beat bar --------------------------------------------------------- */

  function beatsLabel(units) {
    var whole = Math.floor(units / UNITS_PER_BEAT);
    var rem = units % UNITS_PER_BEAT;
    var frac = rem === 0 ? "" : rem * 2 === UNITS_PER_BEAT ? "½" : "+";
    if (whole === 0 && frac) return frac;
    return String(whole) + frac;
  }

  function updateStatus() {
    var el = document.getElementById("transcribe-status");
    var used = usedUnits();

    var nbeats = Math.max(1, Math.ceil(capacity / UNITS_PER_BEAT));
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
          (DURATION_LABELS[effectiveDuration()] || state.duration).toLowerCase() +
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
        var filled = 0;
        for (var u = b * UNITS_PER_BEAT; u < (b + 1) * UNITS_PER_BEAT; u++) {
          if (occupied[u]) filled += 1;
        }
        fills[b].style.width = (filled / UNITS_PER_BEAT) * 100 + "%";
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
    var perBeat = Math.max(1, Math.ceil(capacity / UNITS_PER_BEAT)) * 46;
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
    stave.addClef(clef);
    // Show the key signature so a transfer key reads correctly (e.g. G major's F♯
    // in the signature means the F line is F♯ without a per-note glyph). A minor /
    // C major have an empty signature. getNoteStartX() below absorbs its width.
    if (curKeySig) {
      try {
        stave.addKeySignature(curKeySig);
      } catch (e) {}
    }
    stave.addTimeSignature(curTimeSig);
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
        var evBase = baseDuration(slot.event.duration);
        if (slot.event.kind === "rest") {
          note = new VF.StaveNote({
            clef: clef,
            keys: [restKey()],
            duration: evBase + "r",
          });
          if (isDotted(slot.event.duration)) addDot(note);
        } else {
          /* "G4" -> "g/4"; an explicit accidental bakes into the key ("g#/4") and
             also gets a drawn glyph. Diatonic notes carry none — the key signature
             at the stave head supplies the accidental. A dotted value draws with the
             base note value + an augmentation dot. */
          var evAcc = slot.event.acc || "";
          var accVex = evAcc === "#" ? "#" : evAcc === "b" ? "b" : "";
          note = new VF.StaveNote({
            clef: clef,
            keys: [
              slot.event.pitch.charAt(0).toLowerCase() +
                accVex +
                "/" +
                slot.event.pitch.slice(1),
            ],
            duration: evBase,
          });
          if (evAcc === "#" || evAcc === "b" || evAcc === "n") {
            note.addModifier(new VF.Accidental(evAcc), 0);
          }
          if (isDotted(slot.event.duration)) addDot(note);
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

    /* Beam duple eighth pairs within one beat; group triplet members (tuplet flag)
       into a 3-in-2 Tuplet with its own beam. */
    var beams = [];
    var beamRecords = [];
    var tuplets = [];
    var group = [];
    var groupIdx = [];
    var groupBeat = -1;
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
      groupBeat = -1;
    }
    var tGroup = [];
    function flushTuplet() {
      if (tGroup.length) {
        try {
          tuplets.push(new VF.Tuplet(tGroup, { num_notes: 3, notes_occupied: 2 }));
          if (tGroup.length >= 2) beams.push(new VF.Beam(tGroup));
        } catch (e) {}
      }
      tGroup = [];
    }
    for (var s = 0; s < slots.length; s++) {
      var sl = slots[s];
      var isNote = sl.kind === "event" && sl.event.kind === "note";
      if (isNote && sl.event.tuplet) {
        flushBeam();
        tGroup.push(sl.note);
        if (tGroup.length === 3) flushTuplet();
      } else if (isNote && sl.event.duration === "8") {
        flushTuplet();
        var beat = Math.floor(sl.startUnit / UNITS_PER_BEAT);
        if (group.length && beat !== groupBeat) flushBeam();
        group.push(sl.note);
        groupIdx.push(sl.eventIndex);
        groupBeat = beat;
      } else {
        flushTuplet();
        flushBeam();
      }
    }
    flushTuplet();
    flushBeam();

    try {
      VF.Formatter.FormatAndDraw(ctx, stave, notes);
      for (var b = 0; b < beams.length; b++) {
        beams[b].setContext(ctx).draw();
      }
      for (var tpl = 0; tpl < tuplets.length; tpl++) {
        tuplets[tpl].setContext(ctx).draw();
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

  /* Where the pointer's placement should START, snapped to the duration's
     ALIGNMENT grid (not its length): a dotted quarter is 3 units but starts on the
     beat (every 2 units), so snapping by length would offer illegal starts. For
     binary durations align === units, so this is the old tile behaviour. */
  function tileStartForX(x, duration) {
    var align = durationAlign(duration);
    var units = durationUnits(duration);
    var maxStart = capacity - units;
    var start = Math.floor((x - geo.gridLeft) / (geo.unitPx * align)) * align;
    if (start < 0) start = 0;
    if (start > maxStart) start = Math.floor(maxStart / align) * align;
    return start;
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
     * Triplet tool: one tap fills the pointed-at BEAT with three equal notes
     * (tuplet eighths). Only offered on triplet cards (UNITS_PER_BEAT === 6), where
     * a third of a beat is an integer 2 units, so the three notes land on integer
     * grid positions beat+0/+2/+4.
     */
    if (state.mode === "note" && state.triplet && UNITS_PER_BEAT === 6) {
      var pu = (x - geo.gridLeft) / geo.unitPx;
      var beatStart = Math.floor(pu / UNITS_PER_BEAT) * UNITS_PER_BEAT;
      if (beatStart < 0) beatStart = 0;
      if (beatStart + UNITS_PER_BEAT > capacity) {
        beatStart = capacity - UNITS_PER_BEAT;
      }
      if (beatStart < 0) return null;
      var tReplaces = [];
      for (var ti = 0; ti < state.events.length; ti++) {
        var te = state.events[ti];
        if (te.startUnit < beatStart + UNITS_PER_BEAT && eventEndUnit(te) > beatStart) {
          tReplaces.push(ti);
        }
      }
      var tg = {
        type: "triplet",
        startUnit: beatStart,
        units: UNITS_PER_BEAT,
        replaces: tReplaces,
      };
      tg.pitchIndex = pitchIndexFromY(y);
      tg.pitch = PITCHES[tg.pitchIndex];
      return tg;
    }

    /*
     * Placement snaps to the uniform-grid tile the pointer is over, so
     * the selection flips exactly when the pointer crosses the visible
     * edge of the highlight box. Painting over existing events replaces
     * them, so no eraser round-trip is needed for corrections.
     */
    var dur = effectiveDuration();
    var units = durationUnits(dur);
    var best = tileStartForX(x, dur);

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
      duration: dur,
      replaces: replaces,
    };
    if (ghost.type === "note") {
      ghost.pitchIndex = pitchIndexFromY(y);
      ghost.pitch = PITCHES[ghost.pitchIndex];
      ghost.acc = state.accidental;
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

    /* triplet placement ghost: a box over the beat + three noteheads + a "3". */
    if (ghost.type === "triplet") {
      if (ghost.replaces && ghost.replaces.length) setDoomed(ghost.replaces);
      var tSpanX = gridX(ghost.startUnit);
      var tSpanW = ghost.units * geo.unitPx;
      svgEl(
        "rect",
        {
          x: tSpanX, y: geo.staveTopY - 18, width: tSpanW,
          height: geo.staveBottomY - geo.staveTopY + 44, rx: 9,
          fill: accent, "fill-opacity": 0.1, stroke: accent,
          "stroke-opacity": 0.45, "stroke-width": 1.4, "stroke-dasharray": "4 3",
          "data-ss": "ghost-span",
        },
        overlay
      );
      var tNoteY = yForPitchIndex(ghost.pitchIndex);
      var third = tSpanW / 3;
      for (var tn = 0; tn < 3; tn++) {
        var tcx = tSpanX + third * (tn + 0.5);
        svgEl(
          "ellipse",
          {
            cx: tcx, cy: tNoteY, rx: 5.2, ry: 3.9, fill: accent,
            "fill-opacity": 0.85,
            transform: "rotate(-16 " + tcx + " " + tNoteY + ")",
          },
          overlay
        );
        svgEl(
          "rect",
          {
            x: tcx + 4, y: tNoteY - 28, width: 1.6, height: 28, rx: 0.8,
            fill: accent, "fill-opacity": 0.85,
          },
          overlay
        );
      }
      var tri3 = svgEl(
        "text",
        {
          x: tSpanX + tSpanW / 2, y: geo.staveTopY - 2, "font-size": 12,
          "font-weight": 700, "font-style": "italic", "text-anchor": "middle",
          fill: accent, "fill-opacity": 0.9,
        },
        overlay
      );
      tri3.textContent = "3";
      showGhostLabel("Triplet", tSpanX + tSpanW / 2, geo.staveTopY - 24, null);
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

    // The placed duration may be dotted; the notehead/stem/flag shape follows the
    // BASE value while the dot is an extra glyph and the label reads "dotted …".
    var ghostBase = baseDuration(ghost.duration);
    var ghostDotted = isDotted(ghost.duration);
    var beatText = (DURATION_LABELS[ghost.duration] || ghostBase).toLowerCase();

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
      if (ghostDotted) {
        svgEl("circle", {
          cx: spanX + spanW / 2 + 11, cy: restY + 2.75, r: 1.9,
          fill: accent, "fill-opacity": 0.9,
        }, overlay);
      }
      showGhostLabel(
        (DURATION_LABELS[ghost.duration] || ghostBase) + " rest",
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
    if (ghostBase === "h" || ghostBase === "w") {
      head.setAttribute("fill-opacity", "0.28");
      head.setAttribute("stroke", accent);
      head.setAttribute("stroke-width", "2.4");
    }
    // Augmentation dot, just right of (and slightly above) the notehead.
    if (ghostDotted) {
      svgEl("circle", {
        cx: headX + 10, cy: noteY - 2, r: 1.9,
        fill: accent, "fill-opacity": 0.9,
      }, overlay);
    }

    if (ghostBase !== "w") {
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
      if (ghostBase === "8") {
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

    var accSym = ghost.acc === "#" ? "♯"
      : ghost.acc === "b" ? "♭"
      : ghost.acc === "n" ? "♮" : "";
    if (accSym) {
      var accEl = svgEl(
        "text",
        {
          x: headX - 13,
          y: noteY + 5,
          "font-size": 17,
          "font-weight": 700,
          "text-anchor": "middle",
          fill: accent,
          "fill-opacity": 0.9,
        },
        overlay
      );
      accEl.textContent = accSym;
    }

    // Label shows the spelled pitch (letter + accidental + octave), e.g. "G♯4".
    var labelPitch =
      ghost.pitch.charAt(0) + accSym + ghost.pitch.slice(1);
    showGhostLabel(
      labelPitch + " · " + beatText,
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
              duration: ghost.duration || state.duration,
              startUnit: ghost.startUnit,
            }
          : {
              kind: "note",
              pitch: ghost.pitch,
              duration: ghost.duration || state.duration,
              startUnit: ghost.startUnit,
              acc: ghost.acc || "",
            }
      );
      sortEvents();
      saveEvents();
      renderAll();
      return;
    }
    if (ghost.type === "triplet") {
      pushHistory();
      if (ghost.replaces && ghost.replaces.length) {
        for (var tr = ghost.replaces.length - 1; tr >= 0; tr--) {
          state.events.splice(ghost.replaces[tr], 1);
        }
      }
      // Three tuplet eighths filling the beat (units beat+0/+2/+4 at UPB 6). The
      // tuplet flag drives the engraved "3" bracket; sounded-rhythm grading just
      // sees three onsets a third of a beat apart.
      var third = UNITS_PER_BEAT / 3;
      for (var n = 0; n < 3; n++) {
        state.events.push({
          kind: "note",
          pitch: ghost.pitch,
          duration: "8t",
          startUnit: ghost.startUnit + n * third,
          tuplet: true,
        });
      }
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

    applyPitchContext(data); // sets UNITS_PER_BEAT — must precede capacityForData
    capacity = capacityForData(data);

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

    var soundedMode = curGradeMode === "rhythm" || curGradeMode === "sounded";
    var targetByStart = {};
    for (var t = 0; t < targetEvents.length; t++) {
      targetByStart[targetEvents[t].startUnit] = targetEvents[t];
    }

    var styles = [];
    var correct = 0;
    var tgtGrid = soundedMode ? soundedRhythm(targetEvents, capacity) : null;
    for (var i = 0; i < state.events.length; i++) {
      var match = soundedMode
        ? eventFitsSounded(state.events[i], tgtGrid)
        : eventsMatch(state.events[i], targetByStart[state.events[i].startUnit]);
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
    // Sounded-rhythm equivalence is a whole-sequence property (spellings coalesce,
    // so event counts can differ), hence a binary verdict; melodic stays per-event.
    var perfect = soundedMode
      ? rhythmsMatch(soundedRhythm(state.events, capacity), tgtGrid)
      : correct === total && state.events.length === total && total > 0;

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
        "<span>" +
        (soundedMode
          ? "Perfect — the rhythm matches."
          : "Perfect — every pitch and rhythm matches.") +
        "</span>";
      if (legendEl) legendEl.style.display = "none";
    } else {
      resultEl.className = "ss-verdict ss-verdict-partial";
      resultEl.innerHTML =
        verdictIcon("partial") +
        "<span>" +
        (soundedMode
          ? "The rhythm you wrote sounds different — compare with the target below."
          : correct + " of " + total + " events match — differences are marked red.") +
        "</span>";
      if (legendEl) legendEl.style.display = "";
    }
  }

  /* ---- init ---------------------------------------------------------------------------------- */

  function initFront() {
    var editor = document.getElementById("transcribe-editor");
    if (!editor) return;

    var data = parseData();
    applyPitchContext(data); // sets UNITS_PER_BEAT — must precede capacityForData
    capacity = capacityForData(data);
    clearSavedEvents();
    state.events = [];
    state.history = [];
    state.mode = "note";
    state.duration = "q";
    state.dotted = false;
    state.triplet = false;
    state.accidental = "";

    if (!supportedData(data)) {
      editor.innerHTML =
        '<div class="ss-editor-message">This melody is outside the current transcription exercise scope.</div>';
      return;
    }

    // Rhythm cards: retitle the prompt (pitch is irrelevant — notate the rhythm on
    // any line). The "Rhythm" badge chip is handled by the renderer's renderMeta
    // from data.gradeMode.
    if (curGradeMode === "rhythm" || curGradeMode === "sounded") {
      var prompt = document.querySelector(".ss-prompt-transcribe");
      if (prompt) {
        prompt.textContent = "Write the rhythm you hear (one pitch — it's all timing).";
      }
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

  window.SightSingingTranscriptionToggleDot = function () {
    state.dotted = !state.dotted;
    // Dots apply to placed notes; the dot and the triplet tool are mutually
    // exclusive. Make sure we're placing notes.
    if (state.dotted) {
      state.triplet = false;
      if (state.mode === "erase") state.mode = "note";
    }
    hover = null;
    renderAll();
    return false;
  };

  window.SightSingingTranscriptionToggleTriplet = function () {
    state.triplet = !state.triplet;
    // The triplet tool places three notes at once; it owns note placement while on,
    // so clear the dot and switch to note mode.
    if (state.triplet) {
      state.dotted = false;
      state.mode = "note";
    }
    hover = null;
    renderAll();
    return false;
  };

  window.SightSingingTranscriptionSetAccidental = function (acc) {
    var next = acc === "#" || acc === "b" || acc === "n" ? acc : "";
    // Toggle: tapping the active accidental clears it (back to diatonic).
    state.accidental = state.accidental === next ? "" : next;
    // Accidentals only make sense while placing notes.
    if (state.accidental) state.mode = "note";
    hover = null;
    renderAll();
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
    applyPitchContext(data); // sets UNITS_PER_BEAT — must precede capacityForData
    capacity = capacityForData(data);
    state.events = loadSavedEvents();
    renderSummary(data);
  };

  /* Test/debug hooks: stable coordinates for Playwright and agents. */
  window.SightSingingTranscriptionDebug = {
    getState: function () {
      return {
        mode: state.mode,
        duration: state.duration,
        dotted: state.dotted,
        triplet: state.triplet,
        unitsPerBeat: UNITS_PER_BEAT,
        accidental: state.accidental,
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
