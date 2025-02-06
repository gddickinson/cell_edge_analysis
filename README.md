# PIEZO1 Cell Edge Analysis Tool

A Python-based application for analyzing PIEZO1 protein distribution along cell membranes using TIRF microscopy data.

## Overview

This tool is designed to analyze the relationship between PIEZO1 protein distribution and cell membrane curvature using Total Internal Reflection Fluorescence (TIRF) microscopy data. It processes two types of TIFF stacks:
1. Binary segmented images showing cell position
2. Fluorescence recordings of PIEZO1 protein distribution

The tool enables researchers to:
- Overlay and visualize both data streams
- Detect and analyze cell membrane edges
- Measure PIEZO1 fluorescence intensity along the cell edge
- Analyze the relationship between membrane curvature and PIEZO1 distribution

## Scientific Background

PIEZO1 is a mechanosensitive ion channel protein that plays a crucial role in cellular mechanotransduction. Understanding its distribution along cell membranes and its relationship to membrane curvature is essential for:
- Mechanistic studies of cellular mechanosensing
- Investigation of membrane protein organization
- Understanding cellular responses to mechanical stimuli

## Features

### Image Processing
- Load and display TIFF stacks from TIRF microscopy
- Overlay binary and fluorescence channels
- Adjustable opacity for visualization
- Frame-by-frame navigation
- Zoom and pan capabilities

### Analysis Capabilities
1. Edge Detection
   - Automated cell edge detection
   - Contour extraction and visualization
   - Frame-by-frame edge tracking

2. Intensity Analysis
   - Customizable sampling depth into the cell
   - Adjustable sampling width
   - Multiple intensity measurement options:
     - Mean intensity
     - Maximum intensity
     - Minimum intensity
   - Visual representation of sampling regions

3. Data Visualization
   - Real-time intensity profiles
   - Edge position plotting
   - Sampling vector visualization
   - Frame-synchronized display

## Technical Implementation

### Software Architecture
The application is built using Python with a modular structure:
```
piezo1_analysis/
├── main.py
├── requirements.txt
├── src/
    ├── gui/
    │   ├── main_window.py
    │   ├── image_view.py
    │   └── results_window.py
    ├── image_processing/
    │   ├── tiff_handler.py
    │   └── overlay.py
    └── analysis/
        ├── edge_detection.py
        ├── intensity_analyzer.py
        └── curvature.py
```

### Key Dependencies
- PyQt6: GUI framework
- NumPy: Numerical computations
- OpenCV: Image processing
- scikit-image: Scientific image analysis
- matplotlib: Data visualization

### Core Components

#### Edge Detection
- Uses contour detection algorithms
- Implements noise reduction and filtering
- Handles frame-by-frame tracking
- Border artifact removal

#### Intensity Analysis
- Normal vector calculation for each edge point
- Rectangular sampling regions:
  - Customizable depth into cell
  - Adjustable width for sampling
  - Multiple measurement methods
- Border region exclusion
- Collision detection for sampling regions

#### Visualization
- Real-time overlay generation
- Synchronized multi-window display
- Interactive plot updates
- Vector visualization for sampling regions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/gddickinson/piezo1-analysis.git
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

## Usage

1. Start the application:
```bash
python main.py
```

2. Load data:
   - Use "File → Load Cell Stack" to load binary segmented images
   - Use "File → Load PIEZO1 Stack" to load fluorescence data

3. Analysis workflow:
   1. Detect cell edges using "Analysis → Detect Cell Edges"
   2. Configure and run intensity analysis using "Analysis → Analyze Edge Intensity"
   3. Adjust visualization using the toolbar controls
   4. Toggle sampling vector display in the results window

## Data Requirements

- TIFF stacks should be properly aligned
- Binary images should clearly define cell boundaries
- Fluorescence images should have good signal-to-noise ratio
- Both stacks must have the same dimensions and number of frames

## Contributing

We welcome contributions! Please read our contributing guidelines and submit pull requests for:
- Bug fixes
- New features
- Documentation improvements
- Performance enhancements

## License

This project is licensed under the MIT License - see the LICENSE file for details.


## Contact

george.dickinson@gmail.com
