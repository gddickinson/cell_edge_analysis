# src/analysis/curvature.py
import numpy as np
from scipy.interpolate import splprep, splev
from scipy.ndimage import gaussian_filter1d

class CurvatureAnalyzer:
    def __init__(self):
        self.curvature = None
        self.smoothed_contour = None

    def calculate_curvature(self, contour, smoothing_sigma=3, spline_smoothing=0.1):
        """
        Calculate curvature along the cell edge.

        Args:
            contour (np.ndarray): Contour points array
            smoothing_sigma (float): Gaussian smoothing sigma
            spline_smoothing (float): Spline smoothing parameter

        Returns:
            tuple: (curvature array, smoothed contour points)
        """
        if contour is None or len(contour) < 3:
            return None, None

        # Smooth contour points
        x = gaussian_filter1d(contour[:, 1], smoothing_sigma)
        y = gaussian_filter1d(contour[:, 0], smoothing_sigma)

        # Fit spline to contour
        tck, u = splprep([x, y], s=spline_smoothing, per=True)

        # Generate points along spline
        u_new = np.linspace(0, 1, len(x))
        x_new, y_new = splev(u_new, tck)

        # Calculate derivatives
        dx_dt = splev(u_new, tck, der=1)[0]
        dy_dt = splev(u_new, tck, der=1)[1]
        d2x_dt2 = splev(u_new, tck, der=2)[0]
        d2y_dt2 = splev(u_new, tck, der=2)[1]

        # Calculate curvature
        curvature = (dx_dt * d2y_dt2 - dy_dt * d2x_dt2) / (dx_dt * dx_dt + dy_dt * dy_dt)**1.5

        self.curvature = curvature
        self.smoothed_contour = np.column_stack((y_new, x_new))

        return curvature, self.smoothed_contour

    def classify_regions(self, threshold=0.1):
        """
        Classify regions as convex or concave based on curvature.

        Args:
            threshold (float): Curvature threshold for classification

        Returns:
            tuple: (convex indices, concave indices)
        """
        if self.curvature is None:
            return None, None

        convex_idx = np.where(self.curvature > threshold)[0]
        concave_idx = np.where(self.curvature < -threshold)[0]

        return convex_idx, concave_idx
