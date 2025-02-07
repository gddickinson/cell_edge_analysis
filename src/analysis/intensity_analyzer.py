# src/analysis/intensity_analyzer.py
import numpy as np
from scipy.interpolate import splprep, splev
import cv2
from scipy.ndimage import binary_fill_holes

class IntensityAnalyzer:
    def __init__(self):
        # Analysis parameters
        self.sampling_depth = 20
        self.vector_width = 5
        self.interval = 5
        self.measure_type = 'mean'
        self.normal_window = 5

        # Interior check parameters
        self.use_interior_check = True
        self.check_depth = 10
        self.check_points = 10

        # Storage
        self.intensities = {}
        self.measurement_points = {}
        self.normal_vectors = {}
        self.border_margin = 20

    def set_parameters(self, sampling_depth, vector_width, interval, measure_type,
                      normal_window=5, use_interior_check=True, check_depth=10,
                      check_points=10):
        """Set all analysis parameters."""
        self.sampling_depth = sampling_depth
        self.vector_width = vector_width
        self.interval = interval
        self.measure_type = measure_type
        self.normal_window = normal_window
        self.use_interior_check = use_interior_check
        self.check_depth = check_depth
        self.check_points = check_points
        print(f"Parameters set: depth={sampling_depth}, width={vector_width}, "
              f"interval={interval}, measure={measure_type}, "
              f"normal_window={normal_window}, use_interior={use_interior_check}, "
              f"check_depth={check_depth}, check_points={check_points}")

    def check_vector_direction(self, point, normal, binary_mask):
        """
        Check if vector points into cell interior.
        Returns interior_ratio for better decision making.
        """
        print(f"Checking vector direction at point {point}")  # Debug
        interior_points = 0
        total_valid_points = 0
        check_points = np.linspace(0, self.check_depth, self.check_points)

        for dist in check_points:
            check_point = point + normal * dist
            x, y = int(round(check_point[0])), int(round(check_point[1]))

            if (0 <= x < binary_mask.shape[1] and
                0 <= y < binary_mask.shape[0]):
                total_valid_points += 1
                if binary_mask[y, x]:
                    interior_points += 1

        if total_valid_points == 0:
            return 0

        interior_ratio = interior_points / total_valid_points
        print(f"Interior ratio: {interior_ratio}")  # Debug
        return interior_ratio

    def calculate_normal_vector(self, points, index, binary_mask):
        """Calculate normal vector using window and interior check."""
        n_points = len(points)
        half_window = self.normal_window // 2

        # Get window of points
        window_indices = [(index + i) % n_points
                         for i in range(-half_window, half_window + 1)]
        window_points = points[window_indices]

        # Calculate average direction
        dx = np.mean(np.diff(window_points[:, 0]))
        dy = np.mean(np.diff(window_points[:, 1]))

        # Get both possible normal vectors
        normal1 = np.array([dy, -dx])
        normal2 = np.array([-dy, dx])

        # Normalize vectors
        length1 = np.sqrt(normal1[0]**2 + normal1[1]**2)
        length2 = np.sqrt(normal2[0]**2 + normal2[1]**2)

        if length1 > 0 and length2 > 0:
            normal1 = normal1 / length1
            normal2 = normal2 / length2

            point = points[index].astype(int)

            if self.use_interior_check:
                # Check interior ratios for both directions
                ratio1 = self.check_vector_direction(point, normal1, binary_mask)
                ratio2 = self.check_vector_direction(point, normal2, binary_mask)

                print(f"Normal1 ratio: {ratio1}, Normal2 ratio: {ratio2}")  # Debug

                # Use ratio comparison for decision
                if ratio1 > 0.6:  # Require at least 60% interior points
                    return normal1
                elif ratio2 > 0.6:
                    return normal2
                else:
                    # If neither direction is good, try simpler check
                    print("Both ratios too low, using fallback check")  # Debug

            # Fallback to simpler check
            test_dist = 5
            test_point1 = point + (normal1 * test_dist).astype(int)
            test_point2 = point + (normal2 * test_dist).astype(int)

            # Check bounds
            shape = binary_mask.shape
            in_bounds1 = (0 <= test_point1[0] < shape[1] and
                         0 <= test_point1[1] < shape[0])
            in_bounds2 = (0 <= test_point2[0] < shape[1] and
                         0 <= test_point2[1] < shape[0])

            # Check cell interior
            val1 = binary_mask[test_point1[1], test_point1[0]] if in_bounds1 else 0
            val2 = binary_mask[test_point2[1], test_point2[0]] if in_bounds2 else 0

            chosen_normal = normal1 if val1 > val2 else normal2
            print(f"Chosen normal direction: {chosen_normal}")  # Debug
            return chosen_normal

        return np.array([0, 0])

    def analyze_frame(self, piezo_image, contour, frame_index):
        """Analyze intensity along cell edge for a single frame."""
        try:
            # Create binary mask of cell interior
            binary_mask = np.zeros_like(piezo_image, dtype=np.uint8)
            cv2.drawContours(binary_mask, [contour.astype(np.int32)], -1, 1, thickness=-1)
            binary_mask = binary_fill_holes(binary_mask).astype(np.uint8)

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

                # Skip points near the border
                if not self.is_near_border(current, piezo_image.shape):
                    # Calculate normal vector
                    normal = self.calculate_normal_vector(points, i, binary_mask)

                    # Only use points where we got a valid normal
                    if np.any(normal != 0):
                        # Sample intensity
                        intensity = self.sample_intensity(
                            piezo_image, current, normal, self.sampling_depth
                        )

                        intensities.append(intensity)
                        normals.append(normal)
                        filtered_points.append(current)

            # Convert lists to arrays
            if filtered_points:
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

    def is_near_border(self, point, shape):
        """Check if a point is near the image border."""
        x, y = point
        return (x < self.border_margin or
                x > shape[1] - self.border_margin or
                y < self.border_margin or
                y > shape[0] - self.border_margin)

    def sample_intensity(self, image, point, normal, depth):
        """Sample intensity along normal vector."""
        intensities = []
        positions = np.linspace(0, depth, num=depth)

        for pos in positions:
            sample_point = point + pos * normal
            x, y = int(round(sample_point[0])), int(round(sample_point[1]))

            if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
                intensities.append(image[y, x])
            else:
                intensities.append(0)

        if len(intensities) == 0:
            return 0

        if self.measure_type == 'minimum':
            return np.min(intensities)
        elif self.measure_type == 'maximum':
            return np.max(intensities)
        else:  # default to mean
            return np.mean(intensities)

    def get_frame_data(self, frame_index):
        """Get analysis results for specific frame."""
        return (self.intensities.get(frame_index),
                self.measurement_points.get(frame_index),
                self.normal_vectors.get(frame_index))
