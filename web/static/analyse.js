// Analyse page: load an image stack + mask stack (TIFF) or the synthetic demo, set the pipeline parameters, and see
// the edge, sampling rectangles and intensity profile per frame. The analysis is edge_engine.js (JS port of steps
// 1, 2, 5, 6, 7) in both modes; the local app also reads compressed TIFFs (POST /api/tiff) and re-runs a frame with
// the repo's Python (POST /api/analyse) for comparison.
import { route, app, api, esc, isStatic, download, needsServer } from './core.js';
import { readTiff, fromServer, TiffError } from './tiff.js';
import { runPipeline } from './edge_engine.js';
import { renderParams } from './analyse_params.js';
import { drawFrame, profileSvg, mapSvg, tableHtml, csvText, intensityRange, fmt } from './analyse_view.js';

// Kept across visits so a loaded stack survives navigating away and back.
const S = { stack: null, meta: null, files: null, params: null, frame: 0, res: null, all: null,
  show: { mask: true, edge: true, points: true, rects: true } };
const AUTO_ALL = 4e6;  // run every frame automatically when frames × pixels is at most this

async function loadTiff(file) {
  const buf = await file.arrayBuffer();
  try { return readTiff(buf); } catch (e) {
    if (!(e instanceof TiffError) || isStatic()) throw new Error(`${file.name}: ${e.message}`);
    const fd = new FormData(); fd.append('file', file, file.name);
    return fromServer(await api('/tiff', { body: fd }));  // local app: tifffile reads compressed files too
  }
}

async function setStack(imageFile, maskFile, demo) {
  const [im, mk] = await Promise.all([loadTiff(imageFile), loadTiff(maskFile)]);
  if (im.w !== mk.w || im.h !== mk.h) throw new Error(`Image frames are ${im.w}×${im.h} px but mask frames are ${mk.w}×${mk.h} px.`);
  if (im.frames.length !== mk.frames.length) throw new Error(`The image stack has ${im.frames.length} frames but the mask stack has ${mk.frames.length}.`);
  S.stack = { images: im.frames, masks: mk.frames.map(f => Uint8Array.from(f, v => (v > 0 ? 1 : 0))), h: im.h, w: im.w };
  S.meta = { image: imageFile.name, mask: maskFile.name, um: im.um_per_px, scaleSource: im.scale_source, demo, bits: im.bits };
  S.files = { image: imageFile, mask: maskFile };
  S.frame = 0; S.res = null; S.all = null;
}

async function demoFiles(info) {
  const get = async (url) => { const r = await fetch(url); if (!r.ok) throw new Error(`${r.status} ${url}`); return new File([await r.blob()], url.split('/').pop()); };
  return Promise.all([get(info.demo.image), get(info.demo.mask)]);
}

function sourceNote(info) {
  if (!S.meta) return '<span class="mute">No stack loaded yet.</span>';
  const { stack: st, meta: m } = S;
  const scale = m.um ? `${fmt(m.um, 4)} µm/px (${esc(m.scaleSource)})` : 'pixel size not recorded in the file (results are in pixels)';
  return `${m.demo ? `<span class="sim-badge">SYNTHETIC</span> ${esc(info.demo.note.replace(/^SYNTHETIC /, "Synthetic "))}<br>` : ''}
    <b>${esc(m.image)}</b> + <b>${esc(m.mask)}</b>: ${st.images.length} frame${st.images.length > 1 ? 's' : ''} of ${st.w}×${st.h} px; ${scale}.`;
}

