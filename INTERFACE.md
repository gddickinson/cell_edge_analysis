# INTERFACE.md: navigation map

## Pipeline (repo root; each step reads earlier steps' result folders and writes `stepN_results/`)
| File | Purpose / key functions |
|---|---|
| `pipeline_defaults.py` | `DEFAULTS` (per-step defaults) and `FILE_PATTERNS`: the single source read by run_all_steps, every step script's CONFIG, the GUI and web/analysis.py |
| `run_all_steps.py` | `PIPELINE_CONFIG` (paths + `pipeline_defaults`), dataset discovery, `run_step()` (runs step scripts as subprocesses, resolved via `SCRIPT_DIR`) |
| `step1_data_loading.py` | load TIFF stacks; `subtract_background`, `normalize_frames` |
| `step2_edge_detection.py` | `detect_cell_edge` (longest find_contours at 0.5), `smooth_edge` (Gaussian, wrap/reflect) |
| `step3_displacement_calculation.py` | `calculate_displacement_map` (uppermost-edge y change per integer x) |
| `step4_movement_classification.py` | extruding / retracting / stable per frame pair |
| `step5_edge_sampling.py` | `sample_all_edges`: per_frame, fixed_x, dense, displacement_like; `select_y_value` |
| `step6_sampling_rectangles.py` | `create_rectangles_for_frame`, `check_cell_coverage`, `calculate_edge_normal`, `search_optimal_rotation` |
| `step7_intensity_extraction.py` | `extract_intensity_from_rectangle` (mean in accepted rectangles) |
| `step8_movement_assignment.py` | pairs intensities with local displacement |
| `step9_correlation_analysis.py` | Pearson / binned statistics -> `final_analysis_summary.json` |
| `summarize_batch_results.py`, `combined_batch_analysis.py` | multi-dataset summary table / pooled analysis |
| `cell_edge_analysis_gui.py`, `launch_gui.py` | Tkinter GUI (runs the step scripts in a thread) |
| `old_version/` | earlier PyQt6 curvature/fluorescence app with its own tests (`old_version/tests`) |

## Web interface (`web/`)
| File | Purpose |
|---|---|
| `web/app.py` | FastAPI: `/api/info` (steps, defaults, choices, demo), POST `/api/tiff` (tifffile reader), POST `/api/analyse` (Python check); `STATIC_ENDPOINTS` |
| `web/analysis.py` | `run()` calls the step 1/2/5/6/7 functions on in-memory stacks (sets their CONFIG under a lock); `default_params`, `clean_params`, `to_json` |
| `web/tiff_io.py` | `read_stack()` -> float32 stack + um_per_px from OME / ImageJ / TIFF resolution |
| `web/static/index.html`, `main.js`, `core.js`, `style.css`, `style_app.css` | shell, router (kit), theme |
| `web/static/contours.js` | JS `findContours` (skimage port), `gaussianFilter1d` (scipy port) |
| `web/static/edge_engine.js` | JS steps 1, 2, 5, 6, 7: `preprocessFrame`, `edgeForFrame`, `sampleEdges`, `rectanglesForFrame`, `runPipeline` |
| `web/static/tiff.js` | browser TIFF stack reader (`readTiff`, `fromServer`) |
| `web/static/analyse.js`, `analyse_params.js`, `analyse_view.js` | Analyse page: loading, parameter form, canvas/plots/table/CSV |
| `web/static/home.js`, `pipeline.js`, `about.js`, `static_api.js` | other pages; static-site data layer |
| `web/static/edge_engine.test.mjs` | node test: JS vs Python fixture |
| `web/static/demo/` | synthetic demo stack (from `scripts/make_demo_data.py`) |

## Scripts and tests
- `scripts/make_demo_data.py` (synthetic demo TIFFs), `scripts/make_edge_fixture.py` (-> `tests/fixtures/edge_fixture.json`),
  `scripts/build_static.py` (Pages export), `scripts/screenshots.py` (smoke test + README images).
- `tests/test_web.py` (API, static build, node test), `tests/test_edge_fixture.py` (fixture current),
  `tests/test_script_paths.py`, `tests/test_defaults_single_source.py`, `tests/test_summarize_batch.py`, `tests/test_step6_nan_points.py` (regressions).

## How it connects
`web/analysis.py` imports the step modules and `pipeline_defaults.DEFAULTS`; `/api/info` serves the defaults to the
front end; `edge_engine.js` mirrors steps 1, 2, 5, 6, 7 and is checked against `web/analysis.py` output via the fixture.
