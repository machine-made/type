/* Shuttle page: playground (wght, wdth, size) and glyph map.
   The data comes from data/shuttle.json, which site/build.py writes from the font. */
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

  /* ---------- playground ---------- */
  function setupPlayground(data) {
    var axes = data.axes || {};
    var stage = $("stage-text"), txt = $("txt");
    var wght = $("wght"), wdth = $("wdth"), size = $("size");
    var has = { wght: !!axes.wght, wdth: !!axes.wdth };

    if (has.wght) { wght.min = axes.wght[0]; wght.max = axes.wght[2]; }
    else { $("wght-field").hidden = true; }
    if (has.wdth) { wdth.min = axes.wdth[0]; wdth.max = axes.wdth[2]; }
    else { $("wdth-field").hidden = true; }
    if (!has.wght && !has.wdth) $("axes-missing").hidden = false;
    if (window.innerWidth < 640) size.value = 48;

    function apply() {
      var parts = [];
      if (has.wght) parts.push('"wght" ' + wght.value);
      if (has.wdth) parts.push('"wdth" ' + wdth.value);
      stage.style.fontVariationSettings = parts.length ? parts.join(", ") : "normal";
      stage.style.fontSize = size.value + "px";
      $("size-out").textContent = size.value + " px";
      $("wght-out").textContent = wght.value;
      $("wdth-out").textContent = wdth.value;
    }
    txt.addEventListener("input", function () { stage.textContent = txt.value || " "; });
    [wght, wdth, size].forEach(function (i) { i.addEventListener("input", apply); });
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

  fetch(root + "data/shuttle.json", { cache: "no-cache" }).then(function (r) {
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }).then(function (data) {
    setupPlayground(data);
    setupGlyphs(data);
  }).catch(function (err) {
    $("glyph-map").textContent = "The character map cannot load: " + err.message + ".";
    setupPlayground({ axes: {} });
  });
})();
