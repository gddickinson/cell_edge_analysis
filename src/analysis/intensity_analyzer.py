# src/analysis/intensity_analyzer.py
import numpy as np
from scipy.interpolate import splprep, splev
import cv2
from scipy.ndimage import binary_fill_holes

class IntensityAnalyzer:
    def __init__(self):
        self.sampling_depth = 20  # Default sampling depth in pixels
        self.vector_width = 5    # Default vector width in pixels
        self.interval = 5        # Default interval between measurements
        self.measure_type = 'mean'  # Default intensity measure type
        self.intensities = {}    # Dictionary to store intensities for each frame
        self.measurement_points = {}  # Dictionary to store measurement positions
        self.normal_vectors = {}  # Dictionary to store normal vectors
        self.border_margin = 20  # Pixels to exclude from edges

    def set_parameters(self, sampling_depth, vector_width, interval, measure_type):
        """
        Set analysis parameters.

        Args:
            sampling_depth (int): Distance to sample into cell
            vector_width (int): Width of sampling rectangle
            interval (int): Distance between measurement points
            measure_type (str): Type of intensity measurement ('mean', 'minimum', 'maximum')
        """
        self.sampling_depth = sampling_depth
        self.vector_width = vector_width
        self.interval = interval
        self.measure_type = measure_type
        print(f"Parameters set: depth={sampling_depth}, width={vector_width}, "
              f"interval={interval}, measure={measure_type}")  # Debug print

    def calculate_normal_vector(self, point1, point2, binary_mask):
        """
        Calculate normal vector between two points, ensuring it points into the cell.

        Args:
            point1, point2: Points along the contour
            binary_mask: Binary image of cell
        """
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]

        # Get both possible normal vectors
        normal1 = np.array([dy, -dx])
        normal2 = np.array([-dy, dx])

        # Normalize both vectors
        length1 = np.sqrt(normal1[0]**2 + normal1[1]**2)
        length2 = np.sqrt(normal2[0]**2 + normal2[1]**2)

        if length1 > 0 and length2 > 0:
            normal1 = normal1 / length1
            normal2 = normal2 / length2

            # Check which direction points into the cell
            test_dist = 5  # Test distance
            point = point1.astype(int)

            # Test points in both directions
            test_point1 = point + (normal1 * test_dist).astype(int)
            test_point2 = point + (normal2 * test_dist).astype(int)

            # Ensure test points are within image bounds
            shape = binary_mask.shape
            in_bounds1 = (0 <= test_point1[0] < shape[1] and
                         0 <= test_point1[1] < shape[0])
            in_bounds2 = (0 <= test_point2[0] < shape[1] and
                         0 <= test_point2[1] < shape[0])

            # Check which direction is inside the cell
            val1 = binary_mask[test_point1[1], test_point1[0]] if in_bounds1 else 0
            val2 = binary_mask[test_point2[1], test_point2[0]] if in_bounds2 else 0

            return normal1 if val1 > val2 else normal2

        return np.array([0, 0])

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

    def is_near_border(self, point, shape):
        """Check if a point is near the image border."""
        x, y = point
        return (x < self.border_margin or
                x > shape[1] - self.border_margin or
                y < self.border_margin or
                y > shape[0] - self.border_margin)

    def analyze_frame(self, piezo_image, contour, frame_index):
        """Analyze intensity along cell edge for a single frame."""
        try:
            # Create binary mask of cell interior with correct data type
            binary_mask = np.zeros_like(piezo_image, dtype=np.uint8)
            cv2.drawContours(binary_mask, [contour.astype(np.int32)], -1, 1, thickness=-1)
            binary_mask = binary_fill_holes(binary_mask).astype(np.uint8)  # Convert to uint8

            # Resample contour at regular intervals
            contour = contour.squeeze()
            tck, u = splprep([contour[:, 0], contour[:, 1]], s=0, per=1)
            u_new = np.linspace(0, 1, num=len(contour)//self.interval)
            points = np.column_stack(splev(u_new, tck))

            intensities = []
            normals = []
            filtered_points = []

            # Calculate intensities along the contour
            for i in range(len(points)):
                current = points[i]
                next_point = points[(i + 1) % len(points)]

                # Skip points near the border
                if not self.is_near_border(current, piezo_image.shape):
                    # Calculate normal vector pointing into cell
                    normal = self.calculate_normal_vector(
                        current, next_point, binary_mask
                    )

                    # Check if sampling region stays within borders
                    end_point = current + normal * self.sampling_depth
                    if not self.is_near_border(end_point, piezo_image.shape):
                        # Sample intensity
                        intensity = self.sample_intensity(
                            piezo_image, current, normal, self.sampling_depth
                        )

                        intensities.append(intensity)
                        normals.append(normal)
                        filtered_points.append(current)

            # Convert lists to arrays
            if filtered_points:  # Only store results if we have valid points
                self.intensities[frame_index] = np.array(intensities)
                self.measurement_points[frame_index] = np.array(filtered_points)
                self.normal_vectors[frame_index] = np.array(normals)
                return True
            else:
                print(f"No valid measurement points found in frame {frame_index}")
                return False

        except Exception as e:
            print(f"Error analyzing frame {frame_index}: {e}")
            return False

    def get_frame_data(self, frame_index):
        """Get analysis results for specific frame."""
        return (self.intensities.get(frame_index),
                self.measurement_points.get(frame_index),
                self.normal_vectors.get(frame_index))
