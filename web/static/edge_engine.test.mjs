// Node test: the JS port (contours.js, edge_engine.js, tiff.js) against Python reference values in
// tests/fixtures/edge_fixture.json (written by scripts/make_edge_fixture.py with the repo's own step functions).
// Run: node web/static/edge_engine.test.mjs
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { findContours, gaussianFilter1d } from './contours.js';
import { percentile32, runPipeline } from './edge_engine.js';
import { readTiff } from './tiff.js';

const here = dirname(fileURLToPath(import.meta.url)), root = join(here, '..', '..');
const fx = JSON.parse(readFileSync(join(root, 'tests', 'fixtures', 'edge_fixture.json'), 'utf8'));
let fails = 0, checks = 0;
const fail = msg => { fails++; if (fails <= 25) console.error('FAIL', msg); };
function close(a, b, what, rtol = 1e-9, atol = 1e-9) {
  checks++;
  const na = a == null || Number.isNaN(a), nb = b == null || Number.isNaN(b);
  if (na || nb) { if (na !== nb) fail(`${what}: ${a} vs ${b}`); return; }
  if (Math.abs(a - b) > atol + rtol * Math.abs(b)) fail(`${what}: ${a} vs ${b}`);
}
const pts = (a, b, what, tol) => {
  if (a.length !== b.length) return fail(`${what}: ${a.length} points vs ${b.length}`);
  a.forEach((p, i) => { close(p[0], b[i][0], `${what}[${i}].y`, tol); close(p[1], b[i][1], `${what}[${i}].x`, tol); });
};

// contours (exact geometry and order)
fx.contours.forEach((c, k) => {
  const h = c.mask.length, w = c.mask[0].length, js = findContours(Float64Array.from(c.mask.flat()), h, w, 0.5);
  if (js.length !== c.contours.length) return fail(`contour case ${k}: ${js.length} contours vs ${c.contours.length}`);
  js.forEach((cc, j) => pts(cc, c.contours[j], `contour ${k}.${j}`, 0));
});

// gaussian smoothing
for (const g of fx.gaussian) {
  gaussianFilter1d(g.x, g.sigma, g.mode).forEach((v, i) => close(v, g.y[i], `gauss ${g.mode} s=${g.sigma} [${i}]`, 1e-12, 1e-12));
}

// TIFF reader on the demo stack
const load = rel => readTiff(new Uint8Array(readFileSync(join(root, rel))).buffer);
const img = load(fx.demo.image), msk = load(fx.demo.mask);
const [T, H, W] = fx.demo.shape;
if (img.frames.length !== T || img.h !== H || img.w !== W) fail(`demo tiff shape ${img.frames.length}x${img.h}x${img.w}`);
const sum = img.frames.reduce((s, f) => s + f.reduce((a, v) => a + v, 0), 0);
const inMask = msk.frames.reduce((s, f) => s + f.reduce((a, v) => a + (v > 0), 0), 0);
close(sum, fx.demo.checksum[0], 'demo image checksum', 0, 0);
close(inMask, fx.demo.checksum[1], 'demo mask checksum', 0, 0);
close(img.um_per_px, 0.16, 'demo pixel size', 1e-6);

for (const p of fx.percentile) close(percentile32(img.frames[0], p.p), p.value, `percentile ${p.p}`, 1e-6);

// whole pipeline
function compare(stack, c) {
  const js = runPipeline(stack, c.params, c.frames_requested);
  const py = c.result.frames;
  if (js.length !== py.length) return fail(`${c.name}: ${js.length} frames vs ${py.length}`);
  js.forEach((f, k) => {
    const q = py[k], tag = `${c.name} f${q.frame}`;
    if (Array.isArray(q.edge)) pts(f.edge, q.edge, `${tag} edge`, 1e-9);
    else {
      if (f.edge.length !== q.edge.n) fail(`${tag} edge length ${f.edge.length} vs ${q.edge.n}`);
      const s = f.edge.reduce((a, p) => [a[0] + p[0], a[1] + p[1]], [0, 0]);
      close(s[0], q.edge.sum[0], `${tag} edge sum y`, 1e-9); close(s[1], q.edge.sum[1], `${tag} edge sum x`, 1e-9);
      if (q.edge.n) pts([f.edge[0], f.edge[f.edge.length - 1]], [q.edge.first, q.edge.last], `${tag} edge ends`, 1e-9);
    }
    pts(f.sampled, q.sampled, `${tag} sampled`, 1e-9);
    if (f.rects.length !== q.rects.length) return fail(`${tag}: ${f.rects.length} rects vs ${q.rects.length}`);
    f.rects.forEach((r, i) => {
      const e = q.rects[i], t = `${tag} rect ${i}`;
      checks++;
      if (r.accepted !== e.accepted) fail(`${t} accepted ${r.accepted} vs ${e.accepted}`);
      if (r.pixels.length !== e.n_pixels) fail(`${t} n_pixels ${r.pixels.length} vs ${e.n_pixels}`);
      close(r.coverage, e.coverage, `${t} coverage`, 1e-9);
      close(r.rotation_angle, e.rotation_angle, `${t} angle`, 1e-9);
      close(r.intensity, e.intensity, `${t} intensity`, 2e-6, 1e-6);
      if (r.corners) pts(r.corners, e.corners, `${t} corners`, 1e-9);
    });
  });
}
const binary = frames => frames.map(f => Uint8Array.from(f, v => (v > 0 ? 1 : 0)));
const demo = { images: img.frames, masks: binary(msk.frames), h: H, w: W };
for (const c of fx.pipeline) compare(demo, c);
const b = fx.blob, bh = b.masks[0].length, bw = b.masks[0][0].length;
const blob = { images: b.images.map(f => Float32Array.from(f.flat())), masks: b.masks.map(f => Uint8Array.from(f.flat())), h: bh, w: bw };
for (const c of b.pipeline) compare(blob, c);

if (fails) { console.error(`${fails} of ${checks} checks failed`); process.exit(1); }
console.log(`edge_engine: all ${checks} checks agree with Python`);
