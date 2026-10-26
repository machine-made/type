/* Weft page: playground, FRAG rows, glyph map, readability report, commits.
   The data comes from data/*.json, which site/build.py writes from the font. */
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

  function getJSON(path) {
    return fetch(root + path, { cache: "no-cache" }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status + " for " + path);
      return r.json();
    });
  }

  function hex(u) {
    var s = u.toString(16).toUpperCase();
    while (s.length < 4) s = "0" + s;
    return "U+" + s;
  }

  /* FRAG stages. Keep in step with the stage list on the page. */
  function fragStage(v) {
    if (v === 0) return ["safe", "Clean · safe for body text"];
    if (v <= 15) return ["safe", "Ink-trap notches · safe for body text"];
    if (v <= 50) return ["head", "Cuts · headings only"];
    return ["title", "Broken · titles and marks only"];
  }

  /* ---------- playground ---------- */
  function setupPlayground(data) {
    var axes = data.axes || {};
    var hasW = !!axes.wght, hasF = !!axes.FRAG;
    var stage = $("stage-text"), txt = $("txt");
    var wght = $("wght"), frag = $("frag"), size = $("size");

    if (hasW) {
      wght.min = axes.wght[0]; wght.max = axes.wght[2]; wght.value = axes.wght[1];
    } else {
      $("wght-field").hidden = true;
      $("wght-missing").hidden = false;
    }
    if (hasF) {
      frag.min = axes.FRAG[0]; frag.max = axes.FRAG[2]; frag.value = axes.FRAG[1];
      $("frag-field").hidden = false;
      $("frag-missing").hidden = true;
    }
    if (window.innerWidth < 640) size.value = 44;

    function apply() {
      var parts = [];
      if (hasW) parts.push('"wght" ' + wght.value);
      if (hasF) parts.push('"FRAG" ' + frag.value);
      stage.style.fontVariationSettings = parts.length ? parts.join(", ") : "normal";
      stage.style.fontSize = size.value + "px";
      $("size-out").textContent = size.value + " px";
      if (hasW) $("wght-out").textContent = wght.value;
      if (hasF) {
        var v = +frag.value, st = fragStage(v), chip = $("frag-stage");
        $("frag-out").textContent = v;
        chip.dataset.k = st[0];
        chip.textContent = st[1];
        frag.setAttribute("aria-valuetext", v + ", " + st[1]);
      }
    }
    txt.addEventListener("input", function () { stage.textContent = txt.value || " "; });
    [wght, frag, size].forEach(function (i) { i.addEventListener("input", apply); });
    apply();
  }

  /* ---------- FRAG rows ---------- */
  function setupAxisRows(data) {
    if (!data.axes || !data.axes.FRAG) return;
    var box = $("axis-rows"), lo = data.axes.FRAG[0], hi = data.axes.FRAG[2];
    [0, 8, 15, 30, 50, 70, 100].forEach(function (v) {
      if (v < lo || v > hi) return;
      var row = el("div", { "class": "axis-row" });
      var lab = el("div");
      lab.appendChild(el("span", { "class": "v" }, String(v)));
      lab.appendChild(el("span", { "class": "s" }, fragStage(v)[1].split(" · ")[0]));
      var t = el("div", { "class": "t", "aria-label": "Weft 0042 at FRAG " + v }, "Weft 0042");
      t.style.fontVariationSettings = '"FRAG" ' + v;
      row.appendChild(lab);
      row.appendChild(t);
      box.appendChild(row);
    });
    box.hidden = false;
    $("axis-rows-missing").hidden = true;
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

  /* ---------- look-alikes: name the characters this build does not have ---------- */
  function setupLookalikes(data) {
    var have = {};
    (data.glyphs || []).forEach(function (g) { g.chars.forEach(function (c) { have[c.u] = 1; }); });
    var missing = {};
    Array.prototype.forEach.call(document.querySelectorAll("#look-list li"), function (li) {
      Array.from(li.textContent).forEach(function (ch) {
        var u = ch.codePointAt(0);
        if (ch.trim() && !have[u]) missing[ch] = 1;
      });
    });
    var m = Object.keys(missing);
    if (m.length) {
      var n = $("look-note");
      n.textContent = "Not in this build yet, so shown in a fallback font: " + m.join(" ") + ".";
      n.hidden = false;
    }
  }

  /* ---------- readability ---------- */
  function pct(x) {
    var p = x * 100;
    return (p < 10 ? p.toFixed(2) : p.toFixed(1)) + " %";
  }

  function setupReadability() {
    getJSON("data/readability.json").then(function (r) {
      if (!r || r.status !== "ok" || !r.rows || !r.rows.length) return;
      var box = $("read-report");
      box.textContent = "";
      var base = null;
      r.rows.forEach(function (row) { if (row.frag === 0) base = row.cer; });
      var max = Math.max.apply(null, r.rows.map(function (x) { return x.cer; }).concat([0.0001]));
      var tbl = el("table", { "class": "cer-table" });
      var meta = r.meta || {};
      var cap = "OCR character error rate by FRAG level";
      if (meta.engine || meta.ocr) cap += ", " + (meta.engine || meta.ocr);
      if (meta.size_px) cap += ", " + meta.size_px + " px";
      if (meta.date) cap += ", " + meta.date;
      tbl.appendChild(el("caption", null, cap + ". Lower is better."));
      var thead = el("thead"), hr = el("tr");
      ["FRAG", "Stage", "CER", ""].forEach(function (h, i) {
        var th = el("th", { scope: "col" }, h);
        if (i === 3) th.appendChild(el("span", { "class": "visually-hidden" }, "Bar"));
        hr.appendChild(th);
      });
      thead.appendChild(hr);
      tbl.appendChild(thead);
      var tb = el("tbody");
      r.rows.forEach(function (row) {
        var tr = el("tr");
        var limit = typeof meta.threshold === "number" ? meta.threshold : null;
        var over = limit !== null ? row.cer > limit : (row.frag <= 15 && base !== null && row.cer > base * 1.5 + 0.002);
        if (over) tr.className = "over";
        tr.appendChild(el("td", { "class": "num" }, String(row.frag)));
        tr.appendChild(el("td", null, fragStage(row.frag)[1].split(" · ")[0]));
        tr.appendChild(el("td", { "class": "num" }, pct(row.cer)));
        var bc = el("td", { "class": "cer-cell", "aria-hidden": "true" });
        var bar = el("div", { "class": "cer-bar" });
        bar.style.width = Math.max(0.5, row.cer / max * 100) + "%";
        bc.appendChild(bar);
        tr.appendChild(bc);
        tb.appendChild(tr);
      });
      tbl.appendChild(tb);
      box.appendChild(tbl);
      box.appendChild(el("p", { "class": "note" },
        "Source: proofs/weft/readability.json in the repo, read when the site is built."));
    }).catch(function () { /* Keep the "report pending" text. */ });
  }

  /* ---------- commits ---------- */
  function setupCommits(data) {
    var ul = $("commits");
    ul.textContent = "";
    var rows = (data.commits || []).slice(0, 6);
    if (!rows.length) {
      ul.appendChild(el("li", { "class": "muted" }, "The commit list is not available in this build."));
      return;
    }
    rows.forEach(function (c) {
      var li = el("li");
      var a = el("a", { "class": "sha", href: "https://github.com/machine-made/type/commit/" + c.sha }, c.short);
      li.appendChild(a);
      li.appendChild(el("span", null, c.subject));
      li.appendChild(el("span", { "class": "meta" }, c.date + (c.agent ? " · agent commit" : "")));
      ul.appendChild(li);
    });
  }

  getJSON("data/weft.json").then(function (data) {
    setupPlayground(data);
    setupAxisRows(data);
    setupGlyphs(data);
    setupLookalikes(data);
    setupCommits(data);
  }).catch(function (err) {
    $("glyph-map").textContent = "The character map cannot load: " + err.message + ".";
    setupPlayground({ axes: {} });
  });
  setupReadability();
})();
