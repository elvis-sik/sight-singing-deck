/*
  Error-detection card interaction.

  Front: draw the WRITTEN melody, let the learner tap the note they think was
  played wrong (recolours it via the renderer's per-note styles; the tap is a
  self-graded enhancement — the card works without it).
  Back: redraw with the real wrong note in red and show a verdict against the
  learner's tap.

  Like the other card scripts, this polls for its dependencies (VexFlow + the
  renderer API) instead of assuming script load order, so it is robust on iOS
  WebKit and AnkiDroid where external/inline scripts can run out of order.
*/
(function () {
  "use strict";

  function ready() {
    return !!(
      window.Vex &&
      window.Vex.Flow &&
      typeof window.SightSingingDrawStaff === "function" &&
      typeof window.SightSingingNormalizeData === "function"
    );
  }

  function parseData() {
    var el = document.getElementById("melody-data");
    if (!el) return null;
    try {
      return window.SightSingingNormalizeData(JSON.parse(el.textContent.trim()));
    } catch (e) {
      return null;
    }
  }

  function themeVar(name, fallback) {
    if (typeof window.SightSingingThemeVar === "function") {
      return window.SightSingingThemeVar(name, fallback);
    }
    return fallback;
  }

  function accentStyle() {
    var c = themeVar("--ss-accent", "#4f46e5");
    return { fillStyle: c, strokeStyle: c };
  }

  function badStyle() {
    var c = themeVar("--ss-bad", "#b91c1c");
    return { fillStyle: c, strokeStyle: c };
  }

  function readInt(id) {
    var el = document.getElementById(id);
    if (!el) return -1;
    var n = parseInt((el.textContent || "").trim(), 10);
    return isNaN(n) ? -1 : n;
  }

  /* ---- front: tap to pick ------------------------------------------------- */

  function drawFront(notation, data, pick) {
    var styles = {};
    if (pick >= 0) styles[pick] = accentStyle();
    window.SightSingingDrawStaff(notation, data, { styles: styles });
    var groups = notation.querySelectorAll(".vf-stavenote");
    for (var i = 0; i < groups.length; i++) {
      (function (g, idx) {
        g.style.cursor = "pointer";
        g.addEventListener("click", function () {
          window.__ssErrPick = idx;
          drawFront(notation, data, idx); // recolour + rebind
        });
      })(groups[i], i);
    }
    return groups.length > 0;
  }

  function bindFront() {
    var notation = document.getElementById("notation");
    var data = parseData();
    if (!notation || !data || !data.events || !data.events.length) return false;
    var pick = typeof window.__ssErrPick === "number" ? window.__ssErrPick : -1;
    return drawFront(notation, data, pick);
  }

  /* ---- back: reveal the wrong note --------------------------------------- */

  function revealBack() {
    var notation = document.getElementById("notation");
    var data = parseData();
    if (!notation || !data || !data.events || !data.events.length) return false;
    var errIdx = readInt("error-index");
    var styles = {};
    if (errIdx >= 0) styles[errIdx] = badStyle();
    var pick = typeof window.__ssErrPick === "number" ? window.__ssErrPick : -1;
    if (pick >= 0 && pick !== errIdx) styles[pick] = accentStyle();
    window.SightSingingDrawStaff(notation, data, { styles: styles });

    var verdict = document.getElementById("error-verdict");
    if (verdict) {
      if (pick < 0) {
        verdict.textContent = "The wrong note is shown in red.";
        verdict.className = "ss-verdict ss-verdict-none";
      } else if (pick === errIdx) {
        verdict.textContent = "✓ You found the wrong note.";
        verdict.className = "ss-verdict ss-verdict-good";
      } else {
        verdict.textContent =
          "✗ You tapped note " + (pick + 1) + "; the wrong note is in red.";
        verdict.className = "ss-verdict ss-verdict-bad";
      }
    }
    return true;
  }

  function run() {
    var isBack = !!document.getElementById("error-back");
    var tries = 0;
    var timer = setInterval(function () {
      tries += 1;
      if (ready()) {
        var ok = isBack ? revealBack() : bindFront();
        if (ok) {
          clearInterval(timer);
          return;
        }
      }
      if (tries >= 175) clearInterval(timer);
    }, 40);
  }

  window.SightSingingErrorDetect = run;
  run();
})();
