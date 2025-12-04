#!/usr/bin/env python3
# src/analysis/edge_detection.py

import numpy as np
import cv2
from skimage import morphology
from scipy.ndimage import gaussian_filter1d
from typing import Tuple, Optional
from ..utils.data_structures import EdgeData, ImageData, AnalysisParameters

class EdgeDetector:
    """Class for detecting and processing cell edges from binary masks."""
    
    def __init__(self, params: AnalysisParameters):
        self.params = params
        
    def detect_edge(self, image_data: ImageData) -> Optional[EdgeData]:
        """Detect cell edge from binary segmentation."""
        try:
            # Clean up binary image
            cleaned = morphology.remove_small_objects(
                image_data.data > 0,
                min_size=self.params.min_size
            )
            cleaned = cleaned.astype(np.uint8)
            
            # Find contours using OpenCV
            contours, _ = cv2.findContours(
                cleaned,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_NONE
            )
            
            if not contours:
                return None
                
            # Get largest contour by area
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Create edge image
            edge_image = np.zeros_like(cleaned)
            cv2.drawContours(edge_image, [largest_contour], -1, 255, 2)
            
            # Create EdgeData object
            edge_data = EdgeData(
                contour=largest_contour.squeeze(),
                edge_image=edge_image
            )
            
            # Apply initial smoothing if needed
            if self.params.smoothing_sigma > 0:
                edge_data.smooth_contour(self.params.smoothing_sigma)
            
            return edge_data
            
        except Exception as e:
            print(f"Error in edge detection: {e}")
            return None
    
    def get_normal_vectors(self, edge_data: EdgeData, smooth: bool = True) -> np.ndarray:
        """Calculate normal vectors along the contour."""
        contour = edge_data.smoothed_contour if smooth else edge_data.contour
        n_points = len(contour)
        normals = np.zeros((n_points, 2))
        
        for i in range(n_points):
            # Get next point (with wraparound)
            next_idx = (i + 1) % n_points
            
            # Calculate tangent vector
            tangent = contour[next_idx] - contour[i]
            
            # Calculate normal vector (perpendicular to tangent)
            normal = np.array([-tangent[1], tangent[0]])
            
            # Normalize
            norm = np.linalg.norm(normal)
            if norm > 0:
                normal = normal / norm
                
            normals[i] = normal
            
        return normals
    
    def verify_normal_directions(
        self,
        edge_data: EdgeData,
        normals: np.ndarray,
        binary_image: np.ndarray
    ) -> np.ndarray:
        """Verify and correct normal vector directions to point inward."""
        verified_normals = normals.copy()
        
        for i, (point, normal) in enumerate(zip(edge_data.contour, normals)):
            # Test point slightly along normal direction
            test_point = point + normal * 5
            test_x, test_y = test_point.astype(int)
            
            # Check if coordinates are within image bounds
            if (0 <= test_x < binary_image.shape[1] and 
                0 <= test_y < binary_image.shape[0]):
                # If test point is outside cell (0), flip normal
                if binary_image[test_y, test_x] == 0:
                    verified_normals[i] = -normal
                    
        return verified_normals
    
    def get_sampling_points(
        self,
        edge_data: EdgeData,
        n_samples: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Get evenly spaced sampling points along the contour."""
        contour = edge_data.contour
        n_points = len(contour)
        
        # Generate evenly spaced indices
        sample_indices = np.linspace(0, n_points-1, n_samples, dtype=int)
        
        # Get points and corresponding normal vectors
        sample_points = contour[sample_indices]
        normals = self.get_normal_vectors(edge_data)[sample_indices]
        
        return sample_points, normals
    
    def debug_edge_detection(
        self,
        image_data: ImageData,
        edge_data: EdgeData
    ) -> dict:
        """Generate debug information for edge detection."""
        debug_info = {
            'n_points': len(edge_data.contour),
            'image_shape': image_data.shape,
            'contour_bounds': {
                'min': edge_data.contour.min(axis=0),
                'max': edge_data.contour.max(axis=0)
            }
        }
        
        # Check for potential issues
        debug_info['warnings'] = []
        
        # Check if contour touches image boundaries
        margin = 5
        if (np.any(edge_data.contour[:, 0] < margin) or
            np.any(edge_data.contour[:, 0] > image_data.shape[1] - margin) or
            np.any(edge_data.contour[:, 1] < margin) or
            np.any(edge_data.contour[:, 1] > image_data.shape[0] - margin)):
            debug_info['warnings'].append('Contour touches image boundaries')
            
        # Check for minimum number of points
        if len(edge_data.contour) < 100:
            debug_info['warnings'].append('Low number of contour points')
            
        return debug_info