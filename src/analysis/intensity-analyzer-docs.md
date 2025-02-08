# IntensityAnalyzer Documentation

## Biological Background
The IntensityAnalyzer class quantifies PIEZO1 protein distribution along cell membranes. PIEZO1 proteins are mechanosensitive ion channels that respond to membrane deformation. Their spatial distribution provides insights into:
- Local membrane mechanosensitivity
- Protein clustering behavior
- Potential mechanotransduction hotspots

## Mathematical Framework

### Normal Vector Calculation
The calculation of normal vectors involves determining the perpendicular direction to the cell edge that points into the cell interior. For a curve C(s) parameterized by arc length s:

1. Local tangent vector T(s):
   ```
   T(s) = (dx/ds, dy/ds)
   ```

2. Normal vector N(s):
   ```
   N(s) = (-dy/ds, dx/ds)
   ```

3. Averaged normal using window of size w:
   ```
   N_avg(s) = (1/w) ∫[s-w/2 to s+w/2] N(σ)dσ
   ```

### Interior Point Validation
The algorithm validates normal vector direction using a statistical sampling approach:

1. Point sampling along vector v from position p:
   ```
   p(t) = p₀ + tv, t ∈ [0, d]
   ```
   where d is the check_depth

2. Interior ratio calculation:
   ```
   r = n_interior / n_total
   ```
   where r > 0.6 indicates valid interior direction

### Intensity Sampling
Implements a rectangular sampling region defined by:

1. Region definition R(s):
   ```
   R(s) = {p + αn + βt | 0 ≤ α ≤ d, -w/2 ≤ β ≤ w/2}
   ```
   where:
   - p is the edge point
   - n is the normal vector
   - t is the tangent vector
   - d is sampling_depth
   - w is vector_width

2. Intensity measurements I(s):
   - Mean: μ(s) = (1/|R|) ∫∫_R I(x,y) dxdy
   - Maximum: max{I(x,y) | (x,y) ∈ R}
   - Minimum: min{I(x,y) | (x,y) ∈ R}

## Key Methods

### calculate_normal_vector
- Input: Point sequence, index, binary mask
- Process: 
  1. Calculates local edge direction using window averaging
  2. Generates two possible normal vectors
  3. Validates direction using interior point checking
  4. Falls back to simple point check if needed
- Output: Unit normal vector pointing into cell

### check_vector_direction
- Purpose: Validates that normal vectors point into cell interior
- Method: Statistical sampling along proposed direction
- Validation: Requires 60% of points to be inside cell
- Importance: Prevents measurement artifacts from incorrect sampling directions

### sample_intensity
- Function: Measures protein signal in sampling region
- Implementation:
  1. Creates linear point sequence along normal
  2. Samples intensity at each point
  3. Applies specified measurement type (mean/min/max)
- Boundary handling: Returns 0 for out-of-bounds points

### analyze_frame
- Primary analysis pipeline:
  1. Creates binary cell mask
  2. Resamples contour at regular intervals
  3. Computes normal vectors
  4. Measures intensities
  5. Filters invalid measurements

## Key Parameters

### Sampling Parameters
- sampling_depth: Distance into cell for measurement (μm)
- vector_width: Width of sampling region (μm)
- interval: Distance between measurement points (μm)

### Validation Parameters
- normal_window: Window size for direction averaging
- check_depth: Distance for interior validation
- check_points: Number of validation points

### Quality Control
- Border margin handling
- Interior point validation
- Vector direction verification
- Measurement point filtering

## Biological Considerations

### Sampling Strategy
The rectangular sampling approach accounts for:
1. PIEZO1 protein diffusion in membrane
2. TIRF microscopy point spread function
3. Local membrane topology

### Measurement Choices
Different measurement types serve specific purposes:
- Mean: Overall protein density
- Maximum: Peak clustering
- Minimum: Background estimation

### Spatial Resolution
Parameters should be chosen considering:
- TIRF microscopy resolution (~100 nm)
- PIEZO1 protein size (~25 nm)
- Membrane diffusion characteristics