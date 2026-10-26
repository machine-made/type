// Render proof lines with the sketch 0.1 renderer (reference only).
// Usage: node sketch_render.js <sketch.html> <out.png> <spec.json>
// The spec gives {width, height, size, lineStep, top, left, lines}.
// Needs @napi-rs/canvas. CI does not run this file.
const fs = require('fs');
const { createCanvas } = require('@napi-rs/canvas');
const [html, outPath, specPath] = process.argv.slice(2);
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const src = fs.readFileSync(html, 'utf8');
const js = src.split('<script>')[1].split('/* ---------- state ---------- */')[0].replace('(function(){', '');
const core = new Function(js + '\nreturn {drawLines};')();
const cv = createCanvas(spec.width, spec.height), ctx = cv.getContext('2d');
const layer = createCanvas(spec.width, spec.height), lctx = layer.getContext('2d');
const s = spec.size / 16;
// drawLines puts the baseline of line i at y + (13 + i*lh)*s.
core.drawLines(lctx, spec.lines, {
  x: spec.left, y: spec.top - 13 * s, size: spec.size, lh: spec.lineStep / s,
  wght: 400, frag: 0, wdth: 100, seed: 7, style: 'solid', ink: '#121314', accent: null,
});
ctx.fillStyle = '#F4F5F3'; ctx.fillRect(0, 0, spec.width, spec.height);
ctx.drawImage(layer, 0, 0);
fs.writeFileSync(outPath, cv.toBuffer('image/png'));
console.log('Wrote ' + outPath);
