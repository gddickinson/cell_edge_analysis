#!/usr/bin/env python3
# src/gui/analysis_panel.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSlider, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from ..utils.data_structures import AnalysisParameters

class AnalysisPanel(QWidget):
    """Panel for controlling analysis parameters."""
    
    # Signal emitted when parameters change
    parameters_changed = pyqtSignal()
    
    def __init__(self, params: AnalysisParameters):
        super().__init__()
        self.params = params
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Create parameter groups
        layout.addWidget(self._create_common_group())
        layout.addWidget(self._create_curvature_group())
        layout.addWidget(self._create_fluorescence_group())
        layout.addWidget(self._create_visualization_group())
        
        # Add stretch at the bottom
        layout.addStretch()
        
    def _create_common_group(self) -> QGroupBox:
        """Create group for common parameters."""
        group = QGroupBox("Common Parameters")
        layout = QVBoxLayout(group)
        
        # Number of samples slider
        self.samples_label = QLabel(f"Number of Samples: {self.params.n_samples}")
        self.samples_slider = QSlider(Qt.Orientation.Horizontal)
        self.samples_slider.setMinimum(20)
        self.samples_slider.setMaximum(150)
        self.samples_slider.setValue(self.params.n_samples)
        self.samples_slider.valueChanged.connect(self._on_samples_changed)
        layout.addWidget(self.samples_label)
        layout.addWidget(self.samples_slider)
        
        # Edge smoothing slider
        self.smoothing_label = QLabel(f"Edge Smoothing σ: {self.params.smoothing_sigma:.1f}")
        self.smoothing_slider = QSlider(Qt.Orientation.Horizontal)
        self.smoothing_slider.setMinimum(0)
        self.smoothing_slider.setMaximum(50)
        self.smoothing_slider.setValue(int(self.params.smoothing_sigma * 10))
        self.smoothing_slider.valueChanged.connect(self._on_smoothing_changed)
        layout.addWidget(self.smoothing_label)
        layout.addWidget(self.smoothing_slider)
        
        return group
        
    def _create_curvature_group(self) -> QGroupBox:
        """Create group for curvature analysis parameters."""
        group = QGroupBox("Curvature Analysis")
        layout = QVBoxLayout(group)
        
        # Segment length slider
        self.segment_label = QLabel(f"Segment Length: {self.params.segment_length}")
        self.segment_slider = QSlider(Qt.Orientation.Horizontal)
        self.segment_slider.setMinimum(5)
        self.segment_slider.setMaximum(20)
        self.segment_slider.setValue(self.params.segment_length)
        self.segment_slider.valueChanged.connect(self._on_segment_changed)
        layout.addWidget(self.segment_label)
        layout.addWidget(self.segment_slider)
        
        return group
        
    def _create_fluorescence_group(self) -> QGroupBox:
        """Create group for fluorescence analysis parameters."""
        group = QGroupBox("Fluorescence Analysis")
        layout = QVBoxLayout(group)
        
        # Vector width slider
        self.width_label = QLabel(f"Vector Width: {self.params.vector_width} px")
        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setMinimum(1)
        self.width_slider.setMaximum(20)
        self.width_slider.setValue(self.params.vector_width)
        self.width_slider.valueChanged.connect(self._on_width_changed)
        layout.addWidget(self.width_label)
        layout.addWidget(self.width_slider)
        
        # Vector depth slider
        self.depth_label = QLabel(f"Vector Depth: {self.params.vector_depth} px")
        self.depth_slider = QSlider(Qt.Orientation.Horizontal)
        self.depth_slider.setMinimum(5)
        self.depth_slider.setMaximum(50)
        self.depth_slider.setValue(self.params.vector_depth)
        self.depth_slider.valueChanged.connect(self._on_depth_changed)
        layout.addWidget(self.depth_label)
        layout.addWidget(self.depth_slider)
        
        # Interior threshold slider
        self.interior_label = QLabel(f"Interior Threshold: {self.params.interior_threshold}%")
        self.interior_slider = QSlider(Qt.Orientation.Horizontal)
        self.interior_slider.setMinimum(0)
        self.interior_slider.setMaximum(100)
        self.interior_slider.setValue(self.params.interior_threshold)
        self.interior_slider.valueChanged.connect(self._on_interior_changed)
        layout.addWidget(self.interior_label)
        layout.addWidget(self.interior_slider)
        
        return group
        
    def _create_visualization_group(self) -> QGroupBox:
        """Create group for visualization parameters."""
        group = QGroupBox("Visualization")
        layout = QVBoxLayout(group)
        
        # Line width slider
        self.line_width_label = QLabel(f"Line Width: {self.params.line_width}")
        self.line_width_slider = QSlider(Qt.Orientation.Horizontal)
        self.line_width_slider.setMinimum(1)
        self.line_width_slider.setMaximum(10)
        self.line_width_slider.setValue(self.params.line_width)
        self.line_width_slider.valueChanged.connect(self._on_line_width_changed)
        layout.addWidget(self.line_width_label)
        layout.addWidget(self.line_width_slider)
        
        # Background opacity slider
        self.bg_opacity_label = QLabel(f"Background Opacity: {self.params.background_alpha:.1f}")
        self.bg_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.bg_opacity_slider.setMinimum(0)
        self.bg_opacity_slider.setMaximum(100)
        self.bg_opacity_slider.setValue(int(self.params.background_alpha * 100))
        self.bg_opacity_slider.valueChanged.connect(self._on_bg_opacity_changed)
        layout.addWidget(self.bg_opacity_label)
        layout.addWidget(self.bg_opacity_slider)
        
        # Rectangle opacity slider
        self.rect_opacity_label = QLabel(f"Rectangle Opacity: {self.params.rectangle_alpha:.1f}")
        self.rect_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.rect_opacity_slider.setMinimum(0)
        self.rect_opacity_slider.setMaximum(100)
        self.rect_opacity_slider.setValue(int(self.params.rectangle_alpha * 100))
        self.rect_opacity_slider.valueChanged.connect(self._on_rect_opacity_changed)
        layout.addWidget(self.rect_opacity_label)
        layout.addWidget(self.rect_opacity_slider)
        
        # Edge visibility toggle
        self.show_edge_button = QPushButton("Toggle Cell Edge")
        self.show_edge_button.setCheckable(True)
        self.show_edge_button.setChecked(self.params.show_edge)
        self.show_edge_button.clicked.connect(self._on_show_edge_toggled)
        layout.addWidget(self.show_edge_button)
        
        return group
    
    # Parameter update handlers
    def _on_samples_changed(self, value):
        self.params.n_samples = value
        self.samples_label.setText(f"Number of Samples: {value}")
        self.parameters_changed.emit()
        
    def _on_smoothing_changed(self, value):
        self.params.smoothing_sigma = value / 10
        self.smoothing_label.setText(f"Edge Smoothing σ: {self.params.smoothing_sigma:.1f}")
        self.parameters_changed.emit()
        
    def _on_segment_changed(self, value):
        self.params.segment_length = value
        self.segment_label.setText(f"Segment Length: {value}")
        self.parameters_changed.emit()
        
    def _on_width_changed(self, value):
        self.params.vector_width = value
        self.width_label.setText(f"Vector Width: {value} px")
        self.parameters_changed.emit()
        
    def _on_depth_changed(self, value):
        self.params.vector_depth = value
        self.depth_label.setText(f"Vector Depth: {value} px")
        self.parameters_changed.emit()
        
    def _on_interior_changed(self, value):
        self.params.interior_threshold = value
        self.interior_label.setText(f"Interior Threshold: {value}%")
        self.parameters_changed.emit()
        
    def _on_line_width_changed(self, value):
        self.params.line_width = value
        self.line_width_label.setText(f"Line Width: {value}")
        self.parameters_changed.emit()
        
    def _on_bg_opacity_changed(self, value):
        self.params.background_alpha = value / 100
        self.bg_opacity_label.setText(f"Background Opacity: {self.params.background_alpha:.1f}")
        self.parameters_changed.emit()
        
    def _on_rect_opacity_changed(self, value):
        self.params.rectangle_alpha = value / 100
        self.rect_opacity_label.setText(f"Rectangle Opacity: {self.params.rectangle_alpha:.1f}")
        self.parameters_changed.emit()
        
    def _on_show_edge_toggled(self, checked):
        self.params.show_edge = checked
        self.parameters_changed.emit()
        
    def get_parameters(self) -> AnalysisParameters:
        """Get current parameter values."""
        return self.params