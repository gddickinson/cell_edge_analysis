# Membrane Curvature Analysis: Mathematical Framework and Implementation

## Mathematical Framework

### 1. Curvature Definition and Convention
Local membrane curvature (C) is defined as the reciprocal of the radius (R) of the best-fitting circle at a given point:

C = ±1/R

where the sign convention is:
- Positive (+): membrane bulging toward the cytosol
- Negative (-): membrane bulging away from the cytosol

### 2. Circle Fitting Algorithm
For each membrane segment, we employ an algebraic least squares method to fit a circle to n points {(x₁,y₁), ..., (xₙ,yₙ)}. The algorithm proceeds as follows:

a) Center the segment data:
   x̄ = 1/n ∑xᵢ
   ȳ = 1/n ∑yᵢ
   x'ᵢ = xᵢ - x̄
   y'ᵢ = yᵢ - ȳ

b) Construct the design matrix:
   Z = [z₁ x₁ y₁]
      [z₂ x₂ y₂]
      [... ... ...]
   where zᵢ = x'ᵢ² + y'ᵢ²

c) Solve the eigenvalue problem:
   (Z^T Z)v = λBv
   where B = diag(4,1,1)

d) Extract circle parameters from the eigenvector corresponding to the smallest eigenvalue:
   Center: (a,b) = (-v₁/2v₀, -v₂/2v₀)
   Radius: R = √(a² + b² - v₀/v₂)

### 3. Curvature Sign Determination
The sign of the curvature is determined by:
1. Computing the outward-pointing normal vector at the segment midpoint
2. Calculating the vector from the segment to the circle center
3. Taking the dot product of these vectors to determine orientation

## Implementation Details

### 1. Membrane Segmentation
- Adaptive sampling with N points (default: 75) evenly distributed along the membrane
- Local segments of length L (default: 9 units) centered on each sample point
- Gaussian smoothing (σ adjustable) for noise reduction

### 2. Scale Considerations
The implementation incorporates biologically relevant scales:
- Membrane thickness (h) ≈ 4 nm
- Typical h/R ratios:
  * Plasma membrane: ~10⁻⁴
  * Transport vesicles: ~10⁻¹
  * Endocytic intermediates: ~10⁻¹

### 3. Parameter Optimization
Key parameters with biological justification:
- Segment length: Optimized for local curvature detection while maintaining stability
- Sample density: Balanced between resolution and computational efficiency
- Smoothing: Reduces noise while preserving genuine membrane features

## Interactive Visualization System

### 1. Real-time Analysis Features
- Dynamic parameter adjustment
- Immediate visual feedback
- Curvature-mapped color coding
- Reference markers for biological structures

### 2. Visualization Components
- Main display: Membrane outline with curvature-colored segments
- Colorbar: Symmetric scale with biological reference points
- h/R ratio scale: Direct relationship to membrane geometry
- Sample points: Visual verification of measurement locations
