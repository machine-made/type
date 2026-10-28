/* Warp page: style switch, playground and glyph map.
   The data comes from data/warp.json, which site/build.py writes from the font. */
(function () {
  "use strict";

  var root = document.body.getAttribute("data-root") || "./";
  var $ = function (id) { return document.getElementById(id); };

  function el(tag, attrs, text) {
    var n = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    }
    if (text !== undefined) n.textContent = text;
    return n;
  }

  function hex(u) {
    var s = u.toString(16).toUpperCase();
    while (s.length < 4) s = "0" + s;
    return "U+" + s;
  }

  /* ---------- style switch and playground ---------- */
  var STYLES = ["regular", "italic", "bold", "bolditalic", "display"];

  function setupPlayground() {
    var stage = $("stage-text"), txt = $("txt"), size = $("size");
    var onum = $("onum"), smcp = $("smcp"), paper = $("paper-text");
    var buttons = Array.prototype.slice.call(document.querySelectorAll(".warp-seg button"));
    if (window.innerWidth < 640) size.value = 40;

    function setStyle(name) {
      STYLES.forEach(function (s) {
        stage.classList.toggle("w-" + s, s === name);
        if (paper) paper.classList.toggle("w-" + s, s === name);
      });
      buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-style") === name)); });
    }
    function apply() {
      stage.style.fontSize = size.value + "px";
      $("size-out").textContent = size.value + " px";
      var f = [];
      if (onum.checked) f.push('"onum" 1');
      if (smcp.checked) f.push('"smcp" 1');
      stage.style.fontFeatureSettings = f.length ? f.join(", ") : "normal";
    }
    buttons.forEach(function (b) {
      b.addEventListener("click", function () { setStyle(b.getAttribute("data-style")); });
    });
    txt.addEventListener("input", function () { stage.textContent = txt.value || " "; });
    [size, onum, smcp].forEach(function (i) { i.addEventListener("input", apply); });
    setStyle("regular");
    apply();
  }

  /* ---------- glyph map ---------- */
  function setupGlyphs(data) {
    var map = $("glyph-map");
    map.textContent = "";
    var count = 0, first = null;
    var big = $("glyph-big"), nm = $("glyph-name"), uu = $("glyph-u"), gg = $("glyph-g");
    var pressed = null;

    function show(btn, c) {
      if (pressed) pressed.setAttribute("aria-pressed", "false");
      btn.setAttribute("aria-pressed", "true");
      pressed = btn;
      big.textContent = String.fromCodePoint(c.u);
      nm.textContent = c.n || "(no name)";
      uu.textContent = hex(c.u);
      gg.textContent = c.g;
    }

    (data.glyphs || []).forEach(function (grp) {
      var sec = el("div", { "class": "glyph-group" });
      var hid = "gg-" + grp.name.toLowerCase().replace(/[^a-z]+/g, "-");
      sec.appendChild(el("h3", { id: hid }, grp.name + " (" + grp.chars.length + ")"));
      var grid = el("div", { "class": "glyph-grid", role: "group", "aria-labelledby": hid });
      grp.chars.forEach(function (c) {
        var b = el("button", { type: "button", "aria-pressed": "false",
          "aria-label": (c.n || hex(c.u)) + ", " + hex(c.u), title: hex(c.u) + " " + c.n },
          String.fromCodePoint(c.u));
        b.addEventListener("click", function () { show(b, c); });
        grid.appendChild(b);
        if (!first) first = [b, c];
        count++;
      });
      sec.appendChild(grid);
      map.appendChild(sec);
    });
    $("glyph-count").textContent = count;
    if (first) show(first[0], first[1]);
  }

  setupPlayground();
  fetch(root + "data/warp.json", { cache: "no-cache" }).then(function (r) {
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }).then(setupGlyphs).catch(function (err) {
    $("glyph-map").textContent = "The character map cannot load: " + err.message + ".";
  });
})();
