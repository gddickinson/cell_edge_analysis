# CurvatureAnalyzer Documentation

## Biological Background
Cell membrane curvature is a critical regulator of:
- Membrane protein organization
- Mechanosensitive channel function
- Cell signaling and mechanotransduction
- Membrane-cytoskeleton interactions

Understanding local membrane curvature helps elucidate:
1. Preferential PIEZO1 localization
2. Potential activation zones
3. Membrane-protein structure relationships

## Mathematical Framework

### Contour Resampling
The resampling process ensures uniform point distribution using arc length parameterization:

1. Arc length calculation s(t):
   ```
   s(t) = ∫[0 to t] √((dx/dt)² + (dy/dt)²) dt
   ```

2. Uniform parameterization:
   ```
   t_new = s⁻¹(L * i/N), i = 0,...,N-1
   ```
   where:
   - L is total contour length
   - N is target_points
   - s⁻¹ is inverse arc length function

### Curvature Calculation
Local curvature κ quantifies the rate of change of the unit tangent vector:

1. Parametric curve representation:
   ```
   C(t) = (x(t), y(t))
   ```

2. Curvature formula:
   ```
   κ(t) = (x'y'' - y'x'') / (x'² + y'²)^(3/2)
   ```
   where:
   - Positive κ: Convex regions (bulging outward)
   - Negative κ: Concave regions (bulging inward)
   - Zero κ: Flat regions

### Spline Fitting
B-spline representation ensures smooth derivatives:

1. Spline basis:
   ```
   x(t) = Σᵢ Pᵢ,ₓ Bᵢ,ₖ(t)
   y(t) = Σᵢ Pᵢ,ᵧ Bᵢ,ₖ(t)
   ```
   where:
   - Pᵢ are control points
   - Bᵢ,ₖ are B-spline basis functions
   - k=3 for cubic splines

2. Smoothing parameter s controls fit:
   ```
   Σᵢ wᵢ|fᵢ - S(tᵢ)|² ≤ s
   ```
   where:
   - fᵢ are data points
   - S(t) is spline function
   - wᵢ are weights

## Implementation Details

### resample_contour Method
Purpose: Creates uniformly spaced points along contour
- Prevents bias from uneven point distribution
- Improves numerical stability
- Enables consistent scale analysis

Key steps:
1. Calculates cumulative arc length
2. Creates uniform distance array
3. Interpolates x,y coordinates

### calculate_curvature Method
Core curvature computation pipeline:
1. Input validation and preprocessing
2. Gaussian smoothing of coordinates
3. Spline fitting and derivative calculation
4. Curvature computation with singularity handling

#### Point Selection Strategy
Two modes of operation:
1. Measurement point-based:
   - Uses intensity sampling locations
   - Ensures direct correlation with intensity data
   - Maintains spatial correspondence

2. Regular sampling:
   - Uniform distribution along contour
   - Better for global shape analysis
   - More stable numerical behavior

## Mathematical Considerations

### Scale Dependencies
Curvature measurement depends on observation scale:
1. Local scale (small window):
   - More sensitive to membrane details
   - Higher noise susceptibility
   - Better for protein-scale features

2. Global scale (large window):
   - More stable measurements
   - Better for overall shape analysis
   - Misses fine details

### Numerical Stability
Several safeguards ensure reliable computation:
1. Denominator threshold for division
2. Gaussian pre-smoothing
3. Spline parameter optimization
4. Endpoint handling for periodic curves

## Biological Considerations

### Length Scales
Important biological scales to consider:
- PIEZO1 protein size (~25 nm)
- Membrane thickness (~4-5 nm)
- Local membrane deformations (~10-100 nm)
- Cell-scale features (>1 μm)

### Curvature Classification
Biological significance of different regimes:
1. High positive curvature:
   - Membrane protrusions
   - Potential activation zones
   - Protein clustering regions

2. High negative curvature:
   - Membrane invaginations
   - Endocytic regions
   - Stress concentration points

3. Low curvature:
   - Baseline membrane state
   - Reference for changes
   - Stable regions

## Parameter Selection

### Smoothing Parameters
- smoothing_sigma: Controls noise reduction
  * Too small: Noisy measurements
  * Too large: Loss of relevant features
  * Typical range: 2-5 pixels

### Spline Parameters
- spline_smoothing: Controls fit tightness
  * Small values (<0.1): Close to original points
  * Larger values (>1): More smoothing
  * Default: 0.1 for balance

### Resampling
- target_points: Controls spatial resolution
  * Too few: Miss features
  * Too many: Computational overhead
  * Typical: 500 points for cell-scale analysis

## Applications

### Shape Analysis
- Cell morphology quantification
- Dynamic shape changes
- Migration analysis

### Protein-Curvature Correlation
- PIEZO1 distribution analysis
- Curvature preference determination
- Activation zone identification

### Time Series Analysis
- Membrane dynamics
- Protein redistribution
- Mechanical response

## References

1. Do Carmo, M.P. (1976) Differential Geometry of Curves and Surfaces.

2. Kreyszig, E. (1991) Differential Geometry.

3. Syeda, R., et al. (2016) PIEZO1 Channels Are Inherently Mechanosensitive.

4. Cox, C.D., et al. (2019) Removal of the Mechanoprotective Influence of the Cytoskeleton Reveals PIEZO1 is Gated by Bilayer Tension.