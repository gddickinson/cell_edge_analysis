# Cell Edge Analysis (PIEZO1) -- Roadmap

## Current State
A PyQt-based GUI tool for analyzing PIEZO1 protein distribution and membrane curvature from TIRF microscopy. Well-structured with `src/analysis/`, `src/gui/`, and `src/utils/` subpackages. Includes a test suite (`tests/`), example data, and a curvature simulation tool. Has mathematical documentation of curvature and fluorescence sampling methods. Mature codebase with ~8 analysis/GUI modules.

## Short-term Improvements
- [x] Ensure `tests/test_edge_detection.py`, `test_curvature_analysis.py`, `test_fluorescence_analysis.py` all pass and have adequate coverage
- [x] Add `pyproject.toml` to replace manual dependency management
- [ ] Add input validation for TIFF dimension mismatches between mask and fluorescence files
- [ ] Improve error messages in `src/gui/file_panel.py` when files cannot be loaded
- [ ] Add progress feedback for multi-frame analysis in `src/gui/analysis_panel.py`
- [ ] Document `src/utils/data_structures.py` with usage examples

## Feature Enhancements
- [ ] Add CLI mode for headless batch processing of multiple image pairs
- [ ] Implement automated parameter optimization (e.g., optimal segment length for curvature)
- [ ] Add statistical tests comparing curvature-intensity correlations across conditions
- [ ] Support overlay of multiple analysis results for comparison
- [ ] Add undo/redo for parameter changes in the GUI
- [ ] Export analysis results as publication-ready vector figures (SVG/PDF)

## Long-term Vision
- [ ] Integrate with napari for advanced 3D visualization
- [ ] Add machine learning-based curvature estimation as alternative to circle fitting
- [ ] Support 3D membrane curvature analysis (mean curvature, Gaussian curvature)
- [ ] Publish `curvature_simulation/` as a standalone validation tool
- [ ] Create a plugin architecture so users can add custom analysis modules

## Technical Debt
- [x] Large `.tif` files in project root should be in a `data/` directory with `.gitignore`
- [x] `curvature_simulation/simulate-bleb-curvature.py` uses hyphens in filename -- rename
- [x] `project-structure.py` appears to be a one-off utility -- move to `tools/`
- [x] `volumeslider.log` should be in `.gitignore`
- [x] Test suite may have stale tests if API changed -- audit test fixtures
- [ ] `standalone/` directory purpose unclear relative to main `src/` -- document or consolidate
