/* global window, document */
(function () {
  "use strict";

  var PC = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };

  function noteToMidi(name) {
    var m = String(name).match(/^([A-Ga-g])([#b]?)(\d+)$/);
    if (!m) return 60;
    var letter = m[1].toUpperCase();
    var acc = m[2] || "";
    var oct = parseInt(m[3], 10);
    var pc = PC[letter];
    if (acc === "#") pc += 1;
    if (acc === "b") pc -= 1;
    return (oct + 1) * 12 + pc;
  }

  function midiToFreq(midi) {
    return 440 * Math.pow(2, (midi - 69) / 12);
  }

  function noteToFreq(name) {
    return midiToFreq(noteToMidi(name));
  }

  var audioCtx = null;

  function getCtx() {
    if (!audioCtx) {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return null;
      audioCtx = new Ctx();
    }
    if (audioCtx.state === "suspended") {
      audioCtx.resume();
    }
    return audioCtx;
  }

  function playTone(ctx, freq, start, duration) {
    var osc = ctx.createOscillator();
    var gain = ctx.createGain();
    osc.type = "triangle";
    osc.frequency.value = freq;
    var atk = 0.02;
    var dec = 0.04;
    var rel = 0.12;
    var peak = 0.22;
    var sus = 0.12;
    var end = start + duration;
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(peak, start + atk);
    gain.gain.exponentialRampToValueAtTime(sus, start + atk + dec);
    if (end - rel > start + atk + dec) {
      gain.gain.setValueAtTime(sus, end - rel);
    }
    gain.gain.exponentialRampToValueAtTime(0.0001, end);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(start);
    osc.stop(end + 0.02);
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

  var quarterSec = 0.52;

  window.playCadence = function () {
    var ctx = getCtx();
    if (!ctx) return;
    var roots = ["C4", "F4", "G4", "C4"];
    var t = ctx.currentTime + 0.05;
    var d = 0.42;
    for (var i = 0; i < roots.length; i++) {
      playTone(ctx, noteToFreq(roots[i]), t + i * d, d * 0.92);
    }
  };

  window.playFirstNote = function () {
    var ctx = getCtx();
    if (!ctx) return;
    var data = parseData();
    var n =
      data && data.supports && data.supports.firstNote
        ? data.supports.firstNote
        : "C4";
    playTone(ctx, noteToFreq(n), ctx.currentTime + 0.05, 0.55);
  };

  window.playTonic = function () {
    var ctx = getCtx();
    if (!ctx) return;
    var data = parseData();
    var n =
      data && data.supports && data.supports.tonic
        ? data.supports.tonic
        : "C4";
    playTone(ctx, noteToFreq(n), ctx.currentTime + 0.05, 0.55);
  };

  window.playMelody = function () {
    var ctx = getCtx();
    if (!ctx) return;
    var data = parseData();
    if (!data || !data.notes || !data.notes.length) return;
    var t = ctx.currentTime + 0.05;
    for (var i = 0; i < data.notes.length; i++) {
      playTone(ctx, noteToFreq(data.notes[i]), t + i * quarterSec, quarterSec * 0.9);
    }
  };
})();
