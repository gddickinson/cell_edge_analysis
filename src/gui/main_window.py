#!/usr/bin/env python3

import sys
import numpy as np
import cv2
from typing import List, Optional, Dict, Tuple
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ..utils.data_structures import (
    ImageData, EdgeData, CurvatureData, FluorescenceData, AnalysisParameters
)
from ..analysis.edge_detection import EdgeDetector
from ..analysis.curvature_analyzer import CurvatureAnalyzer
from ..analysis.fluorescence_analyzer import FluorescenceAnalyzer
from .analysis_panel import AnalysisPanel
from .visualization_panel import VisualizationPanel
from .file_panel import FilePanel
from .coordinated_analysis import CoordinatedAnalysis

class MainWindow(QMainWindow):
    """Main window for the PIEZO1 analysis application."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PIEZO1 Analysis Tool")

        # Initialize parameters and analysis objects
        self.params = AnalysisParameters()
        self.edge_detector = EdgeDetector(self.params)
        self.curvature_analyzer = CurvatureAnalyzer(self.params)
        self.fluorescence_analyzer = FluorescenceAnalyzer(self.params)

        # Data storage
        self.cell_data = None
        self.fluor_data = None
        self.edge_data = None
        self.curvature_data = None
        self.fluorescence_data = None

        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create horizontal layout for file panel and main content
        h_layout = QHBoxLayout()

        # Create and add file panel
        self.file_panel = FilePanel()
        self.file_panel.cell_mask_loaded.connect(self.on_cell_mask_loaded)
        self.file_panel.fluorescence_loaded.connect(self.on_fluorescence_loaded)
        h_layout.addWidget(self.file_panel)

        # Create vertical layout for main content
        main_content = QWidget()
        main_layout = QVBoxLayout(main_content)

        # Create tab widget for different views
        self.tab_widget = QTabWidget()

        # Create tabs
        self.analysis_view = self._create_analysis_view()
        self.debug_view = self._create_debug_view()

        self.tab_widget.addTab(self.analysis_view, "Analysis")
        self.tab_widget.addTab(self.debug_view, "Debug")

        main_layout.addWidget(self.tab_widget)
        h_layout.addWidget(main_content, stretch=2)  # Give main content more space

        layout.addLayout(h_layout)

        # Create status bar
        self.statusBar().showMessage("Ready")

    def _create_analysis_view(self):
        """Create the main analysis view."""
        view = QWidget()
        layout = QHBoxLayout(view)

        # Left side: Analysis parameters
        self.analysis_panel = AnalysisPanel(self.params)
        self.analysis_panel.parameters_changed.connect(self.update_analysis)
        layout.addWidget(self.analysis_panel)

        # Right side: Visualization
        self.visualization_panel = VisualizationPanel()
        layout.addWidget(self.visualization_panel)

        return view

    def _create_debug_view(self):
        """Create the debug view."""
        view = QWidget()
        layout = QVBoxLayout(view)

        # Add debug output text area
        self.debug_text = QLabel("No analysis run yet")
        self.debug_text.setWordWrap(True)
        layout.addWidget(self.debug_text)

        return view

    def on_cell_mask_loaded(self, image_data: ImageData):
        """Handle loaded cell mask."""
        self.cell_data = image_data
        self.statusBar().showMessage(f"Loaded cell mask: {image_data.filename}")

        # Only run analysis if both files are loaded
        if self.fluor_data is not None:
            self.run_analysis()

    def on_fluorescence_loaded(self, image_data: ImageData):
        """Handle loaded fluorescence image."""
        self.fluor_data = image_data
        self.statusBar().showMessage(f"Loaded fluorescence: {image_data.filename}")

        # Only run analysis if both files are loaded
        if self.cell_data is not None:
            self.run_analysis()

    def run_analysis(self):
        """Run the complete analysis pipeline."""
        if self.cell_data is None or self.fluor_data is None:
            self.statusBar().showMessage("Load both cell mask and fluorescence images to begin analysis")
            return

        try:
            # Detect cell edge
            self.edge_data = self.edge_detector.detect_edge(self.cell_data)
            if self.edge_data is None:
                raise ValueError("Edge detection failed")

            # Create coordinator for sampling points
            coordinator = CoordinatedAnalysis(self.edge_data, self.params)
            sample_indices = coordinator.generate_sampling_points()

            # Lists to store valid measurements
            valid_indices = []
            valid_points = []
            curvature_segments = []
            curvatures = []
            fluorescence_data = []

            # Process each sample point
            for idx in sample_indices:
                if self.fluor_data is not None:
                    # Check point validity for both analyses
                    is_valid, point_data = coordinator.check_point_validity(
                        idx,
                        self.fluor_data.data,
                        self.cell_data.data
                    )

                    if not is_valid:
                        continue

                    # Calculate curvature for valid point
                    segment = coordinator.contour[point_data['segment_indices']]
                    curvature = self.curvature_analyzer._fit_circle_to_segment(segment)

                    if curvature == 0:  # Skip if curvature calculation failed
                        continue

                    # Sample fluorescence
                    rect_mask = np.zeros_like(self.fluor_data.data, dtype=np.uint8)
                    cv2.fillPoly(rect_mask, [point_data['rect_coords']], 1)
                    mask = rect_mask.astype(bool)
                    fluor_values = self.fluor_data.data[mask]

                    if len(fluor_values) == 0:
                        continue

                    # Store valid measurements
                    valid_indices.append(idx)
                    valid_points.append(point_data['center'])
                    curvature_segments.append(point_data['segment_indices'])
                    curvatures.append(curvature)

                    intensity_data = {
                        'mean': np.mean(fluor_values),
                        'min': np.min(fluor_values),
                        'max': np.max(fluor_values),
                        'std': np.std(fluor_values),
                        'rect_coords': point_data['rect_coords'],
                        'raw_values': fluor_values,
                        'normal': point_data['normal'],
                        'center': point_data['center'],
                        'interior_overlap': point_data['interior_overlap']
                    }
                    fluorescence_data.append(intensity_data)

            # Create data objects for valid measurements
            valid_indices = np.array(valid_indices)
            valid_points = np.array(valid_points)

            if len(valid_indices) == 0:
                raise ValueError("No valid measurement points found")

            # Create curvature data
            self.curvature_data = CurvatureData(
                points=valid_points,
                curvatures=np.array(curvatures),
                segment_indices=curvature_segments,
                ref_curvatures=self.curvature_analyzer.ref_curvatures,
                radius_scale=self.params.radius_scale
            )

            # Create fluorescence data if available
            if self.fluor_data is not None:
                self.fluorescence_data = FluorescenceData(
                    sampling_points=fluorescence_data,
                    intensity_values=np.array([d['mean'] for d in fluorescence_data]),
                    sampling_regions=[d['rect_coords'] for d in fluorescence_data],
                    interior_overlaps=[d['interior_overlap'] for d in fluorescence_data]
                )

            # Update visualization
            self.update_visualization()

            # Update debug information
            self.update_debug_info()

            self.statusBar().showMessage(
                f"Analysis complete - {len(valid_indices)} valid measurement points"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Analysis failed: {e}")
            self.statusBar().showMessage("Analysis failed")

    def update_visualization(self):
        """Update all visualization panels."""
        if self.edge_data is None:
            return

        # Update main visualization
        self.visualization_panel.plot_results(
            cell_data=self.cell_data,
            fluor_data=self.fluor_data,
            edge_data=self.edge_data,
            curvature_data=self.curvature_data,
            fluorescence_data=self.fluorescence_data,
            params=self.params
        )

    def update_debug_info(self):
        """Update debug information display."""
        if self.edge_data is None:
            return

        debug_info = []

        # Edge detection debug info
        edge_debug = self.edge_detector.debug_edge_detection(
            self.cell_data,
            self.edge_data
        )
        debug_info.append("Edge Detection:")
        debug_info.extend(f"  {k}: {v}" for k, v in edge_debug.items())

        # Curvature analysis debug info
        if self.curvature_data is not None:
            curv_debug = self.curvature_analyzer.debug_curvature_analysis(
                self.curvature_data
            )
            debug_info.append("\nCurvature Analysis:")
            debug_info.extend(f"  {k}: {v}" for k, v in curv_debug.items())

        # Fluorescence analysis debug info
        if self.fluorescence_data is not None:
            fluor_debug = self.fluorescence_analyzer.debug_fluorescence_analysis(
                self.fluorescence_data
            )
            debug_info.append("\nFluorescence Analysis:")
            debug_info.extend(f"  {k}: {v}" for k, v in fluor_debug.items())

        # Update debug text
        self.debug_text.setText("\n".join(debug_info))

    def update_analysis(self):
        """Update analysis when parameters change."""
        # Get updated parameters from panel
        self.params = self.analysis_panel.get_parameters()

        # Update analyzers with new parameters
        self.edge_detector.params = self.params
        self.curvature_analyzer.params = self.params
        self.fluorescence_analyzer.params = self.params

        # Re-run analysis if we have data
        if self.cell_data is not None:
            self.run_analysis()