route('analyse', async (args) => {
  const info = await api('/info');
  S.params = S.params || { ...info.defaults };
  app().innerHTML = `<p class="kicker">Analysis</p><h1>Fluorescence along the cell edge</h1>
    <p class="lead">The cell edge from each mask frame, sampling rectangles just inside it, and the mean fluorescence in
      each rectangle: steps 1, 2, 5, 6 and 7 of the pipeline.</p>
    <div class="callout a small">${isStatic()
      ? 'Runs <b>in your browser</b> (JavaScript port of the repo\'s Python, checked against it by a test). Nothing is uploaded. Uncompressed TIFF only here; the local app also opens compressed files.'
      : 'Runs in the browser (the same JavaScript port as the static site). This local app also opens compressed TIFFs with Python tifffile and can re-run a frame with the repo\'s Python steps ("Check with Python").'}</div>
    <div class="panel"><h3 style="margin-top:0">1 · Data</h3>
      <div class="row">
        <div><label for="f-img">Fluorescence stack (TIFF, e.g. ${esc(info.file_patterns.image[0])})</label><input id="f-img" type="file" accept=".tif,.tiff"></div>
        <div><label for="f-msk">Cell mask stack (TIFF, e.g. ${esc(info.file_patterns.mask[0])}; nonzero = cell)</label><input id="f-msk" type="file" accept=".tif,.tiff"></div>
      </div>
      <button id="b-load" type="button">Load stacks</button><button id="b-demo" class="alt" type="button">Use the synthetic demo</button>
      <p id="src" class="small" role="status">${sourceNote(info)}</p></div>
    <div class="panel"><h3 style="margin-top:0">2 · Parameters</h3><div id="params"></div></div>
    <div id="results"></div>`;
  const $ = id => document.getElementById(id);
  const status = (html, bad) => { $('src').innerHTML = bad ? `<span class="status-bad">${html}</span>` : html; };

  const load = async (fn) => {
    $('b-load').disabled = $('b-demo').disabled = true;
    status('Reading...');
    try { await fn(); status(sourceNote(info)); analyse(info); }
    catch (e) { status(esc(e.message) + (isStatic() && /compressed|BigTIFF/.test(e.message) ? ' ' + needsServer('Opening compressed TIFFs') : ''), true); }
    finally { $('b-load').disabled = $('b-demo').disabled = false; }
  };
  $('b-load').onclick = () => {
    const a = $('f-img').files[0], b = $('f-msk').files[0];
    if (!a || !b) return status('Choose both an image stack and a mask stack.', true);
    load(() => setStack(a, b, false));
  };
  $('b-demo').onclick = () => load(async () => { const [a, b] = await demoFiles(info); await setStack(a, b, true); });
  renderParams($('params'), info, S.params, p => { S.params = p; S.all = null; analyse(info); });

  if (S.stack) analyse(info);
  else if (args[0] === 'demo') $('b-demo').click();
});

function analyse(info) {
  if (!S.stack) return;
  const T = S.stack.images.length;
  S.frame = Math.min(S.frame, T - 1);
  try {
    S.res = runPipeline(S.stack, S.params, [S.frame])[0];
    if (!S.all && T * S.stack.w * S.stack.h <= AUTO_ALL) S.all = runPipeline(S.stack, S.params);
  } catch (e) {
    document.getElementById('results').innerHTML = `<p class="err">${esc(e.message)}</p>`;
    return;
  }
  renderResults(info);
}

function summary(res) {
  const acc = res.rects.filter(r => r.accepted), vals = acc.map(r => r.intensity).filter(Number.isFinite);
  const mean = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : NaN;
  return `<div class="tiles">
    <div class="tile"><b>${res.edge.length}</b><span>edge points</span></div>
    <div class="tile"><b>${res.sampled.filter(p => !Number.isNaN(p[0])).length}</b><span>sampling points</span></div>
    <div class="tile"><b>${acc.length}/${res.rects.length}</b><span>rectangles accepted</span></div>
    <div class="tile"><b>${fmt(mean, 2)}</b><span>mean intensity</span></div></div>`;
}

function renderResults(info) {
  const host = document.getElementById('results'), T = S.stack.images.length;
  host.innerHTML = `<div class="panel"><h3 style="margin-top:0">3 · Results</h3>
    <div class="ctl"><label for="fr" id="fr-l"></label>
      <input id="fr" type="range" min="0" max="${T - 1}" step="1" value="${S.frame}" ${T > 1 ? '' : 'disabled'}></div>
    <div class="toggles">${Object.entries({ mask: 'mask tint', edge: 'edge (red)', points: 'sampling points', rects: 'rectangles' })
      .map(([k, l]) => `<label for="t-${k}"><input id="t-${k}" type="checkbox" ${S.show[k] ? 'checked' : ''}>${l}</label>`).join('')}</div>
    <div id="sum"></div>
    <div class="viewer"><div><div class="stage"><canvas id="cv" role="img"></canvas></div>
        <p class="small mute">Contrast 1st-99.5th percentile. Filled rectangles are accepted (colour = mean intensity),
          dashed magenta ones are rejected (coverage below ${S.params.min_cell_coverage}).</p></div>
      <div><h3 style="margin:0">Profile along the edge</h3><div id="prof"></div>
        <div class="cbar" aria-hidden="true"></div><div class="cbar-l" id="cbar-l"></div></div></div>
    <h3>All frames</h3><div id="map"></div>
    <div><button id="b-csv" type="button">CSV: this frame</button><button id="b-csv-all" class="alt" type="button">CSV: all frames</button>
      ${isStatic() ? '' : '<button id="b-py" class="alt" type="button">Check with Python</button>'}
      <span id="py" class="small" role="status"></span></div>
    ${isStatic() ? needsServer('"Check with Python" (re-running the frame with the repo\'s own step functions)') : ''}
    <h3 id="tbl-h"></h3><div id="tbl"></div></div>`;
  const $ = id => document.getElementById(id);
  $('fr').oninput = e => {
    S.frame = +e.target.value;
    S.res = runPipeline(S.stack, S.params, [S.frame])[0];
    $('py').textContent = '';
    updateFrame();
  };
  for (const k of Object.keys(S.show)) $(`t-${k}`).onchange = e => { S.show[k] = e.target.checked; updateFrame(); };
  const base = (S.meta.image || 'stack').replace(/\.tiff?$/i, '');
  $('b-csv').onclick = () => download(`${base}_frame${S.frame}_edge_intensity.csv`, csvText([S.res], S.params, S.meta), 'text/csv');
  $('b-csv-all').onclick = () => {
    S.all = S.all || runPipeline(S.stack, S.params);
    download(`${base}_edge_intensity.csv`, csvText(S.all, S.params, S.meta), 'text/csv');
  };
  if ($('b-py')) $('b-py').onclick = () => checkPython();
  updateMap(info);
  updateFrame();
}

