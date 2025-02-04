# PIEZO1 Cell Edge Analysis Tool

## Overview
This tool analyzes the relationship between PIEZO1 protein distribution and cell membrane curvature using TIRF microscopy data. It processes paired TIFF stacks containing:
1. Binary segmented cell images
2. Fluorescently labeled PIEZO1 protein recordings

The software provides tools for:
- Image stack visualization and overlay
- Automated cell edge detection
- PIEZO1 intensity analysis along cell edges
- Membrane curvature analysis
- Correlation between curvature and PIEZO1 distribution

## Features
- **Stack Loading & Visualization**
  - Load and display paired TIFF stacks
  - Adjustable overlay opacity
  - Frame-by-frame navigation
  - Zoom and pan capabilities

- **Edge Detection**
  - Automated cell boundary detection
  - Edge visualization overlay
  - Frame-by-frame edge tracking

- **Intensity Analysis**
  - Configurable sampling depth into cell
  - Adjustable measurement intervals
  - Normal vector-based intensity sampling
  - Results visualization

- **Curvature Analysis**
  - Edge curvature calculation
  - Configurable analysis window size
  - Convex/concave region classification

## Installation

### Prerequisites
- Python 3.8 or higher
- Qt6

### Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- PyQt6
- numpy
- tifffile
- opencv-python
- scikit-image
- matplotlib
- scipy

### Installation Steps
1. Clone the repository:
```bash
git clone https://github.com/yourusername/piezo1-analysis.git
cd piezo1-analysis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Usage

### Basic Workflow
1. **Load Image Stacks**
   - File → Load Cell Stack (binary segmented image)
   - File → Load PIEZO1 Stack (fluorescence recording)

2. **Adjust Visualization**
   - Use toolbar to navigate frames
   - Adjust overlay opacity
   - Zoom and pan as needed

3. **Detect Cell Edges**
   - Analysis → Detect Cell Edges
   - Verify edge detection results

4. **Analyze PIEZO1 Distribution**
   - Analysis → Analyze Edge Intensity
   - Set sampling parameters:
     - Sampling depth into cell
     - Measurement interval along edge

5. **Calculate Curvature**
   - Analysis → Calculate Curvature
   - View curvature analysis results

### Advanced Features
- Save analysis results
- Export data for further processing
- Batch processing capabilities
- Custom parameter adjustment

## Project Structure
```
piezo1_analysis/
├── main.py
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── image_view.py
│   │   └── toolbar.py
│   ├── image_processing/
│   │   ├── __init__.py
│   │   ├── tiff_handler.py
│   │   └── overlay.py
│   └── analysis/
│       ├── __init__.py
│       ├── edge_detection.py
│       ├── intensity_analyzer.py
│       └── curvature.py
```

## Contributing
Contributions are welcome! Please feel free to submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup
1. Fork the repository
2. Create a development environment
3. Install development dependencies
4. Make your changes
5. Submit a pull request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Citation
If you use this tool in your research, please cite:
[Citation information to be added]

## Contact
[Your contact information or lab details]

## Acknowledgments
- [Your lab or institution]
- Contributors and maintainers
- Support from funding agencies

## Troubleshooting
Common issues and solutions:
1. **Image Loading Issues**
   - Ensure TIFF files are in the correct format
   - Check file permissions

2. **Edge Detection Problems**
   - Verify binary image quality
   - Adjust detection parameters if needed

3. **Performance Issues**
   - Check available system memory
   - Reduce stack size if needed

For more help, please open an issue on GitHub.
