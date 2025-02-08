# Analysis Module Documentation

## Overview
This module implements advanced image analysis algorithms for quantifying membrane protein distribution and membrane geometry in TIRF microscopy data. The analysis pipeline consists of three main components: edge detection, intensity analysis, and curvature calculation.

## Edge Detection (`edge_detection.py`)

### Algorithm Description
The edge detection process employs a multi-step approach to robustly identify cell boundaries in TIRF microscopy data:

1. **Initial Contour Detection**
   - Input binary images are processed using morphological operations to remove noise
   - Contours are detected using OpenCV's implementation of the border following algorithm¹
   - The largest contour by area is selected as the cell boundary

2. **Edge Smoothing**
   - The detected contour undergoes Gaussian smoothing to reduce pixelation artifacts
   - For a contour point sequence {(xi, yi)}, smoothing is applied using:
     ```
     x'i = Σ(xj * G(i-j, σ))
     y'i = Σ(yj * G(i-j, σ))
     ```
     where G(x, σ) is the Gaussian kernel with standard deviation σ

3. **Border Artifact Handling**
   - Points within a margin d of the image border are excluded
   - Edge segments are verified using morphological connectivity

## Intensity Analysis (`intensity_analyzer.py`)

### Mathematical Framework

1. **Normal Vector Calculation**
   - For each point p(t) = (x(t), y(t)) along the contour:
   - Tangent vector: T(t) = (dx/dt, dy/dt)
   - Normal vector: N(t) = (-dy/dt, dx/dt)
   - Direction validation using interior point sampling

2. **Sampling Region Definition**
   - For each point pi:
     - Normal vector ni = (nx, ny)
     - Sampling depth d
     - Sampling width w
   - Region corners defined by:
     ```
     c1 = pi + (w/2)(-ny, nx)
     c2 = pi - (w/2)(-ny, nx)
     c3 = pi + d*ni + (w/2)(-ny, nx)
     c4 = pi + d*ni - (w/2)(-ny, nx)
     ```

3. **Intensity Measurement**
   - For sampling region R:
     - Mean intensity: μ = (1/|R|) ∑(x,y)∈R I(x,y)
     - Maximum intensity: max(x,y)∈R I(x,y)
     - Minimum intensity: min(x,y)∈R I(x,y)
   where I(x,y) is the fluorescence intensity at point (x,y)

## Curvature Analysis (`curvature.py`)

### Mathematical Implementation

1. **Contour Parameterization**
   - Contour resampled using cubic splines:
     ```
     x(t) = Σ Bj,k(t)Pj,x
     y(t) = Σ Bj,k(t)Pj,y
     ```
     where Bj,k are B-spline basis functions of degree k

2. **Curvature Calculation**
   - Local curvature κ computed using:
     ```
     κ(t) = (x'y'' - y'x'') / (x'² + y'²)^(3/2)
     ```
     where prime denotes differentiation with respect to t

3. **Scale-Space Analysis**
   - Multi-scale curvature analysis using Gaussian kernels:
     ```
     κσ(t) = κ(t) * G(t,σ)
     ```
     where σ determines the scale of analysis

## Implementation Details

### Edge Detection Parameters
```python
MORPH_KERNEL_SIZE = 3  # Morphological operation kernel
BORDER_MARGIN = 20     # Border exclusion distance in pixels
MIN_CONTOUR_SIZE = 100 # Minimum valid contour size
```

### Intensity Analysis Parameters
```python
DEFAULT_SAMPLING_DEPTH = 20  # Pixels into cell
DEFAULT_VECTOR_WIDTH = 5     # Sampling region width
MIN_INTERIOR_RATIO = 0.6    # Required interior points ratio
```

### Curvature Analysis Parameters
```python
SPLINE_SMOOTHING = 0.1      # Spline fitting parameter
RESAMPLE_POINTS = 500       # Points for contour resampling
CURVATURE_SCALE = 3        # Gaussian smoothing sigma
```

## Technical Notes

1. **Performance Optimization**
   - Vectorized operations for intensity sampling
   - Efficient contour point management using NumPy arrays
   - Optimized spline calculations using SciPy

2. **Numerical Stability**
   - Robust normal vector calculation with error checking
   - Curvature calculation with singularity handling
   - Adaptive sampling based on local geometry

3. **Error Handling**
   - Boundary condition management
   - Invalid geometry detection
   - Missing data handling

## References

1. Suzuki, S. and Abe, K. (1985) Topological Structural Analysis of Digitized Binary Images by Border Following. CVGIP 30(1), 32-46.

2. Mokhtarian, F. and Mackworth, A. (1992) A Theory of Multi-Scale, Curvature-Based Shape Representation for Planar Curves. IEEE PAMI 14(8), 789-805.

3. Weickert, J. (1998) Anisotropic Diffusion in Image Processing. ECMI Series, Teubner-Verlag.