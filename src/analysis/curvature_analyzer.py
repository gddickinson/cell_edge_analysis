#!/usr/bin/env python3
# src/analysis/curvature_analyzer.py

import numpy as np
from typing import Optional, List, Dict, Tuple
from ..utils.data_structures import EdgeData, CurvatureData, AnalysisParameters

class CurvatureAnalyzer:
    """Class for analyzing membrane curvature."""

    def __init__(self, params: AnalysisParameters):
        self.params = params
        self.valid_indices = None  # Store valid sampling indices
        self.ref_curvatures = {
            'plasma_membrane': 1/(10000),
            'transport_vesicle': 1/(40),
            'endocytic_vesicle': 1/(100)
        }

    def calculate_curvature(
            self,
            edge_data: EdgeData,
            valid_indices: Optional[np.ndarray] = None
        ) -> Optional[CurvatureData]:
            """Calculate curvature at each sample point using circular arc fitting."""
            try:
                points = edge_data.smoothed_contour if edge_data.smoothed_contour is not None else edge_data.contour
                n_points = len(points)
                half_segment = self.params.segment_length // 2
                curvatures = []
                segment_indices = []
                self.valid_indices = []

                # Use provided indices or generate new ones
                if valid_indices is not None:
                    sample_indices = valid_indices
                else:
                    sample_indices = np.linspace(0, n_points-1, self.params.n_samples, dtype=int)

                for idx in sample_indices:
                    try:
                        indices = np.arange(idx - half_segment, idx + half_segment + 1) % n_points
                        segment = points[indices]

                        if len(segment) < 3:
                            continue

                        curvature = self._fit_circle_to_segment(segment)
                        if curvature != 0:  # Only keep valid measurements
                            curvatures.append(curvature)
                            segment_indices.append(indices.tolist())
                            self.valid_indices.append(idx)

                    except Exception as e:
                        print(f"Error calculating curvature at index {idx}: {e}")
                        continue

                if not curvatures:
                    return None

                # Convert valid_indices to numpy array
                self.valid_indices = np.array(self.valid_indices)

                return CurvatureData(
                    points=points[self.valid_indices],
                    curvatures=np.array(curvatures),
                    segment_indices=segment_indices,
                    ref_curvatures=self.ref_curvatures,
                    radius_scale=self.params.radius_scale
                )

            except Exception as e:
                print(f"Error in curvature calculation: {e}")
                return None

    def get_valid_indices(self) -> Optional[np.ndarray]:
        """Return indices of valid sampling points."""
        return self.valid_indices

    def _fit_circle_to_segment(self, segment: np.ndarray) -> float:
        """Fit circle to segment and return signed curvature."""
        if len(segment) < 3:
            return 0

        # Translate segment to origin
        center = segment.mean(axis=0)
        centered = segment - center

        # Scale coordinates to nanometers
        centered = centered * self.params.pixel_size

        # Apply algebraic circle fitting
        x = centered[:, 0]
        y = centered[:, 1]
        z = x*x + y*y

        # Check for valid values
        if np.any(np.isnan(z)) or np.any(np.isinf(z)):
            return 0

        ZXY = np.column_stack((z, x, y))
        A = np.dot(ZXY.T, ZXY)
        B = np.array([[4, 0, 0], [0, 1, 0], [0, 0, 1]])

        try:
            # Compute eigenvalues and eigenvectors
            eigenvalues, eigenvectors = np.linalg.eig(np.dot(np.linalg.inv(B), A))

            # Check for valid eigenvalues
            if np.any(np.isnan(eigenvalues)) or np.any(np.isinf(eigenvalues)):
                return 0

            # Get eigenvector corresponding to smallest eigenvalue
            v = eigenvectors[:, np.argmin(np.abs(eigenvalues))]

            # Check for valid eigenvector
            if np.any(np.isnan(v)) or np.any(np.isinf(v)) or np.abs(v[0]) < 1e-10:
                return 0

            # Calculate center and radius of fitted circle
            a = -v[1]/(2*v[0])
            b = -v[2]/(2*v[0])

            # Check term under square root
            radicand = a*a + b*b - v[0]/v[2]
            if radicand <= 0:
                return 0

            r = np.sqrt(radicand)  # Radius is now in nanometers

            # Verify the fit is reasonable
            min_radius = self.params.segment_length * self.params.pixel_size / 2
            if (not np.isfinite(r) or r < min_radius):
                return 0

            # Calculate outward-pointing normal
            segment_dir = segment[-1] - segment[0]
            normal = np.array([-segment_dir[1], segment_dir[0]])
            normal_norm = np.linalg.norm(normal)

            if normal_norm < 1e-10:
                return 0

            normal = normal / normal_norm

            # Determine if normal points outward
            center_point = np.array([a, b]) / self.params.pixel_size + center
            to_center = center_point - segment.mean(axis=0)
            to_center_norm = np.linalg.norm(to_center)

            if to_center_norm > 0:
                # Curvature is positive when bulging inward (cytosol)
                sign = -np.sign(np.dot(to_center/to_center_norm, normal))
                curvature = (1/r) * sign  # Curvature is now in nm^-1
            else:
                curvature = 0

            return curvature

        except (np.linalg.LinAlgError, ValueError, ZeroDivisionError):
            return 0

    def get_curvature_statistics(self, curvature_data: CurvatureData) -> Dict[str, float]:
        """Calculate statistical measures of curvature."""
        curvatures = curvature_data.curvatures
        valid_curvatures = curvatures[curvatures != 0]

        if len(valid_curvatures) == 0:
            return {
                'mean': 0,
                'std': 0,
                'min': 0,
                'max': 0,
                'median': 0
            }

        return {
            'mean': np.mean(valid_curvatures),
            'std': np.std(valid_curvatures),
            'min': np.min(valid_curvatures),
            'max': np.max(valid_curvatures),
            'median': np.median(valid_curvatures)
        }

    def debug_curvature_analysis(self, curvature_data: CurvatureData) -> dict:
        """Generate debug information for curvature analysis."""
        debug_info = {
            'n_samples': len(curvature_data.curvatures),
            'n_valid_measurements': np.sum(curvature_data.curvatures != 0),
            'statistics': self.get_curvature_statistics(curvature_data),
            'warnings': []
        }

        # Check for potential issues
        zero_curvatures = np.sum(curvature_data.curvatures == 0)
        if zero_curvatures > 0:
            debug_info['warnings'].append(
                f'Found {zero_curvatures} points with zero curvature')

        # Check for extreme curvatures
        abs_curvatures = np.abs(curvature_data.curvatures[curvature_data.curvatures != 0])
        if len(abs_curvatures) > 0:
            extreme_threshold = np.percentile(abs_curvatures, 99) * 2
            n_extreme = np.sum(abs_curvatures > extreme_threshold)
            if n_extreme > 0:
                debug_info['warnings'].append(
                    f'Found {n_extreme} points with extreme curvature values')

        return debug_info
