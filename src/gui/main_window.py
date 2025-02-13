#!/usr/bin/env python3
# src/gui/main_window.py

import sys
import numpy as np
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
        self.run_analysis()

    def on_fluorescence_loaded(self, image_data: ImageData):
        """Handle loaded fluorescence image."""
        self.fluor_data = image_data
        self.statusBar().showMessage(f"Loaded fluorescence: {image_data.filename}")
        self.run_analysis()

    def run_analysis(self):
        """Run the complete analysis pipeline."""
        if self.cell_data is None:
            return

        try:
            # Detect cell edge
            self.edge_data = self.edge_detector.detect_edge(self.cell_data)
            if self.edge_data is None:
                raise ValueError("Edge detection failed")

            # If we have fluorescence data, get valid sampling points first
            if self.fluor_data is not None:
                # Get initial fluorescence measurements
                self.fluorescence_data = self.fluorescence_analyzer.calculate_intensities(
                    self.edge_data,
                    self.fluor_data,
                    self.cell_data
                )

                if self.fluorescence_data is None:
                    raise ValueError("Fluorescence analysis failed")

                # Get valid indices from fluorescence analysis
                valid_indices = self.fluorescence_analyzer.get_valid_indices()

                # Calculate curvature using only these valid points
                self.curvature_data = self.curvature_analyzer.calculate_curvature(
                    self.edge_data,
                    valid_indices
                )
            else:
                # If no fluorescence data, just do curvature analysis
                self.curvature_data = self.curvature_analyzer.calculate_curvature(
                    self.edge_data
                )

            # Update visualization
            self.update_visualization()

            # Update debug information
            self.update_debug_info()

            self.statusBar().showMessage("Analysis complete")

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
