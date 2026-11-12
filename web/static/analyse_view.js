// Drawing for the Analyse page: the frame with mask / edge / sampling rectangles (like the step 5-7 verification
// figures), the intensity profile along the edge, the frame × x map, the results table and the CSV text.
import { esc } from './core.js';

// Viridis anchors (the colour map the step 7 figures use), linearly interpolated.
const VIR = [[68, 1, 84], [59, 82, 139], [33, 145, 140], [94, 201, 98], [253, 231, 37]];
export function viridis(t) {
  t = Math.min(1, Math.max(0, Number.isFinite(t) ? t : 0)) * (VIR.length - 1);
  const i = Math.min(VIR.length - 2, Math.floor(t)), f = t - i, a = VIR[i], b = VIR[i + 1];
  return `rgb(${a.map((v, k) => Math.round(v + (b[k] - v) * f)).join(',')})`;
}

export const fmt = (v, d = 2) => (v == null || Number.isNaN(v) ? '—' : Number(v).toFixed(d));

// Contrast limits as the verification figures use them: 1st and 99.5th percentile of the frame.
function limits(img) {
  const s = Float32Array.from(img).sort(), q = p => s[Math.min(s.length - 1, Math.floor((s.length - 1) * p))];
  return [q(0.01), q(0.995)];
}

export function intensityRange(frames) {
  const v = frames.flatMap(f => f.rects.filter(r => r.accepted).map(r => r.intensity)).filter(Number.isFinite);
  return v.length ? [Math.min(...v), Math.max(...v)] : [0, 1];
}

// Draw frame `res.frame` of the stack with overlays into canvas; opts: { mask, edge, rects, points, range }.
export function drawFrame(canvas, stack, res, opts) {
  const { w, h } = stack, i = res.frame, s = Math.max(1, Math.min(8, Math.ceil(900 / Math.max(w, h))));
  canvas.width = w * s; canvas.height = h * s;
  const off = document.createElement('canvas');
  off.width = w; off.height = h;
  const octx = off.getContext('2d'), id = octx.createImageData(w, h), img = stack.images[i], m = stack.masks[i];
  const [lo, hi] = limits(img), span = hi > lo ? hi - lo : 1;
  for (let k = 0; k < w * h; k++) {
    const g = Math.max(0, Math.min(255, Math.round((img[k] - lo) / span * 255)));
    const tint = opts.mask && m[k] ? 0.82 : 1;
    id.data[4 * k] = g * tint; id.data[4 * k + 1] = g; id.data[4 * k + 2] = g * tint; id.data[4 * k + 3] = 255;
  }
  octx.putImageData(id, 0, 0);
  const ctx = canvas.getContext('2d');
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(off, 0, 0, w * s, h * s);
  const X = p => (p[1] + 0.5) * s, Y = p => (p[0] + 0.5) * s;
  if (opts.edge && res.edge.length) {
    ctx.strokeStyle = '#ff4d4d'; ctx.lineWidth = Math.max(1.5, s * 0.4); ctx.beginPath();
    res.edge.forEach((p, k) => (k ? ctx.lineTo(X(p), Y(p)) : ctx.moveTo(X(p), Y(p))));
    ctx.stroke();
  }
  const [a, b] = opts.range;
  if (opts.rects) {
    for (const r of res.rects) {
      if (!r.corners) continue;
      ctx.beginPath();
      r.corners.forEach((p, k) => (k ? ctx.lineTo(X(p), Y(p)) : ctx.moveTo(X(p), Y(p))));
      ctx.closePath();
      if (r.accepted) {
        ctx.globalAlpha = 0.5; ctx.fillStyle = viridis(b > a ? (r.intensity - a) / (b - a) : 0.5); ctx.fill();
        ctx.globalAlpha = 1; ctx.strokeStyle = '#ffffff'; ctx.setLineDash([]);
      } else { ctx.strokeStyle = '#ff5cc8'; ctx.setLineDash([4, 4]); }
      ctx.lineWidth = 1; ctx.stroke(); ctx.setLineDash([]);
    }
  }
  if (opts.points) {
    for (const p of res.sampled) {
      if (Number.isNaN(p[0])) continue;
      ctx.beginPath(); ctx.arc(X(p), Y(p), Math.max(3, s * 0.9), 0, 2 * Math.PI);
      ctx.fillStyle = '#ffd400'; ctx.fill(); ctx.strokeStyle = '#c00'; ctx.lineWidth = 1.5; ctx.stroke();
    }
  }
}

