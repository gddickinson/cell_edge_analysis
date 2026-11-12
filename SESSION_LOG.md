# SESSION_LOG

## 2026-11-12: web interface + static site (branch web-interface)
- Added `web/` (FastAPI app on port 8124, ES-module front end), static GitHub Pages export and workflow.
- Analyse page runs a JS port of steps 1, 2, 5, 6, 7 (`contours.js`, `edge_engine.js`) on the user's image + mask
  TIFFs; node test agrees with Python (`scripts/make_edge_fixture.py`) on the demo stack and a closed-blob stack for
  every sampling / rotation method.
- Demo data: synthetic stack from `scripts/make_demo_data.py` (the repo has no example images).
- Fixed: step scripts not found when run_all_steps.py / the GUI start from another directory; batch summary reading a
  step 9 file that is never written (correlation always N/A); step 6 crash on NaN points from fixed_x sampling.
- Corrected README/CLI help (real step 9 output file, defaults 100.0 / 20.0, missing ENHANCEMENTS docs).
- Open for George: several existing files exceed 500 lines (GUI 1306, combined_batch_analysis 759, step6 660, ...).

## 2026-11-12 (later): single source of defaults, deterministic angle search
- New `pipeline_defaults.py` (DEFAULTS, FILE_PATTERNS) read by run_all_steps.PIPELINE_CONFIG, every step script's
  CONFIG, the Tk GUI's initial widget values and web/analysis.py. Values are the batch pipeline's. GUI change: it now
  starts with n_points 12 / target_points_displacement 20 (was 10 / 5) and step 8 run standalone or from the GUI uses
  temporal_direction 'future' (was 'past'), so GUI results now match run_all_steps.py. Batch results on the demo stack
  are unchanged (checked). Regression test: tests/test_defaults_single_source.py.
- Step 6 `search` rotation: among angles whose coverage is within COVERAGE_TIE_TOL (1e-9) of the best, the smallest
  angle now wins (previously the winner among equal-coverage angles was decided by float rounding of the rotated
  area, so it differed between platforms and between Python and JS). Same rule in edge_engine.js; the node test no
  longer needs a tie allowance (all checks agree). Changes results only for rotation_method='search' (not the default
  'vertical'), and only at such ties. Regression test: tests/test_rotation_search_ties.py.
