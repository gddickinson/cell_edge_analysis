# src/analysis/edge_detection.py
import numpy as np
import cv2
from skimage import measure, morphology
from scipy.signal import savgol_filter

class EdgeDetector:
    def __init__(self):
        self.edges = {}
        self.contours = {}
        self.edge_images = {}
        self.smoothed_contours = {}
        self.smoothing_window = 0

    def smooth_contour(self, contour, window_size):
        """
        Smooth a contour using Savitzky-Golay filter.
        """
        if window_size < 3:
            return contour

        # Ensure window size is odd
        window_size = window_size + 1 if window_size % 2 == 0 else window_size

        # Calculate appropriate polynomial order (must be less than window_size)
        poly_order = min(3, window_size - 1)

        try:
            # Pad the contour for periodic boundary conditions
            pad_size = window_size // 2
            padded_x = np.pad(contour[:, 0], (pad_size, pad_size), mode='wrap')
            padded_y = np.pad(contour[:, 1], (pad_size, pad_size), mode='wrap')

            # Apply Savitzky-Golay filter
            smoothed_x = savgol_filter(padded_x, window_size, poly_order)
            smoothed_y = savgol_filter(padded_y, window_size, poly_order)

            # Remove padding
            smoothed_x = smoothed_x[pad_size:-pad_size]
            smoothed_y = smoothed_y[pad_size:-pad_size]

            return np.column_stack((smoothed_x, smoothed_y))

        except Exception as e:
            print(f"Error in smooth_contour: {e}")
            return contour

    def get_contour(self, frame_index):
        """
        Get the appropriate contour (smoothed or original) for a frame.

        Args:
            frame_index (int): Frame number

        Returns:
            np.ndarray: Contour points
        """
        if self.smoothing_window > 0:
            # Return smoothed contour if available
            smoothed = self.smoothed_contours.get(frame_index)
            if smoothed is not None:
                print(f"Using smoothed contour for frame {frame_index}")  # Debug print
                return smoothed

        # Return original contour if no smoothed contour available
        return self.contours.get(frame_index)

    def get_edge_image(self, frame_index, *, show_smoothed=False):
        """
        Get edge image with optional smoothed contour.

        Args:
            frame_index (int): Frame number
            show_smoothed (bool, optional): Whether to show smoothed contour

        Returns:
            np.ndarray: Edge image with original and optionally smoothed contours
        """
        # Create edge image
        if frame_index in self.contours:
            edge_image = np.zeros_like(self.edges[frame_index], dtype=np.uint8)

            # Draw original contour in blue (255)
            contour = self.contours[frame_index]
            if contour is not None:
                contour_cv2 = contour.reshape((-1, 1, 2)).astype(np.int32)
                cv2.drawContours(edge_image, [contour_cv2], -1, 255, 2)

            # Draw smoothed contour in half-intensity (128) if requested
            if show_smoothed and self.smoothing_window > 0:
                smoothed = self.smoothed_contours.get(frame_index)
                if smoothed is not None:
                    smoothed_cv2 = smoothed.reshape((-1, 1, 2)).astype(np.int32)
                    cv2.drawContours(edge_image, [smoothed_cv2], -1, 128, 2)
                    print(f"Drew smoothed contour for frame {frame_index}")  # Debug print

            return edge_image
        return None

    def set_smoothing(self, window_size):
        """Set smoothing window size and update smoothed contours."""
        print(f"Setting smoothing window size to: {window_size}")  # Debug print
        self.smoothing_window = window_size

        # Update all existing contours
        for frame_index in self.contours.keys():
            self.update_smoothed_contour(frame_index)

    def update_smoothed_contour(self, frame_index):
        """Update smoothed contour for a specific frame."""
        contour = self.contours.get(frame_index)
        if contour is not None:
            if self.smoothing_window > 0:
                smoothed = self.smooth_contour(contour, self.smoothing_window)
                self.smoothed_contours[frame_index] = smoothed
                print(f"Updated smoothed contour for frame {frame_index}")  # Debug print
            else:
                self.smoothed_contours[frame_index] = contour

    def detect_edges(self, binary_image, frame_index=0):
        """Detect edges in binary cell segmentation image."""
        try:
            # Ensure binary image
            binary = (binary_image > 0).astype(np.uint8)

            # Clean up binary image
            cleaned = morphology.remove_small_objects(binary > 0, min_size=100)
            cleaned = cleaned.astype(np.uint8)

            # Find contours using OpenCV
            contours, hierarchy = cv2.findContours(
                cleaned,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_NONE
            )

            if contours:
                # Get the largest contour
                largest_contour = max(contours, key=cv2.contourArea)

                # Convert to array of points
                contour_points = largest_contour.squeeze()

                # Store original contour
                self.contours[frame_index] = contour_points
                self.edges[frame_index] = np.zeros_like(binary, dtype=np.uint8)

                # Update smoothed contour
                self.update_smoothed_contour(frame_index)

                # Get edge image with both contours
                edge_image = self.get_edge_image(frame_index)

                return edge_image, contour_points

            return np.zeros_like(binary_image, dtype=np.uint8), None

        except Exception as e:
            print(f"Error in detect_edges for frame {frame_index}: {e}")
            return np.zeros_like(binary_image, dtype=np.uint8), None

    def detect_edges_stack(self, binary_stack):
        """Detect edges in entire binary image stack."""
        try:
            # Clear previous results
            self.edges.clear()
            self.contours.clear()
            self.edge_images.clear()
            self.smoothed_contours.clear()

            # Process each frame
            for i in range(len(binary_stack)):
                self.detect_edges(binary_stack[i], i)

            return True

        except Exception as e:
            print(f"Error detecting edges in stack: {e}")
            return False



    def get_edge_mask(self, shape, distance_px):
        """
        Create a mask for the region around detected edges.

        Args:
            shape (tuple): Shape of the original image
            distance_px (int): Distance in pixels to include in mask

        Returns:
            np.ndarray: Binary mask of edge region
        """
        if self.edges is None:
            return None

        # Dilate edges to create region
        kernel = np.ones((distance_px * 2 + 1, distance_px * 2 + 1), np.uint8)
        edge_region = cv2.dilate(self.edges, kernel, iterations=1)

        return edge_region


