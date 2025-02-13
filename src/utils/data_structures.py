#!/usr/bin/env python3
# src/utils/data_structures.py

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import numpy as np

@dataclass
class ImageData:
    """Container for image data and metadata."""
    data: np.ndarray
    filename: str
    is_stack: bool = False
    current_frame: int = 0
    
    @property
    def shape(self):
        return self.data.shape

@dataclass
class EdgeData:
    """Container for cell edge detection results."""
    contour: np.ndarray
    edge_image: np.ndarray
    smoothed_contour: Optional[np.ndarray] = None
    
    def smooth_contour(self, sigma: float) -> np.ndarray:
        """Apply Gaussian smoothing to contour."""
        from scipy.ndimage import gaussian_filter1d
        if sigma > 0:
            self.smoothed_contour = gaussian_filter1d(
                self.contour.astype(float), sigma, axis=0)
        else:
            self.smoothed_contour = self.contour.copy()
        return self.smoothed_contour

@dataclass
class CurvatureData:
    """Container for curvature analysis results."""
    points: np.ndarray
    curvatures: np.ndarray
    segment_indices: List[List[int]]
    ref_curvatures: Dict[str, float]
    radius_scale: float = 100  # nm scale factor

@dataclass
class FluorescenceData:
    """Container for fluorescence analysis results."""
    sampling_points: List[Dict[str, Any]]
    intensity_values: np.ndarray
    sampling_regions: List[np.ndarray]
    interior_overlaps: List[float]
    
    @property
    def mean_intensities(self):
        return np.array([d['mean'] for d in self.sampling_points])
    
    @property
    def sampling_coordinates(self):
        return np.array([d['center'] for d in self.sampling_points])

@dataclass
class AnalysisParameters:
    """Container for analysis parameters."""
    # Common parameters
    n_samples: int = 75
    smoothing_sigma: float = 1.0
    min_size: int = 100
    
    # Curvature specific
    segment_length: int = 9
    membrane_thickness: float = 4  # nm
    radius_scale: float = 100  # scale factor nm
    
    # Fluorescence specific
    vector_width: int = 5
    vector_depth: int = 20
    edge_segment: int = 10
    interior_threshold: float = 0
    
    # Visualization
    line_width: int = 3
    background_alpha: float = 0.5
    rectangle_alpha: float = 0.3
    show_edge: bool = True