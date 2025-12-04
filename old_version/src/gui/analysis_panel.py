#!/usr/bin/env python3
# src/gui/analysis_panel.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSlider, QPushButton, QDoubleSpinBox,
    QComboBox
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
        layout = QVBoxLayout()

        # Pixel size control with decimal support
        pixel_size_layout = QHBoxLayout()
        self.pixel_size_label = QLabel("Pixel Size (nm):")
        self.pixel_size_input = QDoubleSpinBox()  # Changed to QDoubleSpinBox
        self.pixel_size_input.setMinimum(0.1)
        self.pixel_size_input.setMaximum(1000.0)
        self.pixel_size_input.setDecimals(1)  # Show one decimal place
        self.pixel_size_input.setSingleStep(0.1)  # Allow fine adjustments
        self.pixel_size_input.setValue(float(self.params.pixel_size))
        self.pixel_size_input.valueChanged.connect(self._on_pixel_size_changed)
        pixel_size_layout.addWidget(self.pixel_size_label)
        pixel_size_layout.addWidget(self.pixel_size_input)
        layout.addLayout(pixel_size_layout)

        # Number of samples slider
        self.samples_label = QLabel(f"Number of Samples: {self.params.n_samples}")
        self.samples_slider = QSlider(Qt.Orientation.Horizontal)
        self.samples_slider.setMinimum(10)
        self.samples_slider.setMaximum(3000)
        self.samples_slider.setValue(self.params.n_samples)
        self.samples_slider.valueChanged.connect(self._on_samples_changed)
        layout.addWidget(self.samples_label)
        layout.addWidget(self.samples_slider)

        # Edge smoothing slider
        self.smoothing_label = QLabel(f"Edge Smoothing σ: {self.params.smoothing_sigma:.1f}")
        self.smoothing_slider = QSlider(Qt.Orientation.Horizontal)
        self.smoothing_slider.setMinimum(0)
        self.smoothing_slider.setMaximum(500)
        self.smoothing_slider.setValue(int(self.params.smoothing_sigma * 10))
        self.smoothing_slider.valueChanged.connect(self._on_smoothing_changed)
        layout.addWidget(self.smoothing_label)
        layout.addWidget(self.smoothing_slider)

        group.setLayout(layout)
        return group

    def _on_pixel_size_changed(self, value):
        """Update pixel size parameter."""
        self.params.pixel_size = float(value)  # Ensure float conversion
        self.parameters_changed.emit()

    def _create_curvature_group(self) -> QGroupBox:
        """Create group for curvature analysis parameters."""
        group = QGroupBox("Curvature Analysis")
        layout = QVBoxLayout(group)

        # Method selection
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItem("Sample Points")
        self.method_combo.addItem("Moving Window")
        self.method_combo.addItem("Spline Fitting")
        self.method_combo.addItem("Geometric Classification")  # Jinghao's method


        # Set current selection based on parameter
        if self.params.curvature_method == "sample_points":
            current_index = 0
        elif self.params.curvature_method == "moving_window":
            current_index = 1
        elif self.params.curvature_method == "spline_fitting":
            current_index = 2
        elif self.params.curvature_method == "geometric":
            current_index = 3
        else:
            current_index = 0

        self.method_combo.setCurrentIndex(current_index)
        self.method_combo.currentIndexChanged.connect(self._on_method_changed)
        method_layout.addWidget(self.method_combo)
        layout.addLayout(method_layout)

        # Segment length slider
        self.segment_label = QLabel(f"Segment Length: {self.params.segment_length}")
        self.segment_slider = QSlider(Qt.Orientation.Horizontal)
        self.segment_slider.setMinimum(5)
        self.segment_slider.setMaximum(500)
        self.segment_slider.setValue(self.params.segment_length)
        self.segment_slider.valueChanged.connect(self._on_segment_changed)
        layout.addWidget(self.segment_label)
        layout.addWidget(self.segment_slider)

        # Window step slider (for moving window only)
        self.window_step_label = QLabel(f"Window Step: {self.params.window_step}")
        self.window_step_slider = QSlider(Qt.Orientation.Horizontal)
        self.window_step_slider.setMinimum(1)
        self.window_step_slider.setMaximum(10)
        self.window_step_slider.setValue(self.params.window_step)
        self.window_step_slider.valueChanged.connect(self._on_window_step_changed)
        layout.addWidget(self.window_step_label)
        layout.addWidget(self.window_step_slider)

        # Spline smoothing slider (for spline fitting only)
        self.spline_smoothing_label = QLabel(f"Spline Smoothing: {self.params.spline_smoothing:.1f}")
        self.spline_smoothing_slider = QSlider(Qt.Orientation.Horizontal)
        self.spline_smoothing_slider.setMinimum(0)
        self.spline_smoothing_slider.setMaximum(100)
        self.spline_smoothing_slider.setValue(int(self.params.spline_smoothing * 10))
        self.spline_smoothing_slider.valueChanged.connect(self._on_spline_smoothing_changed)
        layout.addWidget(self.spline_smoothing_label)
        layout.addWidget(self.spline_smoothing_slider)

        # Show/hide method-specific controls
        self._update_curvature_controls_visibility()

        return group

    def _create_fluorescence_group(self) -> QGroupBox:
        """Create group for fluorescence analysis parameters."""
        group = QGroupBox("Fluorescence Analysis")
        layout = QVBoxLayout(group)

        # Vector width slider
        self.width_label = QLabel(f"Vector Width: {self.params.vector_width} px")
        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setMinimum(1)
        self.width_slider.setMaximum(100)
        self.width_slider.setValue(self.params.vector_width)
        self.width_slider.valueChanged.connect(self._on_width_changed)
        layout.addWidget(self.width_label)
        layout.addWidget(self.width_slider)

        # Vector depth slider
        self.depth_label = QLabel(f"Vector Depth: {self.params.vector_depth} px")
        self.depth_slider = QSlider(Qt.Orientation.Horizontal)
        self.depth_slider.setMinimum(5)
        self.depth_slider.setMaximum(200)
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

        # Show fitted circles toggle
        self.show_circles_button = QPushButton("Show Fitted Circles")
        self.show_circles_button.setCheckable(True)
        self.show_circles_button.setChecked(self.params.show_fitted_circles)
        self.show_circles_button.clicked.connect(self._on_show_circles_toggled)
        layout.addWidget(self.show_circles_button)

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
        # Make sure this triggers recalculation
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

    def _on_show_circles_toggled(self, checked):
        self.params.show_fitted_circles = checked
        self.parameters_changed.emit()

    def _on_method_changed(self, index):
        """Update curvature method parameter."""
        if index == 0:
            self.params.curvature_method = "sample_points"
        elif index == 1:
            self.params.curvature_method = "moving_window"
        elif index == 2:
            self.params.curvature_method = "spline_fitting"
        elif index == 3:
            self.params.curvature_method = "geometric"
        else:
            self.params.curvature_method = "sample_points"

        # Update control visibility
        self._update_curvature_controls_visibility()

        self.parameters_changed.emit()

    def _on_window_step_changed(self, value):
        """Update window step parameter."""
        self.params.window_step = value
        self.window_step_label.setText(f"Window Step: {value}")
        self.parameters_changed.emit()

    def _on_spline_smoothing_changed(self, value):
        """Update spline smoothing parameter."""
        self.params.spline_smoothing = value / 10.0
        self.spline_smoothing_label.setText(f"Spline Smoothing: {self.params.spline_smoothing:.1f}")
        self.parameters_changed.emit()

    def _update_curvature_controls_visibility(self):
        """Show/hide method-specific controls based on selected method."""
        is_moving_window = self.params.curvature_method == "moving_window"
        is_spline_fitting = self.params.curvature_method == "spline_fitting"

        # Moving window specific controls
        self.window_step_label.setVisible(is_moving_window)
        self.window_step_slider.setVisible(is_moving_window)

        # Spline fitting specific controls
        self.spline_smoothing_label.setVisible(is_spline_fitting)
        self.spline_smoothing_slider.setVisible(is_spline_fitting)
