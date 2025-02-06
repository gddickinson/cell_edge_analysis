# src/analysis/intensity_analyzer.py
import numpy as np
from scipy.interpolate import splprep, splev
import cv2

class IntensityAnalyzer:
    def __init__(self):
        self.sampling_depth = 10  # Default sampling depth in pixels
        self.interval = 5  # Default interval between measurements
        self.intensities = {}  # Dictionary to store intensities for each frame
        self.measurement_points = {}  # Dictionary to store measurement positions
        self.normal_vectors = {}  # Dictionary to store normal vectors

    def set_parameters(self, sampling_depth, interval):
        """Set analysis parameters."""
        self.sampling_depth = sampling_depth
        self.interval = interval

    def calculate_normal_vector(self, point1, point2):
        """
        Calculate normal vector between two points, pointing into the cell.
        The vector will point to the right when moving along the contour.
        """
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        # Get perpendicular vector (normal) pointing into the cell
        normal = np.array([dy, -dx])  # Changed sign to point inward
        # Normalize to unit vector
        length = np.sqrt(normal[0]**2 + normal[1]**2)
        if length > 0:
            normal = normal / length
        return normal

    def sample_intensity(self, image, point, normal, depth):
        """Sample intensity along normal vector."""
        intensities = []
        positions = np.linspace(0, depth, num=depth)

        for pos in positions:
            # Calculate sampling point
            sample_point = point + pos * normal
            # Convert to integer coordinates
            x, y = int(round(sample_point[0])), int(round(sample_point[1]))

            # Check bounds
            if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
                intensities.append(image[y, x])
            else:
                intensities.append(0)

        return np.mean(intensities)  # Return mean intensity

    def analyze_frame(self, piezo_image, contour, frame_index):
        """
        Analyze intensity along cell edge for a single frame.

        Args:
            piezo_image (np.ndarray): PIEZO1 fluorescence image
            contour (np.ndarray): Cell edge contour
            frame_index (int): Frame index
        """
        try:
            # Resample contour at regular intervals
            contour = contour.squeeze()
            tck, u = splprep([contour[:, 0], contour[:, 1]], s=0, per=1)
            u_new = np.linspace(0, 1, num=len(contour)//self.interval)
            points = np.column_stack(splev(u_new, tck))

            intensities = []
            normals = []

            # Calculate intensities along the contour
            for i in range(len(points)):
                # Get current and next point
                current = points[i]
                next_point = points[(i + 1) % len(points)]

                # Calculate normal vector
                normal = self.calculate_normal_vector(current, next_point)
                normals.append(normal)

                # Sample intensity
                intensity = self.sample_intensity(
                    piezo_image, current, normal, self.sampling_depth
                )
                intensities.append(intensity)

            # Store results
            self.intensities[frame_index] = np.array(intensities)
            self.measurement_points[frame_index] = points
            self.normal_vectors[frame_index] = np.array(normals)

            return True

        except Exception as e:
            print(f"Error analyzing frame {frame_index}: {e}")
            return False

    def get_frame_data(self, frame_index):
        """Get analysis results for specific frame."""
        return (self.intensities.get(frame_index),
                self.measurement_points.get(frame_index),
                self.normal_vectors.get(frame_index))
