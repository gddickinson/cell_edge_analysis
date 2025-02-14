#!/usr/bin/env python3

import numpy as np
import cv2
from typing import Tuple, Optional, Dict, List
from ..utils.data_structures import (
    EdgeData, CurvatureData, FluorescenceData, AnalysisParameters, ImageData
)

class CoordinatedAnalysis:
    """Class to coordinate sampling between curvature and fluorescence analysis."""
    
    def __init__(self, edge_data: EdgeData, params: AnalysisParameters):
        self.edge_data = edge_data
        self.params = params
        self.contour = edge_data.smoothed_contour if edge_data.smoothed_contour is not None else edge_data.contour
        self.n_points = len(self.contour)
        
    def generate_sampling_points(self) -> np.ndarray:
        """Generate initial sampling points."""
        n_samples = min(self.params.n_samples, self.n_points)
        return np.linspace(0, self.n_points-1, n_samples, dtype=int)
        
    def get_segment_indices(self, point_idx: int, segment_length: int) -> np.ndarray:
        """Get indices for a segment centered on point_idx."""
        half_segment = segment_length // 2
        return np.arange(point_idx - half_segment,
                        point_idx + half_segment + 1) % self.n_points
        
    def check_point_validity(
        self,
        idx: int,
        fluor_image: np.ndarray,
        cell_mask: np.ndarray,
        border_margin: int = 20
    ) -> Tuple[bool, Optional[Dict]]:
        """Check if a point is valid for both curvature and fluorescence analysis."""
        try:
            # Get point coordinates
            current = self.contour[idx]
            
            # Check border proximity
            if (current[0] < border_margin or
                current[0] > fluor_image.shape[1] - border_margin or
                current[1] < border_margin or
                current[1] > fluor_image.shape[0] - border_margin):
                return False, None
            
            # Get segment for normal calculation
            segment_indices = self.get_segment_indices(idx, self.params.edge_segment)
            segment = self.contour[segment_indices].astype(float)
            
            # Calculate normal vector
            tangent = segment[-1] - segment[0]
            normal = np.array([-tangent[1], tangent[0]])
            norm = np.linalg.norm(normal)
            if norm < 1e-10:
                return False, None
            normal = normal / norm
            
            # Check if normal points into the cell
            test_point = current + normal * 5
            test_x, test_y = test_point.astype(int)
            if (0 <= test_x < cell_mask.shape[1] and 
                0 <= test_y < cell_mask.shape[0]):
                if cell_mask[test_y, test_x] == 0:  # If test point is outside
                    normal = -normal  # Flip normal to point inward
            
            # Create sampling rectangle
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
            
            rect_coords = rect_points.astype(int)
            
            # Check rectangle bounds
            if (np.any(rect_coords[:, 0] < 0) or
                np.any(rect_coords[:, 0] >= fluor_image.shape[1]) or
                np.any(rect_coords[:, 1] < 0) or
                np.any(rect_coords[:, 1] >= fluor_image.shape[0])):
                return False, None
            
            # Create mask and check interior overlap
            rect_mask = np.zeros_like(fluor_image, dtype=np.uint8)
            cv2.fillPoly(rect_mask, [rect_coords], 1)
            interior_overlap = (np.sum(rect_mask & (cell_mask > 0)) / 
                              np.sum(rect_mask) * 100)
            
            if interior_overlap < self.params.interior_threshold:
                return False, None
            
            # Return sampling data for valid point
            return True, {
                'center': current,
                'normal': normal,
                'rect_coords': rect_coords,
                'segment_indices': segment_indices,
                'interior_overlap': interior_overlap
            }
            
        except Exception as e:
            print(f"Error checking point validity: {e}")
            return False, None