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
                # BUGFIX: Make sure we're consistently using the smoothed contour
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
                        # BUGFIX: Make sure to use the points defined earlier, not edge_data.contour
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
                    # BUGFIX: Use the correct points corresponding to valid indices
                    points=points[self.valid_indices],
                    curvatures=np.array(curvatures),
                    segment_indices=segment_indices,
                    ref_curvatures=self.ref_curvatures,
                    radius_scale=self.params.radius_scale
                )
            except Exception as e:
                print(f"Error in curvature calculation: {e}")
                return None


    def calculate_geometric_curvature(
            self,
            edge_data: EdgeData,
            valid_indices: Optional[np.ndarray] = None
        ) -> Optional[CurvatureData]:
            """
            Calculate curvature at each sample point using geometric classification.

            This method uses a simple geometric approach to classify curvature:
            - Positive curvature: point is outside the line connecting adjacent points (on the side of the wound)
            - Negative curvature: point is inside the line connecting adjacent points (on the side of the monolayer)

            The magnitude of curvature is estimated based on the distance from the point to the line.

            As suggested by Jinghao
            """
            try:
                # Get the contour
                contour = edge_data.smoothed_contour if edge_data.smoothed_contour is not None else edge_data.contour
                original_contour = edge_data.contour  # Keep reference to original contour
                n_points = len(contour)

                # For debugging
                print(f"Geometric: contour length = {len(contour)}, original contour length = {len(original_contour)}")

                # Use provided indices or generate new ones
                if valid_indices is not None:
                    sample_indices = valid_indices
                else:
                    sample_indices = np.linspace(0, n_points-1, self.params.n_samples, dtype=int)

                # Arrays to store results
                valid_points = []
                curvatures = []
                segment_indices = []
                self.valid_indices = []
                self.original_indices = []  # NEW: Store indices for original contour

                for idx in sample_indices:
                    try:
                        # Get adjacent points (previous and next)
                        prev_idx = (idx - 1) % n_points
                        next_idx = (idx + 1) % n_points

                        # Get coordinates
                        prev_point = contour[prev_idx]
                        current_point = contour[idx]
                        next_point = contour[next_idx]

                        # Calculate vectors
                        vec_prev_to_next = next_point - prev_point
                        vec_prev_to_current = current_point - prev_point

                        # Calculate cross product to determine position
                        # For 2D, the cross product is a scalar (z-component)
                        cross_product = vec_prev_to_next[0] * vec_prev_to_current[1] - vec_prev_to_next[1] * vec_prev_to_current[0]

                        # Determine curvature sign based on cross product
                        # We'll create a vector pointing from the contour center to the current point
                        contour_center = np.mean(contour, axis=0)
                        to_center_vector = contour_center - current_point

                        # Calculate the normal vector (perpendicular to the line from prev to next)
                        normal = np.array([-vec_prev_to_next[1], vec_prev_to_next[0]])
                        normal = normal / np.linalg.norm(normal)  # Normalize

                        # The dot product will tell us if the normal points toward or away from the center
                        dot_product = np.dot(normal, to_center_vector)

                        # If the dot product is positive, the normal points toward the center
                        sign_factor = -1 if dot_product > 0 else 1

                        # Set sign of curvature based on cross product and orientation
                        curvature_sign = sign_factor * np.sign(cross_product)

                        # Calculate magnitude of curvature
                        # We'll use the distance of the point to the line as a proxy for curvature magnitude
                        line_length = np.linalg.norm(vec_prev_to_next)
                        if line_length > 0:
                            # Height of the triangle formed by the three points
                            height = abs(cross_product) / line_length

                            chord_length = line_length
                            if height > 0:
                                radius = (height**2 + (chord_length/2)**2) / (2*height)
                                # Scale to physical units (nm⁻¹)
                                curvature_magnitude = 1 / (radius * self.params.pixel_size)
                            else:
                                curvature_magnitude = 0
                        else:
                            curvature_magnitude = 0

                        # Combine sign and magnitude
                        curvature = curvature_sign * curvature_magnitude

                        # Skip if curvature is zero
                        if curvature == 0:
                            continue

                        # Get segment for visualization
                        half_segment = self.params.segment_length // 2
                        segment_indices_array = np.arange(idx - half_segment, idx + half_segment + 1) % n_points

                        # Store valid measurements
                        valid_points.append(current_point)
                        curvatures.append(curvature)
                        segment_indices.append(segment_indices_array.tolist())
                        self.valid_indices.append(idx)

                        # NEW: Map this point to original contour if different
                        if contour is not original_contour:
                            # Find closest point in original contour
                            distances = np.linalg.norm(original_contour - current_point, axis=1)
                            closest_idx = np.argmin(distances)
                            self.original_indices.append(closest_idx)
                        else:
                            self.original_indices.append(idx)

                    except Exception as e:
                        print(f"Error calculating geometric curvature at index {idx}: {e}")
                        continue

                if not curvatures:
                    return None

                # Convert valid_indices to numpy array
                self.valid_indices = np.array(self.valid_indices)
                self.original_indices = np.array(self.original_indices)  # NEW

                print(f"Geometric: Found {len(self.valid_indices)} valid points")
                print(f"Geometric: valid_indices max = {max(self.valid_indices) if len(self.valid_indices) > 0 else 'empty'}")
                print(f"Geometric: original_indices max = {max(self.original_indices) if len(self.original_indices) > 0 else 'empty'}")

                return CurvatureData(
                    points=np.array(valid_points),
                    curvatures=np.array(curvatures),
                    segment_indices=segment_indices,
                    ref_curvatures=self.ref_curvatures,
                    radius_scale=self.params.radius_scale
                )

            except Exception as e:
                print(f"Error in geometric curvature calculation: {e}")
                return None



    # def get_valid_indices(self) -> Optional[np.ndarray]:
    #     """Return indices of valid sampling points."""
    #     return self.valid_indices


    def get_valid_indices(self) -> Optional[np.ndarray]:
        """Return indices of valid sampling points mapped to the original contour if available."""
        if hasattr(self, 'original_indices') and self.original_indices is not None:
            return self.original_indices
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

    def calculate_moving_window_curvature(
            self,
            edge_data: EdgeData
        ) -> Optional[CurvatureData]:
            """Calculate curvature using a moving window approach."""
            try:
                # Get contour points
                points = edge_data.smoothed_contour if edge_data.smoothed_contour is not None else edge_data.contour
                n_points = len(points)

                print(f"Moving window analysis: contour has {n_points} points")

                half_segment = self.params.segment_length // 2

                # Arrays to store results
                all_points = []
                all_curvatures = []
                all_indices = []
                self.valid_indices = []  # Store point indices for reference

                # Using window_step to control the sliding increment
                step = max(1, self.params.window_step)  # Ensure step is at least 1

                # Slide window along all points
                for i in range(0, n_points, step):
                    try:
                        # Create segment indices centered at current point
                        indices = np.arange(i - half_segment, i + half_segment + 1) % n_points
                        segment = points[indices]

                        if len(segment) < 3:
                            continue

                        # Calculate curvature for this window
                        curvature = self._fit_circle_to_segment(segment)

                        # Store valid measurements
                        if curvature != 0:
                            all_points.append(points[i])
                            all_curvatures.append(curvature)
                            all_indices.append(indices.tolist())
                            self.valid_indices.append(i)
                    except Exception as e:
                        print(f"Error processing point {i}: {e}")
                        continue

                if not all_curvatures:
                    print("No valid curvature measurements found")
                    return None

                print(f"Moving window found {len(all_curvatures)} valid measurements")

                # Convert to numpy arrays
                self.valid_indices = np.array(self.valid_indices)

                return CurvatureData(
                    points=np.array(all_points),
                    curvatures=np.array(all_curvatures),
                    segment_indices=all_indices,
                    ref_curvatures=self.ref_curvatures,
                    radius_scale=self.params.radius_scale
                )

            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error in moving window curvature calculation: {e}")
                return None

    def calculate_spline_curvature(
            self,
            edge_data: EdgeData
        ) -> Optional[CurvatureData]:
            """Calculate curvature using spline fitting."""
            try:
                from scipy.interpolate import splprep, splev
                from scipy.signal import savgol_filter

                # Get contour points
                points = edge_data.smoothed_contour if edge_data.smoothed_contour is not None else edge_data.contour
                n_points = len(points)

                # Extract x and y coordinates
                x = points[:, 0]
                y = points[:, 1]

                # Create periodic parameter for the points
                t = np.linspace(0, 1, n_points)

                # Fit a periodic spline to the contour
                # The s parameter controls smoothing (s=0 forces exact interpolation)
                smoothing = self.params.spline_smoothing
                tck, u = splprep([x, y], u=t, s=smoothing, per=1)

                # Sample points from the spline at regular intervals
                # Use more points than original for smoother derivatives
                num_samples = min(self.params.n_samples, n_points)
                step = max(1, n_points // num_samples)
                sample_indices = np.arange(0, n_points, step)

                u_samples = t[sample_indices]

                # Evaluate the spline and its derivatives
                # spline_points: [x, y]
                # spline_1st_deriv: [dx/du, dy/du]
                # spline_2nd_deriv: [d²x/du², d²y/du²]
                spline_points = np.array(splev(u_samples, tck, der=0)).T
                spline_1st_deriv = np.array(splev(u_samples, tck, der=1)).T
                spline_2nd_deriv = np.array(splev(u_samples, tck, der=2)).T

                # Calculate curvature using the formula:
                # κ = (x'y'' - y'x'') / (x'² + y'²)^(3/2)
                curvatures = []
                valid_points = []
                segment_indices = []
                valid_indices = []

                for i, (point, d1, d2) in enumerate(zip(spline_points, spline_1st_deriv, spline_2nd_deriv)):
                    try:
                        numerator = d1[0] * d2[1] - d1[1] * d2[0]
                        denominator = (d1[0]**2 + d1[1]**2)**(1.5)

                        if denominator < 1e-10:
                            continue

                        # Calculate curvature (in pixel space)
                        curvature = numerator / denominator

                        # Convert to physical units (nm⁻¹)
                        # Multiply by -1 to match the sign convention from circle fitting
                        # (positive curvature = bulging inward toward cytosol)
                        curvature = -curvature / self.params.pixel_size

                        # Smooth out extreme values (optional)
                        if np.abs(curvature) > 1.0 / (10 * self.params.pixel_size):
                            continue

                        # Find closest point in original contour for segment reference
                        closest_idx = sample_indices[i]

                        # Create segment indices centered on this point
                        half_segment = self.params.segment_length // 2
                        indices = np.arange(closest_idx - half_segment,
                                          closest_idx + half_segment + 1) % n_points

                        valid_points.append(point)
                        curvatures.append(curvature)
                        segment_indices.append(indices.tolist())
                        valid_indices.append(closest_idx)
                    except Exception as e:
                        print(f"Error calculating spline curvature at point {i}: {e}")
                        continue

                if not curvatures:
                    print("No valid spline curvature measurements found")
                    return None

                # Store valid indices for other functions
                self.valid_indices = np.array(valid_indices)

                return CurvatureData(
                    points=np.array(valid_points),
                    curvatures=np.array(curvatures),
                    segment_indices=segment_indices,
                    ref_curvatures=self.ref_curvatures,
                    radius_scale=self.params.radius_scale
                )

            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error in spline curvature calculation: {e}")
                return None
