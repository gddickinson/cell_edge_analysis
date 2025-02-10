# PIEZO1 Membrane Distribution Analysis
## Overview
This tool analyzes the relationship between cell membrane curvature and PIEZO1 protein distribution using TIRF microscopy data. It processes two TIFF stacks:
1. A binary segmentation of the cell
2. A fluorescence recording of PIEZO1 proteins

## Installation
Required packages:
```bash
pip install numpy matplotlib tifffile opencv-python scipy scikit-image
```

## Usage
Replace the file paths in the script:
```python
cell_path = "path_to_cell_segmentation.tif"
piezo_path = "path_to_piezo1_recording.tif"
```

Run the analysis:
```bash
python analyze_piezo1.py
```

## Mathematical Background

### Edge Detection and Contour Analysis
The cell edge is detected using OpenCV's contour finding algorithm on the binary segmentation. The largest contour is selected as the cell boundary. The contour is represented as an ordered set of points: {(x₁, y₁), (x₂, y₂), ..., (xₙ, yₙ)}.

### Intensity Measurement
Intensity measurements are taken along vectors normal to the cell membrane. For each point P(x, y) on the contour:

1. **Normal Vector Calculation**:
   - For consecutive points P₁(x₁, y₁) and P₂(x₂, y₂)
   - Direction vector: D = (dx, dy) = (x₂ - x₁, y₂ - y₁)
   - Normal vector: N = (dy, -dx)
   - Normalized: N = N / |N|

2. **Sampling Process**:
   - For a sampling depth d and point P
   - Sample points: S(t) = P + tN, t ∈ [0, d]
   - Intensity I(t) measured at each S(t)
   - Final intensity: I = mean(I(t))

### Curvature Calculation
Curvature (κ) is calculated using differential geometry principles:

1. **Contour Smoothing**:
   - Gaussian filter applied to x and y coordinates separately
   - σ controls smoothing level: G(x) = (1/√(2πσ²))e^(-x²/2σ²)

2. **Curvature Formula**:
   κ = (x'y'' - y'x'') / (x'² + y'²)^(3/2)
   where:
   - x', y' are first derivatives
   - x'', y'' are second derivatives
   - Calculated using finite differences:
     - x' ≈ (x[i+1] - x[i-1]) / 2
     - x'' ≈ x[i+1] - 2x[i] + x[i-1]

3. **Implementation Details**:
   - Derivatives computed using numpy.gradient
   - Singularity handling: κ = 0 when denominator < 1e-10
   - Smoothing applied before derivative calculation

### Point Filtering
Points are filtered based on several criteria:

1. **Border Margin**:
   - Points within border_margin pixels of image edge are excluded
   - Ensures complete sampling vectors

2. **Cell Interior Check**:
   - Verifies normal vector points into cell
   - Uses binary mask: M(x, y) = 1 if (x, y) inside cell

3. **Valid Sampling Region**:
   - Entire sampling vector must lie within image
   - All samples must be within cell mask

## Output
The script generates four figures:
1. Edge detection result
2. Sampling vectors overlay
3. Intensity and curvature profiles
4. Intensity vs curvature correlation plot

## Mathematical Notes

### Normal Vector Direction
The inward-pointing normal is determined by testing both possible normal vectors:
N₁ = (dy, -dx) and N₂ = (-dy, dx)
The vector giving more interior points is selected.

### Curvature Sign Convention
- Positive curvature: Cell boundary curves inward (concave)
- Negative curvature: Cell boundary curves outward (convex)
- Zero curvature: Straight boundary

### Relationship Analysis
The correlation coefficient r between intensity I and curvature κ is calculated:
r = cov(I, κ) / (σᵢσₖ)
where:
- cov(I, κ) is the covariance
- σᵢ, σₖ are standard deviations

## Limitations
- Assumes cell boundary is well-defined
- Curvature calculation sensitive to noise
- Local intensity variations may affect measurements
- Edge effects near image boundaries


