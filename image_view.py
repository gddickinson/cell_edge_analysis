# src/gui/image_view.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea,
                           QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QImage
import numpy as np

class ImageViewer(QWidget):
    # Signals
    mouse_position = pyqtSignal(int, int)  # Emit mouse coordinates

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.zoom_factor = 1.0

    def setup_ui(self):
        self.layout = QVBoxLayout(self)

        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Create image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Ignored,
                                     QSizePolicy.Policy.Ignored)

        self.scroll_area.setWidget(self.image_label)
        self.layout.addWidget(self.scroll_area)

    def update_display(self, pixmap):
        """Update displayed image."""
        if pixmap:
            # Scale pixmap
            scaled_pixmap = pixmap.scaled(
                self.image_label.size() * self.zoom_factor,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def set_zoom(self, factor):
        """Set zoom factor."""
        self.zoom_factor = max(0.1, min(5.0, factor))
        # Update display with current pixmap
        current_pixmap = self.image_label.pixmap()
        if current_pixmap:
            self.update_display(current_pixmap)

    def mouseMoveEvent(self, event):
        """Handle mouse movement."""
        pos = self.image_label.mapFrom(self, event.pos())
        self.mouse_position.emit(pos.x(), pos.y())
        super().mouseMoveEvent(event)

