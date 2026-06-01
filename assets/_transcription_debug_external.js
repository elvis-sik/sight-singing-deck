/* global window, document */
(function () {
  "use strict";

  function init(root) {
    if (!root || root.dataset.debugInit === "1") return;
    root.dataset.debugInit = "1";

    var state = {
      mode: "note",
      duration: "q",
      slots: ["", "", "", "", "", "", "", ""],
    };

    function render() {
      var buttons = root.querySelectorAll("[data-action]");
      for (var i = 0; i < buttons.length; i++) {
        var btn = buttons[i];
        var active =
          (btn.dataset.action === "mode" && btn.dataset.value === state.mode) ||
          (btn.dataset.action === "duration" && btn.dataset.value === state.duration);
        btn.classList.toggle("debug-active", active);
      }

      var status = root.querySelector("[data-role='status']");
      if (status) {
        status.textContent =
          "Selected: " + state.mode + " / " + state.duration;
      }

      var slots = root.querySelectorAll("[data-slot]");
      for (var j = 0; j < slots.length; j++) {
        var slot = slots[j];
        slot.textContent = state.slots[j];
      }
    }

    function activateSlot(index) {
      if (index < 0 || index >= state.slots.length) return;
      if (state.mode === "erase") {
        state.slots[index] = "";
      } else if (state.mode === "rest") {
        state.slots[index] = "R:" + state.duration;
      } else {
        state.slots[index] = "N:" + state.duration;
      }
      render();
    }

    function bindEvent(el, type, handler) {
      el.addEventListener(type, handler);
    }

    var eventType = root.dataset.bindEvent || "click";

    var controls = root.querySelectorAll("[data-action]");
    for (var c = 0; c < controls.length; c++) {
      bindEvent(controls[c], eventType, function (event) {
        event.preventDefault();
        var target = event.currentTarget;
        if (target.dataset.action === "mode") {
          state.mode = target.dataset.value;
        } else if (target.dataset.action === "duration") {
          state.duration = target.dataset.value;
        } else if (target.dataset.action === "reset") {
          state.slots = ["", "", "", "", "", "", "", ""];
        }
        render();
      });
    }

    var slots = root.querySelectorAll("[data-slot]");
    for (var s = 0; s < slots.length; s++) {
      bindEvent(slots[s], eventType, function (event) {
        event.preventDefault();
        activateSlot(Number(event.currentTarget.dataset.slot || -1));
      });
    }

    render();
  }

  function boot() {
    var root = document.querySelector("[data-debug-root]");
    if (root) init(root);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
