# src/analysis/edge_detection.py
import numpy as np
import cv2
from skimage import measure, morphology

class EdgeDetector:
    def __init__(self):
        self.edges = {}  # Dictionary to store edges for each frame
        self.contours = {}  # Dictionary to store contours for each frame
        self.edge_images = {}  # Dictionary to store edge images for each frame

    def detect_edges(self, binary_image, frame_index=0):
        """
        Detect edges in binary cell segmentation image.
        """
        try:
            # Ensure binary image
            binary = (binary_image > 0).astype(np.uint8)

            # Clean up binary image
            cleaned = morphology.remove_small_objects(binary > 0, min_size=100)
            cleaned = cleaned.astype(np.uint8)

            # Find contours using OpenCV for better compatibility
            contours, hierarchy = cv2.findContours(
                cleaned,
                cv2.RETR_EXTERNAL,  # Only get external contours
                cv2.CHAIN_APPROX_NONE  # Get all contour points
            )

            if contours:
                # Get the largest contour by area
                largest_contour = max(contours, key=cv2.contourArea)

                # Create edge image
                edge_image = np.zeros_like(binary, dtype=np.uint8)

                # Draw contour
                cv2.drawContours(edge_image, [largest_contour], -1, 255, 2)

                # Convert contour to the format used by skimage for consistency
                contour_points = largest_contour.squeeze()

                # Store results
                self.edges[frame_index] = edge_image
                self.contours[frame_index] = contour_points
                self.edge_images[frame_index] = edge_image

                return edge_image, contour_points

            return np.zeros_like(binary_image, dtype=np.uint8), None

        except Exception as e:
            print(f"Error in detect_edges for frame {frame_index}: {e}")
            return np.zeros_like(binary_image, dtype=np.uint8), None

    def detect_edges_stack(self, binary_stack):
        """
        Detect edges in entire binary image stack.
        """
        try:
            # Clear previous results
            self.edges.clear()
            self.contours.clear()
            self.edge_images.clear()

            # Process each frame
            for i in range(len(binary_stack)):
                self.detect_edges(binary_stack[i], i)

            return True

        except Exception as e:
            print(f"Error detecting edges in stack: {e}")
            return False

    def get_edge_image(self, frame_index):
        """Get edge image for specific frame."""
        return self.edge_images.get(frame_index)

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


