# SESSION_LOG

## 2026-11-12: web interface + static site (branch web-interface)
- Added `web/` (FastAPI app on port 8124, ES-module front end), static GitHub Pages export and workflow.
- Analyse page runs a JS port of steps 1, 2, 5, 6, 7 (`contours.js`, `edge_engine.js`) on the user's image + mask
  TIFFs; node test agrees with Python (`scripts/make_edge_fixture.py`) on the demo stack and a closed-blob stack for
  every sampling / rotation method. Angle `search` near-ties (equal coverage up to rounding) can resolve to a different
  angle than Python; the test checks such cases have equal coverage.
- Demo data: synthetic stack from `scripts/make_demo_data.py` (the repo has no example images).
- Fixed: step scripts not found when run_all_steps.py / the GUI start from another directory; batch summary reading a
  step 9 file that is never written (correlation always N/A); step 6 crash on NaN points from fixed_x sampling.
- Corrected README/CLI help (real step 9 output file, defaults 100.0 / 20.0, missing ENHANCEMENTS docs).
- Open for George: GUI defaults differ from PIPELINE_CONFIG (target_points_displacement 5 vs 20, n_points 10 vs 12);
  several existing files exceed 500 lines (GUI 1306, combined_batch_analysis 759, step6 660, ...).
