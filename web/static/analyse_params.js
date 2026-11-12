// Parameter form for the Analyse page: one fieldset per pipeline step, initial values from /api/info defaults
// (pipeline_defaults.DEFAULTS) and help texts from the step scripts' own comments.
import { esc } from './core.js';

export const PARAM_HELP = {
  subtract_background: 'Subtract a background level (a histogram percentile of each frame) before normalisation.',
  background_percentile: 'Percentile of the frame histogram used as background (0-100).',
  normalize_frames: 'Normalise each frame to its brightest pixel.',
  normalization_scale: 'Scaling factor applied after normalisation (100 gives a 0-100 range).',
  smooth_edges: 'Gaussian smoothing of the edge coordinates (endpoints kept for open edges).',
  smoothing_sigma: 'Sigma of the Gaussian along the contour, in contour points (higher = more smoothing).',
  sampling_method: 'per_frame: n_points per frame; fixed_x: the same x-positions in every frame; dense: every unique x; displacement_like: integer x-positions as in steps 3-4.',
  n_points: 'Number of sampling points (per_frame and fixed_x).',
  target_points_displacement: 'Approximate number of points for displacement_like.',
  exclude_endpoints: 'Leave out the ends of the edge (5 % margin, or one position).',
  y_selection: 'Where the edge has several points at one x: uppermost (smallest y, top) or lowermost.',
  width: 'Rectangle width along the edge (px).',
  depth: 'Rectangle depth into the cell (px).',
  min_cell_coverage: 'Minimum fraction of the rectangle inside the cell mask for it to be accepted.',
  rotation_method: 'vertical: straight down; none: along the inward edge normal; flip: also try 180° if rejected; search: try evenly spaced angles for the best coverage.',
  rotation_search_angles: 'Number of angles (0-360°) tried by search.',
};

const GROUPS = [
  ['Step 1 · preprocessing', ['subtract_background', 'background_percentile', 'normalize_frames', 'normalization_scale']],
  ['Step 2 · edge', ['smooth_edges', 'smoothing_sigma']],
  ['Step 5 · sampling', ['sampling_method', 'n_points', 'target_points_displacement', 'exclude_endpoints', 'y_selection']],
  ['Step 6 · rectangles', ['width', 'depth', 'min_cell_coverage', 'rotation_method', 'rotation_search_angles']],
];
const INTS = new Set(['n_points', 'target_points_displacement', 'width', 'depth', 'rotation_search_angles']);
const STEP = { background_percentile: 'any', normalization_scale: 'any', smoothing_sigma: 'any', min_cell_coverage: 0.05 };
const label = k => k.replace(/_/g, ' ');

function field(k, v, choices) {
  const id = `p-${k}`, title = esc(PARAM_HELP[k] || '');
  if (typeof v === 'boolean') return `<label class="chk" for="${id}" title="${title}"><input id="${id}" data-k="${k}" type="checkbox" ${v ? 'checked' : ''}>${label(k)}</label>`;
  if (choices[k]) return `<label for="${id}" title="${title}">${label(k)}</label><select id="${id}" data-k="${k}">${choices[k].map(c => `<option ${c === v ? 'selected' : ''}>${esc(c)}</option>`).join('')}</select>`;
  return `<label for="${id}" title="${title}">${label(k)}</label><input id="${id}" data-k="${k}" type="number" step="${INTS.has(k) ? 1 : STEP[k] || 'any'}" min="0" value="${v}">`;
}

// Render the form into host; onChange(params) fires (debounced) whenever a valid value changes.
export function renderParams(host, info, values, onChange) {
  host.innerHTML = `<div class="params">${GROUPS.map(([title, keys]) => `<fieldset><legend>${title}</legend>
    ${keys.map(k => field(k, values[k], info.choices)).join('')}</fieldset>`).join('')}</div>
    <button id="p-reset" class="alt" type="button">Reset to pipeline defaults</button>
    <span id="p-err" class="small status-bad" role="status"></span>`;
  let timer = 0;
  const fire = () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const r = readParams(host, info.defaults);
      host.querySelector('#p-err').textContent = r.error || '';
      if (!r.error) onChange(r.params);
    }, 250);
  };
  host.querySelectorAll('[data-k]').forEach(el => el.addEventListener(el.type === 'number' ? 'input' : 'change', fire));
  host.querySelector('#p-reset').onclick = () => { renderParams(host, info, { ...info.defaults }, onChange); onChange({ ...info.defaults }); };
}

// Values from the form, validated as clean_params in web/analysis.py validates them.
export function readParams(host, defaults) {
  const p = { ...defaults };
  for (const el of host.querySelectorAll('[data-k]')) {
    const k = el.dataset.k;
    if (el.type === 'checkbox') p[k] = el.checked;
    else if (el.tagName === 'SELECT') p[k] = el.value;
    else {
      const v = Number(el.value);
      if (el.value === '' || !Number.isFinite(v)) return { error: `${label(k)}: enter a number` };
      p[k] = INTS.has(k) ? Math.trunc(v) : v;
    }
  }
  if (p.smooth_edges && p.smoothing_sigma <= 0) return { error: 'smoothing sigma must be > 0' };
  if (p.n_points < 1 || p.target_points_displacement < 1 || p.rotation_search_angles < 1) return { error: 'point counts and search angles must be ≥ 1' };
  if (p.width <= 0 || p.depth <= 0) return { error: 'rectangle width and depth must be > 0' };
  if (p.background_percentile < 0 || p.background_percentile > 100) return { error: 'background percentile must be 0-100' };
  return { params: p };
}