function axes(W, H, m, xr, yr, xl, yl, yTicks = true) {
  const sx = v => m.l + (v - xr[0]) / (xr[1] - xr[0] || 1) * (W - m.l - m.r);
  const sy = v => H - m.b - (v - yr[0]) / (yr[1] - yr[0] || 1) * (H - m.t - m.b);
  const ticks = (r, n = 5) => Array.from({ length: n + 1 }, (_, k) => r[0] + (r[1] - r[0]) * k / n);
  let g = `<rect class="axis-box" x="${m.l}" y="${m.t}" width="${W - m.l - m.r}" height="${H - m.t - m.b}"/>`;
  for (const t of ticks(xr)) g += `<line class="grid-l" x1="${sx(t)}" x2="${sx(t)}" y1="${m.t}" y2="${H - m.b}"/><text x="${sx(t)}" y="${H - m.b + 14}" text-anchor="middle">${+t.toFixed(1)}</text>`;
  if (yTicks) for (const t of ticks(yr, 4)) g += `<line class="grid-l" x1="${m.l}" x2="${W - m.r}" y1="${sy(t)}" y2="${sy(t)}"/><text x="${m.l - 6}" y="${sy(t) + 4}" text-anchor="end">${+t.toPrecision(3)}</text>`;
  g += `<text class="axis-label" x="${(W + m.l - m.r) / 2}" y="${H - 4}" text-anchor="middle">${esc(xl)}</text>
    <text class="axis-label" transform="translate(13 ${(H - m.b + m.t) / 2}) rotate(-90)" text-anchor="middle">${esc(yl)}</text>`;
  return { g, sx, sy };
}

// Intensity vs x-position of the accepted rectangles of one frame (step 7's "Intensity vs X-Position" panel).
export function profileSvg(res, width, range) {
  const pts = res.rects.filter(r => r.accepted && Number.isFinite(r.intensity)).map(r => [r.edge_point[1], r.intensity]).sort((p, q) => p[0] - q[0]);
  const W = 520, H = 300, m = { l: 58, r: 14, t: 12, b: 40 };
  const yr = pts.length ? [Math.min(...pts.map(p => p[1])), Math.max(...pts.map(p => p[1]))] : [0, 1];
  if (yr[0] === yr[1]) { yr[0] -= 1; yr[1] += 1; }
  const { g, sx, sy } = axes(W, H, m, [0, width - 1], yr, 'edge point x (px)', 'mean intensity in rectangle');
  const [a, b] = range;
  const line = pts.map((p, k) => `${k ? 'L' : 'M'}${sx(p[0]).toFixed(1)},${sy(p[1]).toFixed(1)}`).join('');
  const dots = pts.map(p => `<circle cx="${sx(p[0]).toFixed(1)}" cy="${sy(p[1]).toFixed(1)}" r="4.5" fill="${viridis(b > a ? (p[1] - a) / (b - a) : 0.5)}" stroke="#000" stroke-width="1"><title>x ${fmt(p[0], 1)} px: ${fmt(p[1], 3)}</title></circle>`).join('');
  return `<svg class="plot" viewBox="0 0 ${W} ${H}" role="img" aria-label="Intensity profile along the edge, frame ${res.frame}">${g}
    <path d="${line}" fill="none" stroke="var(--accent)" stroke-width="1.5" opacity=".7"/>${dots}
    ${pts.length ? '' : `<text x="${W / 2}" y="${H / 2}" text-anchor="middle">no accepted rectangles in this frame</text>`}</svg>`;
}

