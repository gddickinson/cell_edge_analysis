# Cell Edge Analysis (PIEZO1) - Interface Map

## Module Structure

### Entry Point

| File | Purpose |
|------|---------|
| `main.py` | PyQt6 application entry point, creates `MainWindow` |

### `src/analysis/` - Core Analysis

| File | Key Classes | Purpose |
|------|-------------|---------|
| `edge_detection.py` | `EdgeDetector` | Cell edge detection from binary masks via contour finding |
| `curvature_analyzer.py` | `CurvatureAnalyzer` | Membrane curvature calculation using circular arc fitting |
| `fluorescence_analyzer.py` | `FluorescenceAnalyzer` | PIEZO1 fluorescence intensity sampling along membrane |

### `src/gui/` - GUI Components

| File | Key Classes | Purpose |
|------|-------------|---------|
| `main_window.py` | `MainWindow` | Top-level PyQt6 window, coordinates panels |
| `file_panel.py` | `FilePanel` | File loading for mask and fluorescence TIFFs |
| `analysis_panel.py` | `AnalysisPanel` | Parameter controls and analysis execution |
| `visualization_panel.py` | `VisualizationPanel` | Matplotlib-based result visualization |
| `results_window.py` | `ResultsWindow` | Detailed results display |
| `coordinated_analysis.py` | `CoordinatedAnalysis` | Multi-frame analysis coordination |

### `src/utils/` - Utilities

| File | Key Classes | Purpose |
|------|-------------|---------|
| `data_structures.py` | `ImageData`, `EdgeData`, `CurvatureData`, `FluorescenceData`, `AnalysisParameters` | Core dataclasses for analysis pipeline |
| `image_processing.py` | (utility functions) | Image preprocessing and manipulation |

### `curvature_simulation/` - Simulation Tools

| File | Purpose |
|------|---------|
| `simulate_bleb_curvature.py` | Bleb curvature simulation (renamed from `simulate-bleb-curvature.py`) |
| `analyze_real_cell_example.py` | Real cell curvature analysis |
| `membrane_dynamics_analysis.py` | Membrane dynamics simulation |
| `multi_scale_curvature.py` | Multi-scale curvature analysis |
| `real_curvature_analysis.py` | Real curvature measurement |

### `standalone/` - Standalone Analysis

| File | Purpose |
|------|---------|
| `curvature_measurements.py` | Standalone curvature measurement script |

### `tools/` - Utility Scripts

| File | Purpose |
|------|---------|
| `project_structure.py` | Project structure display (moved from root) |

### Tests

| File | Purpose |
|------|---------|
| `tests/test_edge_detection.py` | Edge detection smoke tests |
| `tests/test_curvature_analysis.py` | Curvature analysis tests |
| `tests/test_fluorescence_analysis.py` | Fluorescence analysis tests |
| `tests/test_data_structures.py` | Data structure tests |

## Data Flow

```
FilePanel --> ImageData --> EdgeDetector --> EdgeData --> CurvatureAnalyzer --> CurvatureData
                                                    \-> FluorescenceAnalyzer --> FluorescenceData
```
