# PIEZO1 Cell Edge Analysis Tool

A Python-based application for analyzing PIEZO1 protein distribution and membrane curvature using TIRF microscopy data.

## Overview

This tool enables simultaneous analysis of membrane curvature and PIEZO1 protein distribution along cell edges using Total Internal Reflection Fluorescence (TIRF) microscopy data. It processes two types of TIFF files:
1. Binary segmented images showing cell position (cell mask)
2. Fluorescence recordings of PIEZO1 protein distribution

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

## Project Structure
piezo1_analysis/
├── README.md
├── curvature_simulation
│   ├── bleb-analysis-readme.md
│   └── simulate-bleb-curvature.py
├── example_data
│   ├── test_cell_mask.tif
│   └── test_piezo1.tif
├── main.py
├── project-structure.py
├── requirements.txt
├── src
│   ├── __init__.py
│   ├── analysis
│   │   ├── __init__.py
│   │   ├── curvature_analyzer.py
│   │   ├── edge_detection.py
│   │   └── fluorescence_analyzer.py
│   ├── gui
│   │   ├── __init__.py
│   │   ├── analysis_panel.py
│   │   ├── file_panel.py
│   │   ├── main_window.py
│   │   └── visualization_panel.py
│   └── utils
│       ├── __init__.py
│       ├── data_structures.py
│       └── image_processing.py
└── tests
    └── __init__.py
    ├── test_edge_detection.py
    ├── test_curvature_analysis.py
    └── test_fluorescence_analysis.py

## Troubleshooting

Common issues and solutions:

1. No edge detected:
   - Check if cell mask is binary
   - Ensure cell is not touching image borders
   - Try adjusting minimum object size

2. Missing fluorescence measurements:
   - Check interior threshold setting
   - Verify fluorescence image alignment
   - Ensure proper image bit depth

3. Inconsistent curvature:
   - Adjust smoothing parameter
   - Increase segment length
   - Check for edge artifacts

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
