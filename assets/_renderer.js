/* global window, document, Vex */
(function () {
  "use strict";

  function scientificToVexKey(name) {
    var m = String(name).match(/^([A-Ga-g])([#b]?)(\d+)$/);
    if (!m) return "c/4";
    var letter = m[1].toLowerCase();
    var acc = m[2] || "";
    var oct = m[3];
    var accVex = acc === "#" ? "#" : acc === "b" ? "b" : "";
    return letter + accVex + "/" + oct;
  }

  function parseData() {
    var el = document.getElementById("melody-data");
    if (!el) return null;
    try {
      return JSON.parse(el.textContent.trim());
    } catch (e) {
      return null;
    }
  }

  function fallbackNotation(container, data) {
    if (!container || !data || !data.notes) return;
    var p = document.createElement("p");
    p.className = "ss-fallback";
    p.textContent = data.notes.join(" ");
    container.appendChild(p);
  }

  function renderDegrees(container, data) {
    if (!container || !data || !data.degrees) return;
    var row = document.createElement("div");
    row.className = "ss-degrees";
    row.innerHTML =
      "<span class='ss-muted'>Scale degrees:</span> " +
      data.degrees.join(", ") +
      "<br><span class='ss-muted'>Notes:</span> " +
      data.notes.join(" ");
    container.appendChild(row);
  }

  function drawStaff(notationEl, data) {
    if (!notationEl || !data || !data.notes) return false;
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
    stave.addClef("treble").addTimeSignature("4/4");
    stave.setContext(ctx).draw();

    var notes = [];
    for (var i = 0; i < data.notes.length; i++) {
      var dur = (data.durations && data.durations[i]) || "q";
      notes.push(
        new VF.StaveNote({
          clef: "treble",
          keys: [scientificToVexKey(data.notes[i])],
          duration: dur,
        })
      );
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

  window.SightSingingRedraw = run;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
})();
