/*
  Error-detection card interaction — on-the-fly (pick-a-variant).

  The note ships EVERY single-note wrong-performance variant (ErrorVariants);
  the card picks one at random each view, so the wrong note is never at a fixed,
  memorisable spot. Grading and the reveal happen ON THE FRONT (on tap), which
  is the one channel guaranteed to work on Desktop, iOS WebKit and AnkiDroid —
  Anki does not reliably carry JS state from the front render to the back render.

  Front:
    - synchronously pick a variant and point the "melody" clue at its clip
      (before the autoplay timer fires),
    - draw the WRITTEN melody, tappable; the first tap commits: the true wrong
      note turns red, the tap is graded, a verdict shows. Locked after.
  Back (best-effort enhancement): if the front's choice survived into this
    render (Desktop/iOS), re-show the red note + verdict + label and enable
    "As heard"; otherwise a neutral note (the front already revealed it).

  Polls for its dependencies instead of assuming script load order.
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

  function parseVariants() {
    var el = document.getElementById("error-variants");
    if (!el) return [];
    try {
      var arr = JSON.parse(el.textContent.trim());
      return Array.isArray(arr) ? arr : [];
    } catch (e) {
      return [];
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

  function chosenErrorIndex() {
    var chosen = window.__ssErrChosen;
    return chosen && typeof chosen.i === "number" ? chosen.i : -1;
  }

  function currentPick() {
    return typeof window.__ssErrPick === "number" ? window.__ssErrPick : -1;
  }

  function setVerdict(el, pick, errIdx) {
    if (!el) return;
    if (pick < 0) {
      el.textContent = "The wrong note is shown in red.";
      el.className = "ss-verdict ss-verdict-none";
    } else if (pick === errIdx) {
      el.textContent = "✓ You found the wrong note.";
      el.className = "ss-verdict ss-verdict-good";
    } else {
      el.textContent =
        "✗ You tapped note " + (pick + 1) + "; the wrong note is in red.";
      el.className = "ss-verdict ss-verdict-bad";
    }
  }

  /* ---- pick one variant, synchronously, before autoplay fires ------------- */

  function pickVariantForFront() {
    var variants = parseVariants();
    window.__ssErrPick = -1;
    window.__ssErrRevealed = false;
    if (!variants.length) {
      window.__ssErrChosen = null;
      return;
    }
    var k = Math.floor(Math.random() * variants.length);
    if (k >= variants.length) k = variants.length - 1;
    var chosen = variants[k];
    window.__ssErrChosen = chosen;
    if (chosen && chosen.f) window.sightSingingMelodyFile = chosen.f;
  }

  /* ---- front: tap to commit + reveal -------------------------------------- */

  function drawFront(notation, data) {
    var errIdx = chosenErrorIndex();
    var pick = currentPick();
    var revealed = !!window.__ssErrRevealed;
    var styles = {};
    if (revealed) {
      if (errIdx >= 0) styles[errIdx] = badStyle();
      if (pick >= 0 && pick !== errIdx) styles[pick] = accentStyle();
    } else if (pick >= 0) {
      styles[pick] = accentStyle();
    }
    window.SightSingingDrawStaff(notation, data, { styles: styles });

    var groups = notation.querySelectorAll(".vf-stavenote");
    for (var i = 0; i < groups.length; i++) {
      (function (g, idx) {
        g.style.cursor = "pointer";
        g.addEventListener("click", function () {
          if (window.__ssErrRevealed) return; // first tap commits; then locked
          window.__ssErrPick = idx;
          window.__ssErrRevealed = true;
          drawFront(notation, data);
          var v = document.getElementById("error-verdict-front");
          if (v) {
            v.style.display = "";
            setVerdict(v, idx, chosenErrorIndex());
          }
          var chosen = window.__ssErrChosen;
          var prompt = document.getElementById("error-prompt");
          if (prompt && chosen && chosen.label) prompt.textContent = chosen.label;
        });
      })(groups[i], i);
    }
    return groups.length > 0;
  }

  function bindFront() {
    var notation = document.getElementById("notation");
    var data = parseData();
    if (!notation || !data || !data.events || !data.events.length) return false;
    return drawFront(notation, data);
  }

  /* ---- back: enhance if the front's choice survived ----------------------- */

  function revealBack() {
    var notation = document.getElementById("notation");
    var data = parseData();
    if (!notation || !data || !data.events || !data.events.length) return false;

    var chosen = window.__ssErrChosen || null;
    var errIdx = chosenErrorIndex();
    var pick = currentPick();
    if (chosen && chosen.f) window.sightSingingMelodyFile = chosen.f;

    var styles = {};
    if (errIdx >= 0) {
      styles[errIdx] = badStyle();
      if (pick >= 0 && pick !== errIdx) styles[pick] = accentStyle();
    }
    window.SightSingingDrawStaff(notation, data, { styles: styles });

    var verdict = document.getElementById("error-verdict");
    var info = document.getElementById("answer-info");
    if (errIdx < 0) {
      if (verdict) {
        verdict.textContent =
          "The wrong note was shown on the front when you tapped it.";
        verdict.className = "ss-verdict ss-verdict-none";
      }
      if (info) info.textContent = "";
    } else {
      setVerdict(verdict, pick, errIdx);
      if (info) info.textContent = chosen && chosen.label ? chosen.label : "";
    }
    return true;
  }

  /* ---- bootstrap ---------------------------------------------------------- */

  function run() {
    var isBack = !!document.getElementById("error-back");
    if (!isBack) pickVariantForFront(); // sync: sets the melody clip pre-autoplay

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