function updateMap(info) {
  const el = document.getElementById('map'), range = intensityRange(S.all || [S.res]);
  el.innerHTML = S.all ? mapSvg(S.all, S.stack.w, range) + '<p class="small mute">Each accepted rectangle over its x-extent, one row per frame, coloured by mean intensity.</p>'
    : '<p class="small mute">Large stack: frames are analysed one at a time.</p><button id="b-all" class="alt" type="button">Analyse all frames</button>';
  const b = document.getElementById('b-all');
  if (b) b.onclick = () => { S.all = runPipeline(S.stack, S.params); updateMap(info); updateFrame(); };
}

function updateFrame() {
  const $ = id => document.getElementById(id), res = S.res, range = intensityRange(S.all || [res]);
  $('fr-l').innerHTML = `Frame <b>${S.frame}</b> of ${S.stack.images.length - 1}`;
  $('sum').innerHTML = summary(res);
  $('cv').setAttribute('aria-label', `Frame ${S.frame} with the detected edge and sampling rectangles`);
  drawFrame($('cv'), S.stack, res, { ...S.show, range });
  $('prof').innerHTML = profileSvg(res, S.stack.w, range);
  $('cbar-l').innerHTML = `<span>${fmt(range[0], 2)}</span><span>colour scale${S.all ? ' (all frames)' : ''}</span><span>${fmt(range[1], 2)}</span>`;
  $('tbl-h').textContent = `Points in frame ${S.frame}`;
  $('tbl').innerHTML = tableHtml(res, S.meta.um);
}

async function checkPython() {
  const out = document.getElementById('py'), btn = document.getElementById('b-py'), res = S.res;
  btn.disabled = true; out.textContent = 'Running the Python steps...';
  try {
    const fd = new FormData();
    fd.append('image', S.files.image, S.files.image.name); fd.append('mask', S.files.mask, S.files.mask.name);
    fd.append('params', JSON.stringify(S.params)); fd.append('frames', String(res.frame));
    const py = (await api('/analyse', { body: fd })).frames[0];
    let dEdge = 0, dInt = 0, dCov = 0, mism = 0;
    const n = (a, b) => (a == null || Number.isNaN(a) ? (b == null ? 0 : Infinity) : Math.abs(a - (b ?? NaN)) || 0);
    if (py.edge.length !== res.edge.length || py.rects.length !== res.rects.length) mism = Infinity;
    else {
      py.edge.forEach((p, i) => { dEdge = Math.max(dEdge, n(res.edge[i][0], p[0]), n(res.edge[i][1], p[1])); });
      py.rects.forEach((r, i) => {
        const j = res.rects[i];
        if (r.accepted !== j.accepted) mism++;
        dCov = Math.max(dCov, n(j.coverage, r.coverage));
        if (r.accepted && r.rotation_angle === j.rotation_angle) dInt = Math.max(dInt, n(j.intensity, r.intensity) / Math.max(1e-12, Math.abs(r.intensity)));
      });
    }
    const ok = mism === 0 && dEdge < 1e-6 && dCov < 1e-6 && dInt < 1e-5;
    out.innerHTML = Number.isFinite(mism)
      ? `<span class="${ok ? 'status-ok' : 'status-bad'}">Python: ${py.rects.filter(r => r.accepted).length} accepted; max |Δ| edge ${dEdge.toExponential(1)} px, coverage ${dCov.toExponential(1)}, intensity (relative) ${dInt.toExponential(1)}; ${mism} acceptance differences.</span>`
      : `<span class="status-bad">Python found ${py.edge.length} edge points / ${py.rects.length} rectangles; the browser ${res.edge.length} / ${res.rects.length}.</span>`;
  } catch (e) { out.innerHTML = `<span class="status-bad">${esc(e.message)}</span>`; }
  finally { btn.disabled = false; }
}
