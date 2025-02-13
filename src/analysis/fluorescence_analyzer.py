#!/usr/bin/env python3
# src/analysis/fluorescence_analyzer.py

import numpy as np
import cv2
from typing import Optional, List, Dict, Tuple
from ..utils.data_structures import (
    EdgeData, FluorescenceData, ImageData, AnalysisParameters
    )

class FluorescenceAnalyzer:
    """Class for analyzing membrane-proximal fluorescence."""

    def __init__(self, params: AnalysisParameters):
        self.params = params
        self.valid_indices = None

    def calculate_intensities(
        self,
        edge_data: EdgeData,
        fluor_data: ImageData,
        cell_mask: ImageData,
        valid_indices: Optional[np.ndarray] = None
    ) -> Optional[FluorescenceData]:
        """Calculate fluorescence intensities along the membrane."""
        try:
            # Use either provided valid indices or generate new ones
            if valid_indices is not None:
                sample_indices = valid_indices
            else:
                n_points = len(edge_data.contour)
                n_samples = min(self.params.n_samples, n_points)
                sample_indices = np.linspace(0, n_points-1, n_samples, dtype=int)

            # Define border margin
            border_margin = 20

            # Create arrays to store valid measurements
            valid_points = []
            valid_intensities = []
            valid_regions = []
            valid_overlaps = []
            self.valid_indices = []  # Store indices of valid measurements

            for i, idx in enumerate(sample_indices):
                try:
                    # Get segment of points for smoothing
                    half_segment = self.params.edge_segment // 2
                    segment_indices = np.arange(idx - half_segment,
                                             idx + half_segment + 1) % len(edge_data.contour)
                    segment = edge_data.contour[segment_indices].astype(float)

                    # Get current point and calculate normal
                    intensity_data = self._calculate_single_intensity(
                        segment=segment,
                        fluor_image=fluor_data.data,
                        cell_mask=cell_mask.data,
                        border_margin=border_margin
                    )

                    if intensity_data is not None:
                        valid_points.append(intensity_data)
                        valid_intensities.append(intensity_data['mean'])
                        valid_regions.append(intensity_data['rect_coords'])
                        valid_overlaps.append(intensity_data['interior_overlap'])
                        self.valid_indices.append(idx)

                except Exception as e:
                    print(f"Error calculating intensity at index {idx}: {e}")
                    continue

            if not valid_points:
                return None

            # Convert valid_indices to numpy array
            self.valid_indices = np.array(self.valid_indices)

            # Create fluorescence data object with only valid measurements
            return FluorescenceData(
                sampling_points=valid_points,
                intensity_values=np.array(valid_intensities),
                sampling_regions=valid_regions,
                interior_overlaps=valid_overlaps
            )

        except Exception as e:
            print(f"Error in intensity calculation: {str(e)}")
            raise

    def get_valid_indices(self) -> Optional[np.ndarray]:
        """Return indices of valid sampling points."""
        return self.valid_indices

    def _calculate_single_intensity(
        self,
        segment: np.ndarray,
        fluor_image: np.ndarray,
        cell_mask: np.ndarray,
        border_margin: int
    ) -> Optional[dict]:
        """Calculate intensity for a single sampling point."""
        # Get current point (central point of segment)
        current = segment[len(segment)//2]

        # Skip points near image border
        if (current[0] < border_margin or
            current[0] > fluor_image.shape[1] - border_margin or
            current[1] < border_margin or
            current[1] > fluor_image.shape[0] - border_margin):
            return None

        # Calculate normal vector
        tangent = segment[-1] - segment[0]
        normal = np.array([-tangent[1], tangent[0]])
        norm = np.linalg.norm(normal)
        if norm < 1e-10:
            return None
        normal = normal / norm

        # Check if normal points into the cell
        test_point = current + normal * 5
        test_x, test_y = test_point.astype(int)
        if (0 <= test_x < cell_mask.shape[1] and
            0 <= test_y < cell_mask.shape[0]):
            if cell_mask[test_y, test_x] == 0:  # If test point is outside
                normal = -normal  # Flip the normal to point inward

        # Create sampling rectangle coordinates
        perpendicular = np.array([-normal[1], normal[0]])
        center = current + (normal * self.params.vector_depth / 2)
        half_width = self.params.vector_width / 2
        half_depth = self.params.vector_depth / 2

        rect_points = np.array([
            center - perpendicular * half_width - normal * half_depth,
            center + perpendicular * half_width - normal * half_depth,
            center + perpendicular * half_width + normal * half_depth,
            center - perpendicular * half_width + normal * half_depth
        ])

        # Get integer coordinates for sampling
        rect_coords = rect_points.astype(int)

        # Check if rectangle is fully within image bounds
        if (np.any(rect_coords[:, 0] < 0) or
            np.any(rect_coords[:, 0] >= fluor_image.shape[1]) or
            np.any(rect_coords[:, 1] < 0) or
            np.any(rect_coords[:, 1] >= fluor_image.shape[0])):
            return None

        # Create mask for the rectangle
        rect_mask = np.zeros_like(fluor_image, dtype=np.uint8)
        cv2.fillPoly(rect_mask, [rect_coords], 1)

        # Calculate percentage of rectangle that overlaps with cell interior
        interior_overlap = (np.sum(rect_mask & (cell_mask > 0)) /
                          np.sum(rect_mask) * 100)

        # Skip if doesn't meet interior threshold
        if interior_overlap < self.params.interior_threshold:
            return None

        # Sample fluorescence values using the mask
        mask = rect_mask.astype(bool)
        fluorescence_values = fluor_image[mask]

        if len(fluorescence_values) == 0:
            return None

        return {
            'mean': np.mean(fluorescence_values),
            'min': np.min(fluorescence_values),
            'max': np.max(fluorescence_values),
            'std': np.std(fluorescence_values),
            'rect_coords': rect_coords,
            'raw_values': fluorescence_values,
            'normal': normal,
            'center': current,
            'interior_overlap': interior_overlap
        }

    def get_intensity_statistics(
        self,
        fluor_data: FluorescenceData
    ) -> Dict[str, float]:
        """Calculate statistical measures of fluorescence intensity."""
        return {
            'mean': np.mean(fluor_data.intensity_values),
            'std': np.std(fluor_data.intensity_values),
            'min': np.min(fluor_data.intensity_values),
            'max': np.max(fluor_data.intensity_values),
            'median': np.median(fluor_data.intensity_values),
            'percentile_5': np.percentile(fluor_data.intensity_values, 5),
            'percentile_95': np.percentile(fluor_data.intensity_values, 95)
        }

    def debug_fluorescence_analysis(
        self,
        fluor_data: FluorescenceData
    ) -> dict:
        """Generate debug information for fluorescence analysis."""
        debug_info = {
            'n_samples': len(fluor_data.sampling_points),
            'statistics': self.get_intensity_statistics(fluor_data),
            'warnings': []
        }

        # Check interior overlap distribution
        low_overlap_threshold = 50
        n_low_overlap = sum(1 for overlap in fluor_data.interior_overlaps
                          if overlap < low_overlap_threshold)
        if n_low_overlap > 0:
            debug_info['warnings'].append(
                f'Found {n_low_overlap} sampling regions with <{low_overlap_threshold}% interior overlap')

        # Check for potentially saturated pixels
        max_intensities = [data['max'] for data in fluor_data.sampling_points]
        if any(intensity >= 255 for intensity in max_intensities):
            debug_info['warnings'].append('Some sampling regions contain saturated pixels')

        # Calculate coefficient of variation
        cv = np.std(fluor_data.intensity_values) / np.mean(fluor_data.intensity_values)
        debug_info['coefficient_of_variation'] = cv

        if cv > 1.0:
            debug_info['warnings'].append('High variation in fluorescence intensities')

        return debug_info
