# PIEZO1 Cell Edge Analysis Tool

A Python-based application for analyzing PIEZO1 protein distribution and membrane curvature using TIRF microscopy data.

## Overview

This tool enables simultaneous analysis of membrane curvature and PIEZO1 protein distribution along cell edges using Total Internal Reflection Fluorescence (TIRF) microscopy data. It processes two types of TIFF files:
1. Binary segmented images showing cell position (cell mask)
2. Fluorescence recordings of PIEZO1 protein distribution

## Analysis Workflow

The analysis pipeline consists of three main stages:

1. **Edge Detection and Validation**
   - Binary mask preprocessing using morphological operations
   - Contour detection with sub-pixel accuracy
   - Edge smoothing using Gaussian filtering
   - Validation of edge continuity and border artifacts

2. **Curvature Analysis**
   - Local circle fitting to edge segments
   - Calculation of signed curvature
   - Statistical validation of measurements
   - Reference to biological curvature scales

3. **Fluorescence Analysis**
   - Normal vector calculation at sampling points
   - Rectangular sampling region definition
   - Interior overlap verification
   - Background-subtracted intensity measurement

### Mathematical Framework

#### Curvature Calculation
The local curvature κ at each point is calculated using circle fitting:
1. For each point p₀, consider a segment of length L centered at p₀
2. Fit circle using algebraic least squares method:
   - Transform to implicit form: (x - a)² + (y - b)² = r²
   - Solve eigenvalue problem to find center (a,b) and radius r
3. Calculate signed curvature: κ = ±1/r
   - Sign determined by normal vector orientation
   - Scaled to physical units (nm⁻¹)

#### Fluorescence Sampling
Intensity measurements use oriented rectangular sampling:
1. Calculate normal vector n̂ at each point
2. Define sampling rectangle R(w,d):
   - Width w perpendicular to n̂
   - Depth d along n̂
3. Measure mean intensity I:
   I = (1/A)∫∫ᵣ F(x,y) dx dy
   where F is the fluorescence image and A is the area

## Project Structure
```
piezo1_analysis/
├── README.md
├── curvature_simulation/          # Curvature simulation tools
│   ├── bleb-analysis-readme.md
│   └── simulate-bleb-curvature.py
├── example_data/                  # Test datasets
│   ├── test_cell_mask.tif
│   └── test_piezo1.tif
├── main.py                        # Application entry point
├── requirements.txt               # Package dependencies
├── src/                          # Source code
│   ├── analysis/                 # Analysis modules
│   │   ├── curvature_analyzer.py
│   │   ├── edge_detection.py
│   │   └── fluorescence_analyzer.py
│   ├── gui/                      # User interface
│   │   ├── analysis_panel.py
│   │   ├── file_panel.py
│   │   ├── main_window.py
│   │   └── visualization_panel.py
│   └── utils/                    # Utility functions
│       ├── data_structures.py
│       └── image_processing.py
└── tests/                        # Test suite
    ├── test_edge_detection.py
    ├── test_curvature_analysis.py
    └── test_fluorescence_analysis.py
```

## Features

### Core Analysis Capabilities
- Automated cell edge detection and smoothing
- Local membrane curvature calculation
- Membrane-proximal fluorescence intensity measurement
- Synchronized curvature and intensity analysis
- Frame-by-frame analysis for time series data

### Analysis Parameters
- Edge smoothing with adjustable sigma
- Customizable sampling density along membrane
- Adjustable segment length for curvature calculation
- Vector depth and width for fluorescence sampling
- Interior threshold filtering for fluorescence measurements

### Visualization Options
- Combined curvature and fluorescence display
- Intensity-curvature correlation plots
- Intensity profile visualization
- Adjustable visualization parameters:
  - Line width
  - Background opacity
  - Rectangle opacity
  - Cell edge visibility toggle

### Debug Features
- Detailed edge detection statistics
- Curvature measurement validation
- Fluorescence sampling verification
- Warning system for potential analysis issues

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/piezo1-analysis.git
cd piezo1-analysis
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

1. Launch the application:
```bash
python main.py
```

2. Load example data:
   - Navigate to example_data folder
   - Load the cell mask TIFF file using "Load Cell Mask"
   - Load the PIEZO1 fluorescence TIFF file using "Load Fluorescence"

3. Adjust analysis parameters as needed:
   - Common Parameters:
     - Number of Samples (20-150)
     - Edge Smoothing σ (0-5.0)
   - Curvature Analysis:
     - Segment Length (5-20 pixels)
   - Fluorescence Analysis:
     - Vector Width (1-20 pixels)
     - Vector Depth (5-50 pixels)
     - Interior Threshold (0-100%)

4. Use visualization controls to optimize display:
   - Line Width
   - Background Opacity
   - Rectangle Opacity
   - Toggle Cell Edge visibility

## Example Data

The `example_data` folder contains test files for verifying the analysis pipeline:

- `test_cell_mask.tif`: Binary cell mask image
- `test_piezo1.tif`: Corresponding PIEZO1 fluorescence image

These files demonstrate the expected format and can be used to test the analysis workflow.

## Data Requirements

### Input Files
- TIFF format (single image or stack)
- Both mask and fluorescence images must have the same dimensions
- Cell mask should be binary (0 and 255 or 0 and 1)
- Fluorescence image should be grayscale

### Image Quality
- Clear cell boundaries in mask image
- Good signal-to-noise ratio in fluorescence image
- Minimal motion artifacts
- Proper focus throughout imaging

## Technical Details

### Cell Edge Detection
- Contour detection using OpenCV
- Morphological cleaning of binary mask
- Smoothing options for noise reduction
- Border artifact handling

### Curvature Analysis
- Local circle fitting algorithm
- Adjustable segment length for local fitting
- Validation of fitting quality
- Reference curvature markers

### Fluorescence Analysis
- Normal vector calculation at each point
- Rectangular sampling regions
- Interior overlap verification
- Background subtraction option


## References and Methods

### Edge Detection
The edge detection algorithm uses OpenCV's `findContours` function with sub-pixel refinement, followed by optional Gaussian smoothing:
```python
σ_smooth = 1.0  # smoothing parameter
edge_smooth = gaussian_filter1d(edge_points, σ_smooth, axis=0)
```

### Curvature Calculation
Circle fitting uses the algebraic method described in:
1. Pratt, V. "Direct least-squares fitting of algebraic surfaces." Computer Graphics 21(4):145-152 (1987)
2. Taubin, G. "Estimation of planar curves, surfaces, and nonplanar space curves defined by implicit equations with applications to edge and range image segmentation." IEEE PAMI 13(11):1115-1138 (1991)

### Fluorescence Analysis
Intensity sampling follows methods similar to:
- Aimon et al. "Membrane Shape Modulates Transmembrane Protein Distribution." Developmental Cell 28(2):212-218 (2014)

## Contributing

Contributions are welcome! Please read the contributing guidelines and submit pull requests for:
- Bug fixes
- New features
- Documentation improvements
- Performance enhancements

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Developed for the analysis of PIEZO1 protein distribution in relation to membrane curvature in TIRF microscopy data.

## Contact

For questions and support, please contact:
- Email: george.dickinson@gmail.com
- Issues: Submit via GitHub issue tracker
