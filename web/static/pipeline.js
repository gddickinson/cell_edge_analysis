// Pipeline page: the nine steps (from /api/info, as README / run_all_steps.py describe them) and the parameters.
import { route, app, api, esc } from './core.js';
import { PARAM_HELP } from './analyse_params.js';

route('pipeline', async () => {
  const info = await api('/info'), d = info.defaults;
  app().innerHTML = `<p class="kicker">Method</p><h1>The nine-step pipeline</h1>
    <p class="lead">Each step is a script that reads the previous steps' results and writes its own folder
      (<code>step1_results/</code> ... <code>step9_results/</code>). <code>run_all_steps.py --batch</code> runs them all
      on every dataset under <code>data/</code>. Steps marked <b>browser</b> run on the Analyse page.</p>
    <ol class="steps">${info.steps.map(s => `<li class="${s.web ? 'web' : ''}"><b>${s.n}. ${esc(s.name)}</b>
      ${s.web ? '<span class="tag">browser</span>' : '<span class="tag">Python only</span>'}
      <span class="small mute mono">${esc(s.script)}</span><br><span class="small">${esc(s.text)}</span></li>`).join('')}</ol>
    <div class="callout small">Steps 3, 4, 8 and 9 relate the intensity to edge <i>movement</i> between frames and compute
      the correlation statistics; they need the full pipeline (<code>python run_all_steps.py --batch</code> or the desktop
      GUI), which also writes verification figures for every step.</div>
    <h2>Parameters and defaults</h2>
    <p class="small mute">Defaults are the batch pipeline's (<code>PIPELINE_CONFIG</code> in <code>run_all_steps.py</code>).
      All lengths are in pixels.</p>
    <div class="scroll"><table><thead><tr><th>Parameter</th><th>Default</th><th>Meaning</th></tr></thead><tbody>
      ${Object.entries(PARAM_HELP).map(([k, v]) => `<tr><td class="num">${esc(k)}</td><td class="num">${esc(String(d[k]))}</td>
        <td class="small">${esc(v)}${info.choices[k] ? ` <span class="mute">(${info.choices[k].map(esc).join(', ')})</span>` : ''}</td></tr>`).join('')}
    </tbody></table></div>
    <h2>Conventions</h2>
    <p class="small">Points are (row, column) = (y, x) with pixel centres at integer coordinates, as
      <code>skimage.measure.find_contours</code> returns them. "Uppermost" means the smallest row (top of the image). The
      pipeline works in pixels throughout; when a TIFF records its pixel size the Analyse page shows it and adds it to the
      CSV export, but no threshold depends on it.</p>`;
});