// Frame × x map: every accepted rectangle drawn over its x-extent in its frame row, coloured by intensity.
export function mapSvg(frames, width, range) {
  const T = frames.length, W = 520, H = Math.max(140, Math.min(420, 30 + T * 22)), m = { l: 58, r: 14, t: 10, b: 40 };
  const fr = [frames[0].frame - 0.5, frames[T - 1].frame + 0.5];
  const { g, sx } = axes(W, H, m, [0, width - 1], [0, 1], 'x (px)', 'frame', false);
  const rowH = (H - m.t - m.b) / (fr[1] - fr[0]), [a, b] = range;
  let cells = '', labels = '';
  for (const f of frames) {
    const y = m.t + (f.frame - fr[0] - 0.5) * rowH;
    labels += `<text x="${m.l - 6}" y="${y + rowH / 2 + 4}" text-anchor="end">${f.frame}</text>`;
    for (const r of f.rects) {
      if (!r.accepted || !r.corners) continue;
      const xs = r.corners.map(c => c[1]), x0 = sx(Math.max(0, Math.min(...xs))), x1 = sx(Math.min(width - 1, Math.max(...xs)));
      cells += `<rect x="${x0.toFixed(1)}" y="${(y + 1).toFixed(1)}" width="${Math.max(1, x1 - x0).toFixed(1)}" height="${Math.max(1, rowH - 2).toFixed(1)}" fill="${viridis(b > a ? (r.intensity - a) / (b - a) : 0.5)}" opacity=".85"><title>frame ${f.frame}, x ${fmt(r.edge_point[1], 1)}: ${fmt(r.intensity, 3)}</title></rect>`;
    }
  }
  return `<svg class="plot" viewBox="0 0 ${W} ${H}" role="img" aria-label="Intensity along the edge for every frame">${g}${cells}${labels}</svg>`;
}

export function tableHtml(res, um) {
  const rows = res.rects.map(r => `<tr><td class="num">${r.point_index}</td><td class="num">${fmt(r.edge_point[1], 1)}</td>
    <td class="num">${fmt(r.edge_point[0], 1)}</td><td>${r.accepted ? 'yes' : '<span class="status-bad">no</span>'}</td>
    <td class="num">${fmt(r.coverage, 3)}</td><td class="num">${fmt(r.rotation_angle, 0)}°</td><td class="num">${r.pixels.length}</td>
    <td class="num">${fmt(r.intensity, 3)}</td></tr>`).join('');
  return `<div class="scroll"><table><thead><tr><th>#</th><th>x (px)</th><th>y (px)</th><th>accepted</th><th>coverage</th>
    <th>angle</th><th>pixels</th><th>mean intensity</th></tr></thead><tbody>${rows || '<tr><td colspan="8" class="mute">No sampling points in this frame.</td></tr>'}</tbody></table></div>
    ${um ? `<p class="small mute">Pixel size from the file: ${fmt(um, 4)} µm/px (x in µm = x px × ${fmt(um, 4)}).</p>` : ''}`;
}

export function csvText(frames, params, meta) {
  const head = [`# cell_edge_analysis web export (JS port of steps 1, 2, 5, 6, 7); image ${meta.image}; mask ${meta.mask}`,
    `# um_per_px ${meta.um ?? 'not recorded in the file'} (${meta.scaleSource}); coordinates in pixels, (y, x) = (row, column)`,
    `# params ${JSON.stringify(params)}`];
  const cols = ['frame', 'point_index', 'x_px', 'y_px', 'accepted', 'coverage', 'rotation_angle', 'n_pixels', 'mean_intensity'];
  if (meta.um) cols.push('x_um', 'y_um');
  const lines = [cols.join(',')];
  for (const f of frames) {
    for (const r of f.rects) {
      const v = [f.frame, r.point_index, r.edge_point[1], r.edge_point[0], r.accepted, r.coverage, r.rotation_angle, r.pixels.length,
        Number.isFinite(r.intensity) ? r.intensity : ''];
      if (meta.um) v.push(r.edge_point[1] * meta.um, r.edge_point[0] * meta.um);
      lines.push(v.map(x => (Number.isNaN(x) ? '' : x)).join(','));
    }
  }
  return head.concat(lines).join('\n') + '\n';
}
