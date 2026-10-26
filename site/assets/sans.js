/* Sans page: switch the sharp (ss02) row on and off. */
(function () {
  "use strict";
  var box = document.getElementById("sharp-toggle");
  var sample = document.getElementById("sharp-sample");
  if (!box || !sample) return;
  function apply() { sample.classList.toggle("off", !box.checked); }
  box.addEventListener("change", apply);
  apply();
})();
