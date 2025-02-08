# EdgeDetector Documentation

## Biological Background
Cell edge detection is crucial for understanding cell morphology and membrane dynamics. In TIRF microscopy:
- The cell-substrate interface appears as a high-contrast boundary
- Edge detection identifies the membrane region where PIEZO1 mechanosensing occurs
- Edge smoothness reflects underlying cytoskeletal structure and membrane tension

## Mathematical Framework

### Edge Detection Theory
The edge detection pipeline implements multiple stages of mathematical processing:

1. **Binary Image Processing**
   ```
   B(x,y) ∈ {0,1}: Binary image
   E = {(x,y) | B(x,y) = 1 ∧ ∃(x',y') ∈ N(x,y) : B(x',y') = 0}
   ```
   where E is the edge set and N(x,y) is the 8-neighborhood of point (x,y)

2. **Morphological Operations**
   - Opening operation: A ∘ B = (A ⊖ B) ⊕ B
   - Small object removal: Connected components < threshold
   - Hole filling using flood-fill algorithms

3. **Contour Extraction**
   Uses border following algorithm (Suzuki & Abe, 1985):
   ```
   C = {p₁, p₂, ..., pₙ}
   where pᵢ are boundary pixels in clockwise order
   ```

### Savitzky-Golay Smoothing
Applied to reduce pixel noise while preserving edge features:

1. **Filter Theory**
   For a window of size M = 2m + 1:
   ```
   x_smooth(n) = Σ[k=-m to m] h(k)x(n+k)
   ```
   where h(k) are the Savitzky-Golay coefficients

2. **Polynomial Fitting**
   - Local least-squares polynomial approximation
   - Degree p < window size
   - Preserves moments up to order p

3. **Periodic Boundary Conditions**
   ```
   x_padded[i] = x[i mod N] for i ∈ [-m, N+m]
   ```
   Ensures continuity at contour endpoints

## Implementation Details

### Edge Detection Pipeline
```python
1. Binary image preparation
   - Type conversion to uint8
   - Small object removal (min_size=100)
   - Connected component analysis

2. Contour extraction
   - cv2.findContours with RETR_EXTERNAL
   - Largest contour selection by area
   - Point sequence extraction

3. Contour smoothing
   - Window size validation
   - Polynomial order selection
   - Separate x,y coordinate smoothing
```

### Key Methods

#### smooth_contour
**Purpose**: Reduces pixel quantization noise while preserving edge geometry
- Input: Raw contour points, window size
- Process:
  1. Ensures odd window size
  2. Calculates appropriate polynomial order
  3. Applies periodic boundary conditions
  4. Performs coordinate smoothing
- Output: Smoothed contour points

#### get_contour
**Purpose**: Provides access to appropriate contour version
- Selection logic:
  1. Returns smoothed contour if available
  2. Falls back to original contour
  3. Handles frame indexing

#### get_edge_image
**Purpose**: Generates visualization of detected edges
- Features:
  1. Original contour in full intensity (255)
  2. Smoothed contour in half intensity (128)
  3. Separate drawing to prevent overlap

## Biological Considerations

### Edge Detection Quality
Important biological factors affecting edge detection:
1. **Membrane Properties**
   - Local membrane tension
   - Cytoskeletal attachment points
   - Membrane protein density

2. **Image Quality Factors**
   - Signal-to-noise ratio
   - Photobleaching effects
   - Cell movement during acquisition

3. **Cell Type Specific Considerations**
   - Membrane morphology
   - Adhesion patterns
   - Edge complexity

### Smoothing Considerations

#### Window Size Selection
Balance between noise reduction and feature preservation:
- Too small: Insufficient noise reduction
- Too large: Loss of biologically relevant features
- Typical range: 3-21 pixels

#### Biological Feature Scales
Important length scales to consider:
- Membrane proteins: ~10-100 nm
- Focal adhesions: ~0.5-2 μm
- Membrane ruffles: ~1-5 μm

## Technical Parameters

### Edge Detection Parameters
```python
MIN_CONTOUR_SIZE = 100  # Minimum valid contour size (pixels)
POLY_ORDER = 3         # Polynomial order for smoothing
BOUNDARY_MODE = 'wrap' # Periodic boundary conditions
```

### Smoothing Controls
- Window size: Adjustable via UI
- Polynomial order: Automatically calculated
- Boundary handling: Periodic conditions

### Quality Metrics
1. Contour continuity
2. Feature preservation
3. Noise reduction
4. Edge position accuracy

## Error Handling

### Common Issues
1. **No Contour Found**
   - Causes: Poor segmentation, small objects
   - Handling: Returns None, reports error

2. **Smoothing Failures**
   - Causes: Window size issues, singular matrices
   - Handling: Returns original contour

3. **Memory Management**
   - Frame-by-frame processing
   - Dictionary-based storage
   - Cleanup on reprocessing

## References

1. Suzuki, S. and Abe, K. (1985) Topological Structural Analysis of Digitized Binary Images by Border Following. CVGIP 30(1), 32-46.

2. Savitzky, A. and Golay, M.J.E. (1964) Smoothing and Differentiation of Data by Simplified Least Squares Procedures. Analytical Chemistry 36(8), 1627-1639.

3. Shen, J. and Castan, S. (1992) An Optimal Linear Operator for Step Edge Detection. CVGIP: Graphical Models and Image Processing 54(2), 112-133.