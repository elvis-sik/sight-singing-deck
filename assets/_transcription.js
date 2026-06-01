/* global window, document, localStorage */
(function () {
  "use strict";

  var PITCHES = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"];
  var PITCH_Y = {
    C4: 108,
    D4: 100,
    E4: 92,
    F4: 84,
    G4: 76,
    A4: 68,
    B4: 60,
    C5: 52,
  };
  var STAFF_LINES = [28, 44, 60, 76, 92];
  var BAR_LEFT = 54;
  var BAR_RIGHT = 18;
  var BAR_UNITS = 8;
  var DURATION_UNITS = {
    "8": 1,
    q: 2,
    h: 4,
    w: 8,
  };
  var DURATION_ORDER = ["w", "h", "q", "8"];
  var DURATION_LABELS = {
    "8": "Eighth",
    q: "Quarter",
    h: "Half",
    w: "Whole",
  };

  var state = {
    mode: "note",
    duration: "w",
    events: [],
  };

  function isBack() {
    return !!document.getElementById("back");
  }

  function parseData() {
    if (window.SightSingingParseData) {
      return window.SightSingingParseData();
    }
    return null;
  }

  function melodyId() {
    return String(window.sightSingingMelodyId || "").trim() || "unknown";
  }

  function storageKey() {
    return "ss-transcribe:" + melodyId();
  }

  function durationUnits(duration) {
    return DURATION_UNITS[String(duration || "")] || 0;
  }

  function durationStep(duration) {
    return durationUnits(duration);
  }

  function durationFitsAt(startUnit, duration, occupied) {
    var units = durationUnits(duration);
    if (!units) return false;
    if (startUnit < 0 || startUnit + units > BAR_UNITS) return false;
    if (startUnit % durationStep(duration) !== 0) return false;
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
    if (!durationFitsAt(cloned.startUnit, cloned.duration, occupiedUnits([]))) {
      return null;
    }
    if (cloned.kind === "note" && !PITCH_Y[cloned.pitch]) return null;
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

  function nearestPitch(y) {
    var bestPitch = PITCHES[0];
    var bestDistance = Infinity;
    for (var i = 0; i < PITCHES.length; i++) {
      var pitch = PITCHES[i];
      var dist = Math.abs(y - PITCH_Y[pitch]);
      if (dist < bestDistance) {
        bestDistance = dist;
        bestPitch = pitch;
      }
    }
    return bestPitch;
  }

  function editorMetrics(editorEl) {
    var width = Math.max(editorEl.clientWidth || 0, 300);
    var usableWidth = width - BAR_LEFT - BAR_RIGHT;
    var unitWidth = usableWidth / BAR_UNITS;
    return {
      width: width,
      usableWidth: usableWidth,
      unitWidth: unitWidth,
    };
  }

  function unitX(metrics, unit) {
    return BAR_LEFT + metrics.unitWidth * unit;
  }

  function quarterCenterX(metrics, beatIndex) {
    return BAR_LEFT + metrics.unitWidth * (beatIndex * 2 + 1);
  }

  function eventUnits(event) {
    return durationUnits(event.duration);
  }

  function eventEndUnit(event) {
    return event.startUnit + eventUnits(event);
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

  function occupiedUnits(events) {
    var occupied = [false, false, false, false, false, false, false, false];
    var source = Array.isArray(events) ? events : state.events;
    for (var i = 0; i < source.length; i++) {
      var event = source[i];
      var end = eventEndUnit(event);
      for (var unit = event.startUnit; unit < end; unit++) {
        if (unit >= 0 && unit < BAR_UNITS) {
          occupied[unit] = true;
        }
      }
    }
    return occupied;
  }

  function eventAtUnit(unit) {
    for (var i = 0; i < state.events.length; i++) {
      if (state.events[i].startUnit <= unit && eventEndUnit(state.events[i]) > unit) {
        return i;
      }
    }
    return -1;
  }

  function freeIntervals() {
    var occupied = occupiedUnits();
    var cursor = 0;
    var out = [];

    while (cursor < BAR_UNITS) {
      if (occupied[cursor]) {
        cursor += 1;
        continue;
      }

      var chosen = "8";
      for (var i = 0; i < DURATION_ORDER.length; i++) {
        var duration = DURATION_ORDER[i];
        if (durationFitsAt(cursor, duration, occupied)) {
          chosen = duration;
          break;
        }
      }

      out.push({
        startUnit: cursor,
        duration: chosen,
      });
      cursor += durationUnits(chosen);
    }

    return out;
  }

  function placementZones() {
    var zones = [];
    var occupied = occupiedUnits();
    if (state.mode === "erase") {
      for (var unit = 0; unit < BAR_UNITS; unit++) {
        zones.push({
          startUnit: unit,
          duration: "8",
          valid: eventAtUnit(unit) >= 0,
        });
      }
      return zones;
    }

    var step = durationStep(state.duration);
    for (var start = 0; start < BAR_UNITS; start += step) {
      zones.push({
        startUnit: start,
        duration: state.duration,
        valid: durationFitsAt(start, state.duration, occupied),
      });
    }
    return zones;
  }

  function setStatus(html, strong) {
    var el = document.getElementById("transcribe-status");
    if (!el) return;
    if (strong) {
      el.innerHTML = "<strong>" + strong + "</strong> " + html;
    } else {
      el.innerHTML = html;
    }
  }

  function updateToolbar() {
    var toolIds = ["note", "rest", "erase"];
    for (var i = 0; i < toolIds.length; i++) {
      var tool = toolIds[i];
      var toolBtn = document.getElementById("transcribe-tool-" + tool);
      if (toolBtn) {
        toolBtn.className =
          "ss-btn" + (state.mode === tool ? " ss-tool-active" : "");
      }
    }

    var durationIds = ["8", "q", "h", "w"];
    for (var j = 0; j < durationIds.length; j++) {
      var duration = durationIds[j];
      var durationBtn = document.getElementById(
        "transcribe-duration-" + duration
      );
      if (durationBtn) {
        durationBtn.className =
          "ss-btn" +
          (state.duration === duration ? " ss-tool-active" : "");
      }
    }
  }

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
    return cursor === BAR_UNITS ? out : [];
  }

  function supportedData(data) {
    if (!data) return false;
    if (String(data.clef || "treble") !== "treble") return false;
    return targetEventsFromData(data).length > 0;
  }

  function buildAnswerData() {
    return {
      version: 2,
      clef: "treble",
      key: "C",
      mode: "major",
      timeSig: "4/4",
      events: state.events.map(function (event) {
        if (event.kind === "rest") {
          return { kind: "rest", duration: event.duration };
        }
        return {
          kind: "note",
          pitch: event.pitch,
          duration: event.duration,
        };
      }),
    };
  }

  function renderFreeIntervals(editorEl, metrics) {
    var intervals = freeIntervals();
    for (var i = 0; i < intervals.length; i++) {
      var interval = intervals[i];
      var startX = unitX(metrics, interval.startUnit);
      var width = metrics.unitWidth * durationUnits(interval.duration);

      var gap = document.createElement("div");
      gap.className = "ss-transcribe-gap";
      gap.style.left = startX + 4 + "px";
      gap.style.width = Math.max(18, width - 8) + "px";
      editorEl.appendChild(gap);

      var label = document.createElement("div");
      label.className = "ss-transcribe-gap-label";
      label.style.left = startX + width / 2 + "px";
      label.textContent = interval.duration;
      editorEl.appendChild(label);
    }
  }

  function renderPlacementZones(editorEl, metrics, readonly) {
    var zones = placementZones();
    for (var i = 0; i < zones.length; i++) {
      var zone = zones[i];
      var startX = unitX(metrics, zone.startUnit);
      var width = metrics.unitWidth * durationUnits(zone.duration);

      var hit = document.createElement("button");
      hit.type = "button";
      hit.className =
        "ss-transcribe-hit" +
        (zone.valid ? " ss-transcribe-hit-valid" : " ss-transcribe-hit-invalid");
      hit.style.left = startX + "px";
      hit.style.width = width + "px";
      hit.dataset.startUnit = String(zone.startUnit);
      hit.dataset.duration = zone.duration;
      if (!readonly && zone.valid) {
        hit.addEventListener("click", handleZoneClick);
      } else {
        hit.disabled = true;
      }
      editorEl.appendChild(hit);
    }
  }

  function renderPlacedEvents(editorEl, metrics) {
    for (var eventIndex = 0; eventIndex < state.events.length; eventIndex++) {
      var event = state.events[eventIndex];
      var units = eventUnits(event);
      var startX = unitX(metrics, event.startUnit);
      var width = metrics.unitWidth * units;
      var centerX = startX + Math.min(metrics.unitWidth, width) / 2;

      var span = document.createElement("div");
      span.className =
        "ss-transcribe-event-span" +
        (event.kind === "rest" ? " ss-transcribe-event-rest" : "");
      span.style.left = startX + 6 + "px";
      span.style.width = Math.max(16, width - 12) + "px";
      editorEl.appendChild(span);

      var badge = document.createElement("div");
      badge.className = "ss-transcribe-duration-tag";
      badge.style.left = startX + width / 2 + "px";
      badge.textContent = event.duration;
      editorEl.appendChild(badge);

      if (event.kind === "rest") {
        var rest = document.createElement("div");
        rest.className =
          "ss-transcribe-rest ss-transcribe-rest-" + event.duration;
        rest.style.left = startX + width / 2 + "px";
        editorEl.appendChild(rest);
        continue;
      }

      var noteEl = document.createElement("div");
      noteEl.className =
        "ss-transcribe-note ss-transcribe-note-" + event.duration;
      noteEl.style.left = centerX + "px";
      noteEl.style.top = PITCH_Y[event.pitch] + "px";
      editorEl.appendChild(noteEl);

      if (event.pitch === "C4") {
        var ledger = document.createElement("div");
        ledger.className = "ss-transcribe-ledger";
        ledger.style.left = centerX - 12 + "px";
        ledger.style.top = PITCH_Y[event.pitch] + "px";
        ledger.style.width = "24px";
        ledger.style.height = "1px";
        editorEl.appendChild(ledger);
      }
    }
  }

  function renderEditor() {
    var editorEl = document.getElementById("transcribe-editor");
    if (!editorEl) return;

    var readonly = isBack();
    editorEl.innerHTML = "";
    editorEl.className =
      "ss-transcribe-editor" + (readonly ? " ss-readonly" : "");

    var metrics = editorMetrics(editorEl);

    for (var i = 0; i < STAFF_LINES.length; i++) {
      var line = document.createElement("div");
      line.className = "ss-transcribe-staff-line";
      line.style.top = STAFF_LINES[i] + "px";
      editorEl.appendChild(line);
    }

    var leftBar = document.createElement("div");
    leftBar.className = "ss-transcribe-bar-line";
    leftBar.style.left = BAR_LEFT + "px";
    editorEl.appendChild(leftBar);

    var rightBar = document.createElement("div");
    rightBar.className = "ss-transcribe-bar-line";
    rightBar.style.left = metrics.width - BAR_RIGHT + "px";
    editorEl.appendChild(rightBar);

    for (var unit = 1; unit < BAR_UNITS; unit++) {
      var guide = document.createElement("div");
      guide.className =
        "ss-transcribe-slot-guide" +
        (unit % 2 === 0 ? " ss-transcribe-slot-guide-beat" : "");
      guide.style.left = unitX(metrics, unit) + "px";
      editorEl.appendChild(guide);
    }

    for (var beat = 0; beat < 4; beat++) {
      var label = document.createElement("div");
      label.className = "ss-transcribe-slot-index";
      label.style.left = quarterCenterX(metrics, beat) + "px";
      label.textContent = String(beat + 1);
      editorEl.appendChild(label);
    }

    renderFreeIntervals(editorEl, metrics);
    renderPlacementZones(editorEl, metrics, readonly);
    renderPlacedEvents(editorEl, metrics);
  }

  function updateFrontStatus(data) {
    if (isBack()) return;
    if (!supportedData(data)) {
      setStatus(
        "This prototype currently supports one treble-clef bar in 4/4 using eighth, quarter, half, and whole values."
      );
      return;
    }

    var validCount = 0;
    var zones = placementZones();
    for (var i = 0; i < zones.length; i++) {
      if (zones[i].valid) validCount += 1;
    }

    var modeText =
      state.mode === "erase"
        ? "erase"
        : DURATION_LABELS[state.duration] +
          " " +
          (state.mode === "rest" ? "rest" : "note");

    setStatus(
      "used " +
        (usedUnits() / 2).toFixed(1).replace(".0", "") +
        "/4 beats. Selected: " +
        modeText +
        ". Valid areas: " +
        validCount +
        ".",
      "Bar"
    );
  }

  function compareEvents(a, b) {
    return (
      a.kind === b.kind &&
      a.startUnit === b.startUnit &&
      a.duration === b.duration &&
      (a.kind === "rest" || a.pitch === b.pitch)
    );
  }

  function renderSummary(data) {
    var resultEl = document.getElementById("transcribe-result");
    var targetEl = document.getElementById("transcribe-target");
    var userEl = document.getElementById("transcribe-user");
    if (!resultEl || !targetEl || !userEl) return;

    if (!supportedData(data)) {
      resultEl.textContent =
        "This melody is outside the current transcription prototype scope.";
      return;
    }

    var targetEvents = targetEventsFromData(data);
    if (window.SightSingingDrawStaff) {
      window.SightSingingDrawStaff(targetEl, data);
      window.SightSingingDrawStaff(userEl, buildAnswerData());
    }

    var correct = 0;
    var count = Math.max(targetEvents.length, state.events.length);
    for (var i = 0; i < Math.min(targetEvents.length, state.events.length); i++) {
      if (compareEvents(state.events[i], targetEvents[i])) {
        correct += 1;
      }
    }

    if (!state.events.length) {
      resultEl.innerHTML =
        "<strong>No answer entered.</strong> The target melody is shown below.";
      return;
    }

    resultEl.innerHTML =
      "<strong>" +
      correct +
      "/" +
      count +
      " events correct.</strong> Review your transcription against the target below.";
  }

  function placeEvent(startUnit, pitch) {
    var occupied = occupiedUnits();
    if (!durationFitsAt(startUnit, state.duration, occupied)) {
      setStatus("That value does not fit in the selected interval.", "Does not fit");
      return;
    }

    state.events.push(
      state.mode === "rest"
        ? {
            kind: "rest",
            duration: state.duration,
            startUnit: startUnit,
          }
        : {
            kind: "note",
            pitch: pitch,
            duration: state.duration,
            startUnit: startUnit,
          }
    );
    sortEvents();
    saveEvents();
  }

  function eraseAtUnit(unit) {
    var idx = eventAtUnit(unit);
    if (idx >= 0) {
      state.events.splice(idx, 1);
      saveEvents();
    }
  }

  function handleZoneClick(event) {
    if (isBack()) return;
    var startUnit = Number(event.currentTarget.dataset.startUnit || 0);
    if (state.mode === "erase") {
      eraseAtUnit(startUnit);
      renderEditor();
      updateToolbar();
      updateFrontStatus(parseData());
      return;
    }

    var editorEl = document.getElementById("transcribe-editor");
    if (!editorEl) return;
    var rect = editorEl.getBoundingClientRect();
    var y = event.clientY - rect.top;

    if (state.mode === "rest") {
      placeEvent(startUnit, null);
    } else {
      placeEvent(startUnit, nearestPitch(y));
    }

    renderEditor();
    updateToolbar();
    updateFrontStatus(parseData());
  }

  function init() {
    var editorEl = document.getElementById("transcribe-editor");
    if (!editorEl) return;

    var data = parseData();
    if (!isBack()) {
      clearSavedEvents();
      state.events = [];
    } else {
      state.events = loadSavedEvents();
    }

    state.mode = "note";
    state.duration = "w";

    var toolButtons = document.querySelectorAll("[data-transcribe-tool]");
    for (var i = 0; i < toolButtons.length; i++) {
      toolButtons[i].addEventListener("click", function (event) {
        event.preventDefault();
        window.SightSingingTranscriptionSetTool(
          event.currentTarget.getAttribute("data-transcribe-tool")
        );
      });
    }

    var durationButtons = document.querySelectorAll("[data-transcribe-duration]");
    for (var j = 0; j < durationButtons.length; j++) {
      durationButtons[j].addEventListener("click", function (event) {
        event.preventDefault();
        window.SightSingingTranscriptionSetDuration(
          event.currentTarget.getAttribute("data-transcribe-duration")
        );
      });
    }

    var resetButton = document.getElementById("transcribe-reset");
    if (resetButton) {
      resetButton.addEventListener("click", function (event) {
        event.preventDefault();
        window.SightSingingTranscriptionReset();
      });
    }

    updateToolbar();
    renderEditor();
    updateFrontStatus(data);
  }

  window.SightSingingTranscriptionSetTool = function (tool) {
    state.mode = tool === "erase" ? "erase" : tool === "rest" ? "rest" : "note";
    updateToolbar();
    renderEditor();
    updateFrontStatus(parseData());
    return false;
  };

  window.SightSingingTranscriptionSetDuration = function (duration) {
    if (durationUnits(duration)) {
      state.duration = String(duration);
      updateToolbar();
      renderEditor();
      updateFrontStatus(parseData());
    }
    return false;
  };

  window.SightSingingTranscriptionReset = function () {
    state.events = [];
    saveEvents();
    renderEditor();
    updateToolbar();
    updateFrontStatus(parseData());
    return false;
  };

  window.SightSingingTranscriptionReview = function () {
    state.events = loadSavedEvents();
    renderSummary(parseData());
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
