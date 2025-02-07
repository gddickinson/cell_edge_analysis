# src/analysis/curvature.py
import numpy as np
from scipy.interpolate import splprep, splev, interp1d
from scipy.ndimage import gaussian_filter1d

class CurvatureAnalyzer:
    def __init__(self):
        self.curvature = {}
        self.smoothed_contours = {}

    def resample_contour(self, contour, target_points=500):
        """Resample contour to have fewer points."""
        # Calculate current arc lengths
        diff = np.diff(contour, axis=0)
        segment_lengths = np.sqrt(np.sum(diff**2, axis=1))
        arc_lengths = np.concatenate(([0], np.cumsum(segment_lengths)))

        # Create new sample points
        total_length = arc_lengths[-1]
        sample_distances = np.linspace(0, total_length, target_points)

        # Interpolate x and y coordinates
        resampled_x = np.interp(sample_distances, arc_lengths, contour[:, 0])
        resampled_y = np.interp(sample_distances, arc_lengths, contour[:, 1])

        return np.column_stack((resampled_x, resampled_y))

    def calculate_curvature(self, contour, frame_index, measurement_points=None, smoothing_sigma=3, spline_smoothing=0.1):
        """
        Calculate curvature along the cell edge.

        Args:
            contour (np.ndarray): Contour points array
            frame_index (int): Frame number
            measurement_points (np.ndarray): Points where intensity was measured
            smoothing_sigma (float): Gaussian smoothing sigma
            spline_smoothing (float): Spline smoothing parameter

        Returns:
            tuple: (curvature array, smoothed contour points)
        """
        try:
            if contour is None:
                print("Error: Contour is None")
                return None, None

            print(f"Original contour shape: {contour.shape}")

            if len(contour) < 3:
                print("Error: Contour has fewer than 3 points")
                return None, None

            # Ensure contour is properly shaped
            if len(contour.shape) > 2:
                contour = contour.squeeze()

            # Resample contour to fewer points for spline fitting
            resampled_contour = self.resample_contour(contour)
            print(f"Resampled contour shape: {resampled_contour.shape}")

            # Smooth contour points
            x = gaussian_filter1d(resampled_contour[:, 0], smoothing_sigma)
            y = gaussian_filter1d(resampled_contour[:, 1], smoothing_sigma)

            # Fit spline to contour
            try:
                tck, u = splprep([x, y], s=spline_smoothing, per=True, k=3)
                print("Spline fitting successful")
            except Exception as e:
                print(f"Error in spline fitting: {e}")
                return None, None

            # If measurement points provided, use those for curvature calculation
            if measurement_points is not None and len(measurement_points) > 0:
                print(f"Using {len(measurement_points)} measurement points for curvature")

                # Find parameter values for measurement points
                u_measured = np.zeros(len(measurement_points))
                for i, point in enumerate(measurement_points):
                    # Find closest point on spline
                    dists = (x - point[0])**2 + (y - point[1])**2
                    closest = np.argmin(dists)
                    u_measured[i] = u[closest]

                # Sort parameter values
                u_measured = np.sort(u_measured)

                # Calculate derivatives at measurement points
                x_new, y_new = splev(u_measured, tck)
                dx_dt, dy_dt = splev(u_measured, tck, der=1)
                d2x_dt2, d2y_dt2 = splev(u_measured, tck, der=2)
            else:
                # Use regular sampling if no measurement points provided
                u_new = np.linspace(0, 1, len(x))
                x_new, y_new = splev(u_new, tck)
                dx_dt, dy_dt = splev(u_new, tck, der=1)
                d2x_dt2, d2y_dt2 = splev(u_new, tck, der=2)

            # Calculate curvature
            denominator = (dx_dt * dx_dt + dy_dt * dy_dt)**1.5
            curvature = np.zeros_like(x_new)
            valid_indices = denominator > 1e-10
            curvature[valid_indices] = (dx_dt[valid_indices] * d2y_dt2[valid_indices] -
                                      dy_dt[valid_indices] * d2x_dt2[valid_indices]) / denominator[valid_indices]

            print(f"Curvature shape: {curvature.shape}")
            print(f"Curvature range: [{np.min(curvature)}, {np.max(curvature)}]")

            # Store results
            self.curvature[frame_index] = curvature
            self.smoothed_contours[frame_index] = np.column_stack((x_new, y_new))

            return curvature, self.smoothed_contours[frame_index]

        except Exception as e:
            print(f"Error calculating curvature for frame {frame_index}: {e}")
            import traceback
            print(traceback.format_exc())
            return None, None

    def get_curvature_data(self, frame_index):
        """Get curvature data for specific frame."""
        return (self.curvature.get(frame_index),
                self.smoothed_contours.get(frame_index))

    def classify_regions(self, frame_index, threshold=0.1):
        """Classify regions as convex or concave based on curvature."""
        curvature = self.curvature.get(frame_index)
        if curvature is None:
            return None, None

        convex_idx = np.where(curvature > threshold)[0]
        concave_idx = np.where(curvature < -threshold)[0]

        return convex_idx, concave_idx
