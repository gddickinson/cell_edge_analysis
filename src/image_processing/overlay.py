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

    def create_overlay(self, cell_image, piezo_image, edge_image=None):
        """
        Create an overlay of cell boundary, PIEZO1 images, and detected edges.

        Args:
            cell_image (np.ndarray): Binary cell image
            piezo_image (np.ndarray): PIEZO1 fluorescence image
            edge_image (np.ndarray, optional): Detected edge image

        Returns:
            QPixmap: Overlay image for display
        """
        if cell_image is None or piezo_image is None:
            return None

        # Create RGB image
        overlay = np.zeros((*cell_image.shape, 3), dtype=np.uint8)

        # Process PIEZO1 signal (green channel)
        piezo_normalized = self._normalize_image(piezo_image)
        # Enhance contrast for better visibility of puncta
        piezo_enhanced = cv2.equalizeHist(piezo_normalized)
        overlay[:, :, 1] = piezo_enhanced

        # Process cell boundary (red channel)
        cell_normalized = self._normalize_image(cell_image)
        # Create semi-transparent cell overlay
        cell_overlay = np.zeros_like(overlay)
        cell_overlay[cell_normalized > 0] = self.cell_color

        # Add detected edges if available (in blue)
        if edge_image is not None:
            edge_overlay = np.zeros_like(overlay)
            edge_overlay[edge_image > 0] = (0, 0, 255)  # Blue color for edges
            overlay = cv2.addWeighted(edge_overlay, 1.0, overlay, 1.0, 0)

        # Blend cell overlay using opacity
        overlay = cv2.addWeighted(cell_overlay, self.opacity, overlay, 1.0, 0)

        # Convert to QPixmap
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

    def set_cell_color(self, color):
        """Set cell boundary color (RGB tuple)."""
        self.cell_color = color

    def set_piezo_color(self, color):
        """Set PIEZO1 signal color (RGB tuple)."""
        self.piezo_color = color
