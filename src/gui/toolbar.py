# src/gui/toolbar.py
from PyQt6.QtWidgets import (QToolBar, QPushButton, QSpinBox, QLabel,
                           QDoubleSpinBox, QComboBox)
from PyQt6.QtCore import pyqtSignal

class ToolBar(QToolBar):
    # Signals
    frame_changed = pyqtSignal(int)
    opacity_changed = pyqtSignal(float)
    zoom_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # Navigation controls
        prev_button = QPushButton("Previous Frame")
        prev_button.clicked.connect(self.previous_frame)
        self.addWidget(prev_button)

        self.frame_spinbox = QSpinBox()
        self.frame_spinbox.setMinimum(1)
        self.frame_spinbox.setMaximum(1000)
        self.frame_spinbox.valueChanged.connect(self.frame_changed)
        self.addWidget(self.frame_spinbox)

        next_button = QPushButton("Next Frame")
        next_button.clicked.connect(self.next_frame)
        self.addWidget(next_button)

        self.addSeparator()

        # Overlay controls
        self.addWidget(QLabel("Opacity:"))
        self.opacity_spinbox = QDoubleSpinBox()
        self.opacity_spinbox.setRange(0.0, 1.0)
        self.opacity_spinbox.setSingleStep(0.1)
        self.opacity_spinbox.setValue(0.5)
        self.opacity_spinbox.valueChanged.connect(self.opacity_changed)
        self.addWidget(self.opacity_spinbox)

        self.addSeparator()

        # Zoom controls
        self.addWidget(QLabel("Zoom:"))
        self.zoom_spinbox = QDoubleSpinBox()
        self.zoom_spinbox.setRange(0.1, 5.0)
        self.zoom_spinbox.setSingleStep(0.1)
        self.zoom_spinbox.setValue(1.0)
        self.zoom_spinbox.valueChanged.connect(self.zoom_changed)
        self.addWidget(self.zoom_spinbox)

    def set_frame_range(self, max_frames):
        """Set the maximum number of frames."""
        self.frame_spinbox.setMaximum(max_frames)

    def previous_frame(self):
        """Go to previous frame."""
        current = self.frame_spinbox.value()
        if current > self.frame_spinbox.minimum():
            self.frame_spinbox.setValue(current - 1)

    def next_frame(self):
        """Go to next frame."""
        current = self.frame_spinbox.value()
        if current < self.frame_spinbox.maximum():
            self.frame_spinbox.setValue(current + 1)

