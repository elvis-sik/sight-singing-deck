/* global window, document */
(function () {
  "use strict";

  var currentAudio = null;

  function files() {
    if (window.sightSingingAudioFiles) {
      return window.sightSingingAudioFiles;
    }
    return {};
  }

  function makeAudio(filename) {
    var name = String(filename || "").trim();
    if (!name) return null;
    var resolved = name;
    try {
      resolved = String(new URL(name, document.baseURI));
    } catch (e) {}
    var a = new Audio(resolved);
    a.preload = "auto";
    return a;
  }

  function stopCurrent() {
    if (!currentAudio) return;
    try {
      currentAudio.pause();
      currentAudio.currentTime = 0;
    } catch (e) {}
    currentAudio = null;
  }

  window.sightSingingButton = function (action) {
    if (window.Audio == undefined) {
      return false;
    }
    var src = files();
    var a = makeAudio(src[action]);
    if (!a) {
      return false;
    }
    stopCurrent();
    try {
      currentAudio = a;
      var pr = a.play();
      if (pr !== undefined && pr.then) {
        pr.catch(function () {});
      }
    } catch (e) {}
    return false;
  };
})();
