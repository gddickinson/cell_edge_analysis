// Home page: hero, facts from the repo (/api/info: pipeline steps and defaults) and links to the pages.
import { route, app, api, esc, isStatic } from './core.js';

route('home', async () => {
  const info = await api('/info'), d = info.defaults, web = info.steps.filter(s => s.web).length;
  app().innerHTML = `<section class="hero"><p class="kicker">Fluorescence microscopy · cell edge dynamics</p>
    <h1 class="glow">Cell edge analysis</h1>
    <p class="lead">${esc(info.description)} Load a fluorescence stack and its cell mask, and see the detected edge, the
      sampling rectangles and the intensity profile along the edge for every frame.</p>
    <a class="btn" href="#/analyse/demo">Try the demo stack</a><a class="btn alt" href="#/analyse">Analyse your images</a></section>
    <div class="tiles">
      <div class="tile"><b>${info.steps.length}</b><span>pipeline steps (run_all_steps.py)</span></div>
      <div class="tile"><b>${web}</b><span>steps run in your browser</span></div>
      <div class="tile"><b>${info.choices.sampling_method.length}</b><span>edge sampling methods</span></div>
      <div class="tile"><b>${d.width}×${d.depth}</b><span>default rectangle (px)</span></div></div>
    <div class="callout a small">${isStatic()
      ? 'On this site the analysis runs <b>in your browser</b> with a JavaScript port of the repo\'s Python steps 1, 2, 5, 6 and 7, tested to give the same edges, rectangles and intensities. Your images are not uploaded.'
      : 'In the local app the analysis runs in the browser (the same JavaScript port as the static site); the Python server reads any TIFF with tifffile and can re-run the frame with the repo\'s own Python steps to check the result.'}</div>
    <div class="grid">
      <a class="card" href="#/analyse"><b>Analyse</b><span>Image + mask TIFF stacks or the demo: edge, sampling points, rectangles coloured by intensity, the profile along the edge, a frame × position map, CSV export.</span></a>
      <a class="card" href="#/pipeline"><b>Pipeline</b><span>The nine steps from loading to correlation, which ones the browser runs, and every parameter with its default.</span></a>
      <a class="card" href="#/about"><b>About</b><span>What the project does, how to run the batch pipeline, the desktop GUI and this web app.</span></a>
    </div>`;
});
