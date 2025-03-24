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
import traceback

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

        # Create and add file panel with analyzers and parameters
        self.file_panel = FilePanel(
            edge_detector=self.edge_detector,
            curvature_analyzer=self.curvature_analyzer,
            fluorescence_analyzer=self.fluorescence_analyzer,
            params=self.params,
            parent=self
        )

        # Connect file panel signals
        self.file_panel.cell_mask_loaded.connect(self.on_cell_mask_loaded)
        self.file_panel.fluorescence_loaded.connect(self.on_fluorescence_loaded)
        self.file_panel.files_ready.connect(self.run_analysis)


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

            if self.params.curvature_method == "moving_window":
                # ===== MOVING WINDOW IMPLEMENTATION =====
                # Get the contour
                contour = self.edge_data.smoothed_contour if self.edge_data.smoothed_contour is not None else self.edge_data.contour
                n_points = len(contour)

                # Parameters
                half_segment = self.params.segment_length // 2
                step = max(1, self.params.window_step)

                # Arrays to store results
                valid_points = []
                valid_indices = []  # Add this to store indices
                curvatures = []
                segment_indices = []

                # For fluorescence
                fluorescence_data = []
                intensity_values = []
                sampling_regions = []
                interior_overlaps = []

                # Slide window along contour
                for i in range(0, n_points, step):
                    try:
                        # 1. Calculate curvature
                        # Create segment indices centered at current point
                        curve_indices = np.arange(i - half_segment, i + half_segment + 1) % n_points
                        segment = contour[curve_indices]

                        if len(segment) < 3:
                            continue

                        curvature = self.curvature_analyzer._fit_circle_to_segment(segment)

                        if curvature == 0:  # Skip if invalid curvature
                            continue

                        # 2. Calculate fluorescence (only if curvature is valid)
                        # Create normal vector for fluorescence sampling
                        # Use edge_segment for normal calculation (more stable)
                        norm_half_segment = self.params.edge_segment // 2
                        norm_indices = np.arange(i - norm_half_segment, i + norm_half_segment + 1) % n_points
                        norm_segment = contour[norm_indices]

                        # Calculate normal
                        tangent = norm_segment[-1] - norm_segment[0]
                        normal = np.array([-tangent[1], tangent[0]])
                        norm = np.linalg.norm(normal)
                        if norm < 1e-10:
                            continue
                        normal = normal / norm

                        # Check if normal points into the cell
                        point = contour[i]  # Current point
                        test_point = point + normal * 5
                        test_x, test_y = test_point.astype(int)

                        # Check bounds
                        if not (0 <= test_x < self.cell_data.data.shape[1] and
                                0 <= test_y < self.cell_data.data.shape[0]):
                            continue

                        # Ensure normal points inward
                        if self.cell_data.data[test_y, test_x] == 0:
                            normal = -normal

                        # Create sampling rectangle
                        perpendicular = np.array([-normal[1], normal[0]])
                        center = point + (normal * self.params.vector_depth / 2)
                        half_width = self.params.vector_width / 2
                        half_depth = self.params.vector_depth / 2

                        rect_points = np.array([
                            center - perpendicular * half_width - normal * half_depth,
                            center + perpendicular * half_width - normal * half_depth,
                            center + perpendicular * half_width + normal * half_depth,
                            center - perpendicular * half_width + normal * half_depth
                        ])

                        rect_coords = rect_points.astype(int)

                        # Check rectangle bounds
                        if (np.any(rect_coords[:, 0] < 0) or
                            np.any(rect_coords[:, 0] >= self.fluor_data.data.shape[1]) or
                            np.any(rect_coords[:, 1] < 0) or
                            np.any(rect_coords[:, 1] >= self.fluor_data.data.shape[0])):
                            continue

                        # Create mask and sample
                        rect_mask = np.zeros_like(self.fluor_data.data, dtype=np.uint8)
                        cv2.fillPoly(rect_mask, [rect_coords], 1)

                        # Check interior overlap
                        interior_overlap = (np.sum(rect_mask & (self.cell_data.data > 0)) /
                                          np.sum(rect_mask) * 100)

                        if interior_overlap < self.params.interior_threshold:
                            continue

                        # Sample fluorescence values
                        mask = rect_mask.astype(bool)
                        fluor_values = self.fluor_data.data[mask]

                        if len(fluor_values) == 0:
                            continue

                        # Store valid point for both curvature and fluorescence
                        valid_points.append(point)
                        valid_indices.append(i)  # Store the index
                        curvatures.append(curvature)
                        segment_indices.append(curve_indices.tolist())

                        # Create and store fluorescence data
                        intensity_data = {
                            'mean': np.mean(fluor_values),
                            'min': np.min(fluor_values),
                            'max': np.max(fluor_values),
                            'std': np.std(fluor_values),
                            'rect_coords': rect_coords,
                            'raw_values': fluor_values,
                            'normal': normal,
                            'center': point,
                            'interior_overlap': interior_overlap
                        }

                        fluorescence_data.append(intensity_data)
                        intensity_values.append(np.mean(fluor_values))
                        sampling_regions.append(rect_coords)
                        interior_overlaps.append(interior_overlap)

                    except Exception as e:
                        print(f"Error processing point {i}: {e}")
                        continue

                # Check if we have valid data
                if not curvatures:
                    raise ValueError("No valid measurements found")

                # Store valid indices in curvature analyzer for debug info
                self.curvature_analyzer.valid_indices = np.array(valid_indices)

                # Create data objects
                self.curvature_data = CurvatureData(
                    points=np.array(valid_points),
                    curvatures=np.array(curvatures),
                    segment_indices=segment_indices,
                    ref_curvatures=self.curvature_analyzer.ref_curvatures,
                    radius_scale=self.params.radius_scale
                )

                self.fluorescence_data = FluorescenceData(
                    sampling_points=fluorescence_data,
                    intensity_values=np.array(intensity_values),
                    sampling_regions=sampling_regions,
                    interior_overlaps=interior_overlaps
                )



            elif self.params.curvature_method == "spline_fitting":
                # Spline fitting method using a combined approach (similar to moving window)
                # Get the contour
                contour = self.edge_data.smoothed_contour if self.edge_data.smoothed_contour is not None else self.edge_data.contour
                n_points = len(contour)

                # Create spline fit of the contour
                try:
                    from scipy.interpolate import splprep, splev

                    # Extract x and y coordinates
                    x = contour[:, 0]
                    y = contour[:, 1]

                    # Create periodic parameter for the points
                    t = np.linspace(0, 1, n_points)

                    # Fit a periodic spline to the contour
                    smoothing = self.params.spline_smoothing
                    tck, u = splprep([x, y], u=t, s=smoothing, per=1)

                    # Sample points from the spline at regular intervals
                    num_samples = min(self.params.n_samples, n_points)
                    step = max(1, n_points // num_samples)
                    sample_indices = np.arange(0, n_points, step)

                    u_samples = t[sample_indices]

                    # Evaluate the spline and its derivatives
                    spline_points = np.array(splev(u_samples, tck, der=0)).T
                    spline_1st_deriv = np.array(splev(u_samples, tck, der=1)).T
                    spline_2nd_deriv = np.array(splev(u_samples, tck, der=2)).T

                    # Arrays to store results
                    valid_points = []
                    valid_indices = []  # Initialize valid_indices list
                    curvatures = []
                    segment_indices = []

                    # For fluorescence
                    fluorescence_data = []
                    intensity_values = []
                    sampling_regions = []
                    interior_overlaps = []

                    # Process each spline point
                    for i, (point, d1, d2) in enumerate(zip(spline_points, spline_1st_deriv, spline_2nd_deriv)):
                        try:
                            # 1. Calculate curvature from spline derivatives
                            numerator = d1[0] * d2[1] - d1[1] * d2[0]
                            denominator = (d1[0]**2 + d1[1]**2)**(1.5)

                            if denominator < 1e-10:
                                continue

                            # Calculate curvature (in pixel space)
                            curvature = numerator / denominator

                            # Convert to physical units (nm⁻¹)
                            # Multiply by -1 to match the sign convention
                            curvature = -curvature / self.params.pixel_size

                            # Skip extreme values
                            if np.abs(curvature) > 1.0 / (10 * self.params.pixel_size):
                                continue

                            # 2. Calculate normal vector for fluorescence sampling
                            # Use the spline derivatives for normal vector
                            tangent = d1
                            normal = np.array([-tangent[1], tangent[0]])
                            norm = np.linalg.norm(normal)

                            if norm < 1e-10:
                                continue

                            normal = normal / norm

                            # Check if normal points into the cell
                            test_point = point + normal * 5
                            test_x, test_y = test_point.astype(int)

                            # Check bounds
                            if not (0 <= test_x < self.cell_data.data.shape[1] and
                                    0 <= test_y < self.cell_data.data.shape[0]):
                                continue

                            # Ensure normal points inward
                            if self.cell_data.data[test_y, test_x] == 0:
                                normal = -normal

                            # Create sampling rectangle
                            perpendicular = np.array([-normal[1], normal[0]])
                            center = point + (normal * self.params.vector_depth / 2)
                            half_width = self.params.vector_width / 2
                            half_depth = self.params.vector_depth / 2

                            rect_points = np.array([
                                center - perpendicular * half_width - normal * half_depth,
                                center + perpendicular * half_width - normal * half_depth,
                                center + perpendicular * half_width + normal * half_depth,
                                center - perpendicular * half_width + normal * half_depth
                            ])

                            rect_coords = rect_points.astype(int)

                            # Check rectangle bounds
                            if (np.any(rect_coords[:, 0] < 0) or
                                np.any(rect_coords[:, 0] >= self.fluor_data.data.shape[1]) or
                                np.any(rect_coords[:, 1] < 0) or
                                np.any(rect_coords[:, 1] >= self.fluor_data.data.shape[0])):
                                continue

                            # Create mask and sample
                            rect_mask = np.zeros_like(self.fluor_data.data, dtype=np.uint8)
                            cv2.fillPoly(rect_mask, [rect_coords], 1)

                            # Check interior overlap
                            interior_overlap = (np.sum(rect_mask & (self.cell_data.data > 0)) /
                                              np.sum(rect_mask) * 100)

                            if interior_overlap < self.params.interior_threshold:
                                continue

                            # Sample fluorescence values
                            mask = rect_mask.astype(bool)
                            fluor_values = self.fluor_data.data[mask]

                            if len(fluor_values) == 0:
                                continue

                            # Find corresponding segment in original contour (for reference only)
                            point_idx = sample_indices[i]
                            half_segment = self.params.segment_length // 2
                            indices = np.arange(point_idx - half_segment,
                                              point_idx + half_segment + 1) % n_points

                            # Store valid measurements
                            valid_points.append(point)
                            valid_indices.append(point_idx)  # Store the index
                            curvatures.append(curvature)
                            segment_indices.append(indices.tolist())

                            # Create and store fluorescence data
                            intensity_data = {
                                'mean': np.mean(fluor_values),
                                'min': np.min(fluor_values),
                                'max': np.max(fluor_values),
                                'std': np.std(fluor_values),
                                'rect_coords': rect_coords,
                                'raw_values': fluor_values,
                                'normal': normal,
                                'center': point,
                                'interior_overlap': interior_overlap
                            }

                            fluorescence_data.append(intensity_data)
                            intensity_values.append(np.mean(fluor_values))
                            sampling_regions.append(rect_coords)
                            interior_overlaps.append(interior_overlap)
                        except Exception as e:
                            print(f"Error processing spline point {i}: {e}")
                            continue

                    # Check if we have valid measurements
                    if not curvatures:
                        raise ValueError("No valid spline curvature measurements found")

                    # Create data objects
                    self.curvature_data = CurvatureData(
                        points=np.array(valid_points),
                        curvatures=np.array(curvatures),
                        segment_indices=segment_indices,
                        ref_curvatures=self.curvature_analyzer.ref_curvatures,
                        radius_scale=self.params.radius_scale
                    )

                    self.fluorescence_data = FluorescenceData(
                        sampling_points=fluorescence_data,
                        intensity_values=np.array(intensity_values),
                        sampling_regions=sampling_regions,
                        interior_overlaps=interior_overlaps
                    )

                    # Store valid indices in curvature analyzer for debug info
                    self.curvature_analyzer.valid_indices = np.array(valid_indices)

                except Exception as e:
                    traceback.print_exc()
                    raise ValueError(f"Spline fitting failed: {e}")




            elif self.params.curvature_method == "geometric":
                # Completely bypass the normal analysis flow for geometric method
                try:
                    print("Starting geometric method implementation...")

                    # Get the contour
                    contour = self.edge_data.smoothed_contour if self.edge_data.smoothed_contour is not None else self.edge_data.contour
                    n_points = len(contour)

                    # Generate sampling points
                    sample_indices = np.linspace(0, n_points-1, self.params.n_samples, dtype=int)

                    # Arrays to store results for both curvature and fluorescence
                    valid_points = []
                    curvatures = []
                    segment_indices = []
                    fluorescence_data_points = []
                    intensity_values = []
                    sampling_regions = []
                    interior_overlaps = []

                    # Initialize valid_indices for debug code elsewhere
                    valid_indices = []

                    print(f"Processing {len(sample_indices)} sample points...")

                    # Process each sample point
                    for idx in sample_indices:
                        # STEP 1: Calculate geometric curvature for this point
                        try:
                            # Get adjacent points
                            prev_idx = (idx - 1) % n_points
                            next_idx = (idx + 1) % n_points

                            prev_point = contour[prev_idx]
                            current_point = contour[idx]
                            next_point = contour[next_idx]

                            # Calculate vectors
                            vec_prev_to_next = next_point - prev_point
                            vec_prev_to_current = current_point - prev_point

                            # Calculate cross product
                            cross_product = vec_prev_to_next[0] * vec_prev_to_current[1] - vec_prev_to_next[1] * vec_prev_to_current[0]

                            # Calculate curvature sign
                            contour_center = np.mean(contour, axis=0)
                            to_center_vector = contour_center - current_point

                            normal = np.array([-vec_prev_to_next[1], vec_prev_to_next[0]])
                            normal = normal / np.linalg.norm(normal)

                            dot_product = np.dot(normal, to_center_vector)
                            sign_factor = -1 if dot_product > 0 else 1
                            curvature_sign = sign_factor * np.sign(cross_product)

                            # Calculate curvature magnitude
                            line_length = np.linalg.norm(vec_prev_to_next)
                            if line_length > 0:
                                height = abs(cross_product) / line_length

                                chord_length = line_length
                                if height > 0:
                                    radius = (height**2 + (chord_length/2)**2) / (2*height)
                                    curvature_magnitude = 1 / (radius * self.params.pixel_size)
                                else:
                                    curvature_magnitude = 0
                            else:
                                curvature_magnitude = 0

                            # Skip if curvature is zero
                            if curvature_magnitude == 0:
                                continue

                            curvature = curvature_sign * curvature_magnitude

                            # STEP 2: Calculate fluorescence for this point if we have fluorescence data
                            if self.fluor_data is not None:
                                # Get segment for normal calculation
                                half_segment = self.params.edge_segment // 2
                                segment_indices_array = np.arange(idx - half_segment, idx + half_segment + 1) % n_points
                                segment = contour[segment_indices_array]

                                # Calculate fluorescence using private method directly
                                intensity_data = self.fluorescence_analyzer._calculate_single_intensity(
                                    segment,
                                    self.fluor_data.data,
                                    self.cell_data.data,
                                    border_margin=20
                                )

                                # Skip if no valid fluorescence measurement
                                if intensity_data is None:
                                    continue

                                # Store fluorescence data
                                fluorescence_data_points.append(intensity_data)
                                intensity_values.append(intensity_data['mean'])
                                sampling_regions.append(intensity_data['rect_coords'])
                                interior_overlaps.append(intensity_data['interior_overlap'])

                            # Store curvature data
                            half_segment = self.params.segment_length // 2
                            vis_segment_indices = np.arange(idx - half_segment, idx + half_segment + 1) % n_points

                            valid_points.append(current_point)
                            curvatures.append(curvature)
                            segment_indices.append(vis_segment_indices.tolist())


                        except Exception as e:
                            print(f"Error processing point {idx}: {e}")
                            continue

                    print(f"Found {len(valid_points)} valid points with both curvature and fluorescence data")

                    # Create data objects if we have valid data
                    if len(valid_points) == 0:
                        raise ValueError("No valid measurements found")

                    # Create curvature data
                    self.curvature_data = CurvatureData(
                        points=np.array(valid_points),
                        curvatures=np.array(curvatures),
                        segment_indices=segment_indices,
                        ref_curvatures=self.curvature_analyzer.ref_curvatures,
                        radius_scale=self.params.radius_scale
                    )

                    # Create fluorescence data if available
                    if self.fluor_data is not None:
                        self.fluorescence_data = FluorescenceData(
                            sampling_points=fluorescence_data_points,
                            intensity_values=np.array(intensity_values),
                            sampling_regions=sampling_regions,
                            interior_overlaps=interior_overlaps
                        )

                    print("Geometric method completed successfully")


                    # Set valid indices in the curvature analyzer for debug info
                    self.curvature_analyzer.valid_indices = np.array([sample_indices[i] for i in range(len(valid_points))])


                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    raise ValueError(f"Geometric method failed: {e}")




            else:


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

            # Update visualization only if we have data
            if self.curvature_data is not None:
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

        if self.curvature_data is not None:
            # Add segment length info to debug
            debug_info.append(f"\nCurrent Segment Length: {self.params.segment_length}")
            # Show length of first few segments
            if self.curvature_data.segment_indices:
                for i in range(min(3, len(self.curvature_data.segment_indices))):
                    segment = self.curvature_data.segment_indices[i]
                    debug_info.append(f"Segment {i} length: {len(segment)} points")


        # Update debug text
        self.debug_text.setText("\n".join(debug_info))

    def update_analysis(self):
        """Update analysis when parameters change."""
        # Get updated parameters from panel
        self.params = self.analysis_panel.get_parameters()

        # Print debug info to verify parameter update
        #print(f"Updated segment_length parameter: {self.params.segment_length}")

        # Update analyzers with new parameters
        self.edge_detector.params = self.params
        self.curvature_analyzer.params = self.params
        self.fluorescence_analyzer.params = self.params

        # Update file panel parameters
        self.file_panel.params = self.params

        # Re-run analysis if we have data
        if self.cell_data is not None:
            self.run_analysis()
