# cell_edge_analysis

Nine-step pipeline (step1_...step9_*.py, run_all_steps.py), Tkinter GUI (cell_edge_analysis_gui.py) and a web
interface (web/). Navigation map: @INTERFACE.md. Progress: SESSION_LOG.md.

- Tests: `python -m pytest -q tests` (web, fixture, regressions) and `node web/static/edge_engine.test.mjs`.
- After changing steps 1, 2, 5, 6 or 7 (or the demo data), regenerate the JS fixture:
  `python scripts/make_edge_fixture.py`, and keep web/static/edge_engine.js in step.
- Pipeline defaults live in run_all_steps.PIPELINE_CONFIG; the web reads them from there.
