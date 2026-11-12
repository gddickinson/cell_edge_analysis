// About page: what the project is, how to run the pipeline, the desktop GUI and the web app, credits.
import { route, app, api, esc } from './core.js';

route('about', async () => {
  const info = await api('/info');
  app().innerHTML = `<p class="kicker">About</p><h1>Cell Edge Movement Analysis</h1>
    <p class="lead">A Python pipeline for analysing PIEZO1 protein localisation and cell edge dynamics in fluorescence
      microscopy: it detects the cell edge from a mask in every frame, measures PIEZO1 intensity in rectangles just
      inside the edge, and correlates that intensity with how the edge moves (extruding, retracting or stable).</p>
    <h2>Run the pipeline</h2>
    <pre>pip install numpy scipy matplotlib scikit-image tifffile
# data/&lt;dataset&gt;/&lt;name&gt;${esc(info.file_patterns.image[0])} and &lt;name&gt;${esc(info.file_patterns.mask[0])}
python run_all_steps.py --batch                 # every dataset under data/
python run_all_steps.py --batch --dataset exp1  # one dataset
python summarize_batch_results.py results/      # table of all datasets
python combined_batch_analysis.py               # pooled correlation</pre>
    <p>Main result per dataset: <code>results/&lt;dataset&gt;/step9_results/final_analysis_summary.json</code>.
      Parameters live in <code>PIPELINE_CONFIG</code> in <code>run_all_steps.py</code>; each step script also takes them
      on the command line (<code>--help</code>).</p>
    <h2>Desktop GUI</h2>
    <pre>python launch_gui.py       # or: python cell_edge_analysis_gui.py</pre>
    <p>A Tkinter app that runs all or single steps with chosen parameters, streams the log and browses the results
      frame by frame (see <code>GUI_USER_GUIDE.md</code>).</p>
    <h2>Run the web app</h2>
    <pre>pip install -r requirements-web.txt
python run_web.py          # http://127.0.0.1:8124</pre>
    <p>The Analyse page runs a JavaScript port of steps 1, 2, 5, 6 and 7 (<code>edge_engine.js</code>,
      <code>contours.js</code>) in the browser, both here and on the static GitHub Pages site. A node test checks it
      against the repo's Python on the demo stack and a closed-cell example for every sampling and rotation method. The
      local app adds TIFF reading with tifffile (compressed files) and a "Check with Python" button that re-runs the
      frame with the repo's own step functions.</p>
    <p class="small">${esc(info.demo.note)}</p>
    <h2>Credits</h2>
    <p>George Dickinson. Web interface built with AI assistance from
      <a href="https://claude.com/" target="_blank" rel="noopener">Claude (Anthropic)</a>. Licence: MIT. Source:
      <a href="https://github.com/gddickinson/${esc(info.repo)}" target="_blank" rel="noopener">github.com/gddickinson/${esc(info.repo)}</a>.</p>`;
});
