/* Copy buttons for the code snippets on the download page. */
(function () {
  "use strict";
  Array.prototype.forEach.call(document.querySelectorAll("button[data-copy]"), function (btn) {
    var label = btn.textContent;
    btn.addEventListener("click", function () {
      var src = document.getElementById(btn.getAttribute("data-copy"));
      if (!src) return;
      var text = src.textContent;
      var done = function (msg) {
        btn.textContent = msg;
        setTimeout(function () { btn.textContent = label; }, 1600);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function () { done("Copied"); }, function () { done("Select and copy"); });
      } else {
        var range = document.createRange();
        range.selectNodeContents(src);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        done("Text selected");
      }
    });
  });
})();
