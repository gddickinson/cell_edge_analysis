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

        Args:
            binary_image (np.ndarray): Binary segmentation image
            frame_index (int): Current frame index

        Returns:
            tuple: (edge_image, contour)
        """
        try:
            # Print debug information
            print(f"Frame {frame_index} input shape: {binary_image.shape}")
            print(f"Frame {frame_index} input dtype: {binary_image.dtype}")

            # Ensure binary image and make contiguous in memory
            binary = np.ascontiguousarray(binary_image > 0, dtype=np.uint8)

            # Clean up binary image
            cleaned = morphology.remove_small_objects(binary > 0, min_size=100)
            cleaned = np.ascontiguousarray(cleaned, dtype=np.uint8)

            # Correct orientation: rotate 90 degrees clockwise, flip left-right and up-down
            #cleaned = np.ascontiguousarray(np.flipud(np.fliplr(np.rot90(cleaned, k=-1))))

            # Create edge image with same shape as cleaned image
            edge_image = np.zeros(cleaned.shape, dtype=np.uint8)
            edge_image = np.ascontiguousarray(edge_image)

            print(f"Frame {frame_index} cleaned shape: {cleaned.shape}")
            print(f"Frame {frame_index} edge image shape: {edge_image.shape}")

            # Find contours using OpenCV
            contours, _ = cv2.findContours(cleaned.copy(),
                                         cv2.RETR_EXTERNAL,
                                         cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                # Get the longest contour
                contour = max(contours, key=cv2.contourArea)

                # Create a fresh image for contour drawing
                temp_image = np.zeros_like(cleaned, dtype=np.uint8)

                # Draw contour on temporary image
                try:
                    temp_image = cv2.drawContours(temp_image,
                                                [contour],
                                                -1,
                                                (255),
                                                2)
                except Exception as draw_error:
                    print(f"Error drawing contour in frame {frame_index}: {draw_error}")
                    print(f"Contour shape: {contour.shape}")
                    return edge_image, None

                # Store the results for this frame
                self.edges[frame_index] = temp_image
                self.contours[frame_index] = contour
                self.edge_images[frame_index] = temp_image

                return temp_image, contour

            return edge_image, None

        except Exception as e:
            print(f"Error in detect_edges for frame {frame_index}: {e}")
            print(f"Stack trace:", np.format_exception())
            return np.zeros_like(binary_image, dtype=np.uint8), None

    def detect_edges_stack(self, binary_stack):
        """
        Detect edges in entire binary image stack.

        Args:
            binary_stack (np.ndarray): Stack of binary images

        Returns:
            bool: Success status
        """
        try:
            # Print stack information
            print(f"Stack shape: {binary_stack.shape}")
            print(f"Stack dtype: {binary_stack.dtype}")

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
        """
        Get edge image for specific frame.

        Args:
            frame_index (int): Frame index

        Returns:
            np.ndarray: Edge image for frame
        """
        edge_image = self.edge_images.get(frame_index)
        if edge_image is None:
            return None
        return np.ascontiguousarray(edge_image.copy())  # Return a contiguous copy

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


