# src/image_processing/overlay.py
import numpy as np
import cv2
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt

class ImageOverlay:
    def __init__(self):
        self.opacity = 0.5
        self.cell_color = (255, 0, 0)  # Red for cell boundary
        self.piezo_color = (0, 255, 0)  # Green for PIEZO1

    def create_overlay(self, cell_image, piezo_image, edge_image=None, show_vectors=False,
                      measurement_points=None, normal_vectors=None, sampling_depth=None,
                      vector_width=None, show_smoothed=False):
        """Create an overlay with all components."""
        if cell_image is None or piezo_image is None:
            return None

        print(f"Creating overlay. Show smoothed: {show_smoothed}")  # Debug print

        # Create RGB image
        overlay = np.zeros((*cell_image.shape, 3), dtype=np.uint8)

        # Process PIEZO1 signal (green channel)
        piezo_normalized = self._normalize_image(piezo_image)
        piezo_enhanced = cv2.equalizeHist(piezo_normalized)
        overlay[:, :, 1] = piezo_enhanced

        # Process cell boundary (red channel)
        cell_normalized = self._normalize_image(cell_image)
        cell_overlay = np.zeros_like(overlay)
        cell_overlay[cell_normalized > 0] = self.cell_color

        # Add edge lines
        if edge_image is not None:
            print(f"Edge image unique values: {np.unique(edge_image)}")  # Debug print

            # Create separate edge overlays for original and smoothed
            edge_overlay = np.zeros_like(overlay)

            # Original edge (255) in blue
            original_mask = (edge_image == 255)
            edge_overlay[original_mask] = (0, 0, 255)

            # Smoothed edge (128) in red if requested
            smoothed_mask = (edge_image == 128)
            if show_smoothed and np.any(smoothed_mask):
                print("Adding smoothed edge line")  # Debug print
                edge_overlay[smoothed_mask] = (255, 0, 0)

            overlay = cv2.addWeighted(edge_overlay, 1.0, overlay, 1.0, 0)


        # Add sampling vectors if requested
        if (show_vectors and measurement_points is not None and
            normal_vectors is not None and sampling_depth is not None and
            vector_width is not None):

            # Create binary mask for collision detection
            vector_mask = np.zeros_like(cell_image, dtype=bool)

            for point, normal in zip(measurement_points, normal_vectors):
                try:
                    # Start point
                    start = point.astype(np.int32)

                    # Check if start point is valid
                    if (0 <= start[0] < cell_image.shape[1] and
                        0 <= start[1] < cell_image.shape[0]):

                        # Calculate end point
                        end = (point + normal * sampling_depth).astype(np.int32)

                        # Calculate perpendicular vector for width
                        half_width = vector_width / 2
                        perp_vector = np.array([-normal[1], normal[0]]) * half_width

                        # Calculate corner points
                        corners = np.array([
                            start + perp_vector,
                            start - perp_vector,
                            end - perp_vector,
                            end + perp_vector
                        ], dtype=np.int32)

                        # Draw filled rectangle
                        cv2.fillPoly(overlay, [corners], (255, 255, 0))  # Yellow color

                except Exception as e:
                    print(f"Error drawing vector: {e}")
                    continue

        # Blend cell overlay using opacity
        overlay = cv2.addWeighted(cell_overlay, self.opacity, overlay, 1.0, 0)

        return self._array_to_qpixmap(overlay)

    def _normalize_image(self, image):
        """Normalize image to 8-bit range."""
        if image.dtype != np.uint8:
            image = ((image - image.min()) * 255 /
                    (image.max() - image.min())).astype(np.uint8)
        return image

    def _array_to_qpixmap(self, array):
        """Convert numpy array to QPixmap."""
        height, width, channels = array.shape
        bytes_per_line = channels * width

        # Convert to QImage
        q_img = QImage(array.data, width, height, bytes_per_line,
                      QImage.Format.Format_RGB888)

        # Convert to QPixmap
        return QPixmap.fromImage(q_img)

    def set_opacity(self, value):
        """Set overlay opacity (0-1)."""
        self.opacity = max(0.0, min(1.0, value))
