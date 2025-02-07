# src/gui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QFileDialog, QMenuBar, QMenu,
                           QStatusBar, QDialog, QSpinBox)
from PyQt6.QtCore import Qt
from .image_view import ImageViewer
from .toolbar import ToolBar
from .analysis_dialog import IntensityAnalysisDialog
from .results_window import ResultsWindow
from ..image_processing.tiff_handler import TiffHandler
from ..image_processing.overlay import ImageOverlay
from ..analysis.edge_detection import EdgeDetector
from ..analysis.curvature import CurvatureAnalyzer
from ..analysis.intensity_analyzer import IntensityAnalyzer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PIEZO1 Analysis Tool")

        # Initialize handlers and windows
        self.tiff_handler = TiffHandler()
        self.overlay_handler = ImageOverlay()
        self.edge_detector = EdgeDetector()
        self.curvature_analyzer = CurvatureAnalyzer()
        self.intensity_analyzer = IntensityAnalyzer()
        self.results_window = None

        self.setup_ui()

    def setup_ui(self):
        # Set up the main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create menu bar
        self.create_menu_bar()

        # Create toolbar
        self.toolbar = ToolBar()
        self.toolbar.frame_changed.connect(self.update_frame)
        self.toolbar.opacity_changed.connect(self.update_opacity)
        self.toolbar.zoom_changed.connect(self.update_zoom)
        self.toolbar.smoothing_changed.connect(self.update_smoothing)
        self.addToolBar(self.toolbar)

        # Create image viewer
        self.image_viewer = ImageViewer()
        self.image_viewer.mouse_position.connect(self.update_status_bar)
        self.layout.addWidget(self.image_viewer)

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Set window size
        self.resize(1200, 800)

    def update_smoothing(self, window_size):
        """Update edge smoothing."""
        self.edge_detector.set_smoothing(window_size)
        self.update_display()

        # Re-run intensity analysis if it exists
        if self.results_window is not None and self.results_window.isVisible():
            self.analyze_edge_intensity(reuse_settings=True)

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        load_cell_action = file_menu.addAction("Load Cell Stack")
        load_cell_action.triggered.connect(self.load_cell_stack)

        load_piezo_action = file_menu.addAction("Load PIEZO1 Stack")
        load_piezo_action.triggered.connect(self.load_piezo_stack)

        file_menu.addSeparator()

        save_action = file_menu.addAction("Save Analysis")
        save_action.triggered.connect(self.save_analysis)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # Analysis menu
        analysis_menu = menubar.addMenu("Analysis")

        detect_edges_action = analysis_menu.addAction("Detect Cell Edges")
        detect_edges_action.triggered.connect(self.detect_edges)

        intensity_action = analysis_menu.addAction("Analyze Edge Intensity")
        intensity_action.triggered.connect(self.analyze_edge_intensity)

        calculate_curvature_action = analysis_menu.addAction("Calculate Curvature")
        calculate_curvature_action.triggered.connect(self.calculate_curvature)

        # View menu
        view_menu = menubar.addMenu("View")

        toggle_overlay_action = view_menu.addAction("Toggle Overlay")
        toggle_overlay_action.triggered.connect(self.toggle_overlay)

    def load_cell_stack(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Cell Stack", "",
            "TIFF files (*.tif *.tiff)"
        )
        if file_name:
            self.status_bar.showMessage(f"Loading cell stack: {file_name}")
            if self.tiff_handler.load_cell_stack(file_name):
                self.update_display()
                self.toolbar.set_frame_range(self.tiff_handler.n_frames)

    def load_piezo_stack(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load PIEZO1 Stack", "",
            "TIFF files (*.tif *.tiff)"
        )
        if file_name:
            self.status_bar.showMessage(f"Loading PIEZO1 stack: {file_name}")
            if self.tiff_handler.load_piezo_stack(file_name):
                self.update_display()

    def update_frame(self, frame_number):
        if self.tiff_handler.set_frame(frame_number - 1):  # Convert to 0-based index
            self.update_display()

    def update_opacity(self, value):
        self.overlay_handler.set_opacity(value)
        self.update_display()

    def update_zoom(self, value):
        self.image_viewer.set_zoom(value)

    def update_display(self):
        # Update main display
        cell_frame, piezo_frame = self.tiff_handler.get_current_frame()
        if cell_frame is not None and piezo_frame is not None:
            edge_image = self.edge_detector.get_edge_image(self.tiff_handler.current_frame)

            # Get sampling vectors if results window is showing them
            show_vectors = (self.results_window is not None and
                          self.results_window.isVisible() and
                          self.results_window.show_vectors)

            if show_vectors:
                # Get measurement points and normals
                _, points, normals = self.intensity_analyzer.get_frame_data(
                    self.tiff_handler.current_frame
                )
                sampling_depth = self.intensity_analyzer.sampling_depth
                vector_width = self.intensity_analyzer.vector_width
            else:
                points = None
                normals = None
                sampling_depth = None
                vector_width = None

            # Create overlay with optional vectors
            pixmap = self.overlay_handler.create_overlay(
                cell_frame,
                piezo_frame,
                edge_image,
                show_vectors,
                points,
                normals,
                sampling_depth,
                vector_width
            )
            self.image_viewer.update_display(pixmap)

        # Update results if window exists and is visible
        if self.results_window is not None and self.results_window.isVisible():
            intensities, points, _ = self.intensity_analyzer.get_frame_data(
                self.tiff_handler.current_frame
            )
            if intensities is not None and points is not None:
                self.results_window.update_results(
                    intensities,
                    points,
                    self.tiff_handler.current_frame
                )

    def update_status_bar(self, x, y):
        cell_frame, piezo_frame = self.tiff_handler.get_current_frame()
        if cell_frame is not None and piezo_frame is not None:
            try:
                cell_val = cell_frame[y, x]
                piezo_val = piezo_frame[y, x]
                self.status_bar.showMessage(
                    f"Position: ({x}, {y}) | Cell: {cell_val} | PIEZO1: {piezo_val}"
                )
            except IndexError:
                pass

    def detect_edges(self):
        if self.tiff_handler.cell_stack is not None:
            self.status_bar.showMessage("Detecting cell edges in all frames...")
            success = self.edge_detector.detect_edges_stack(self.tiff_handler.cell_stack)
            if success:
                self.status_bar.showMessage("Edge detection complete for all frames")
            else:
                self.status_bar.showMessage("Error during edge detection")
            self.update_display()

    def analyze_edge_intensity(self, reuse_settings=False):
        """Run edge intensity analysis."""
        print("Starting edge intensity analysis")  # Debug print
        if self.edge_detector.contours:
            # Only show settings dialog if not reusing settings
            if not reuse_settings:
                dialog = IntensityAnalysisDialog(self)
                if not dialog.exec():
                    return
                settings = dialog.get_settings()
                print("Analysis settings:", settings)  # Debug print

                # Set parameters
                self.intensity_analyzer.set_parameters(
                    settings['sampling_depth'],
                    settings['vector_width'],
                    settings['sampling_interval'],
                    settings['measure_type']
                )

            # Get current frame data
            cell_frame, piezo_frame = self.tiff_handler.get_current_frame()
            # Get smoothed contour if smoothing is applied, otherwise original contour
            contour = self.edge_detector.get_contour(self.tiff_handler.current_frame)

            if piezo_frame is not None and contour is not None:
                # Run analysis
                self.status_bar.showMessage("Analyzing edge intensity...")
                print("Running intensity analysis")  # Debug print
                success = self.intensity_analyzer.analyze_frame(
                    piezo_frame,
                    contour,
                    self.tiff_handler.current_frame
                )

                if success:
                    print("Analysis successful, creating results window")  # Debug print
                    # Get results data
                    intensities, points, _ = self.intensity_analyzer.get_frame_data(
                        self.tiff_handler.current_frame
                    )

                    print(f"Got data: {intensities is not None}, {points is not None}")  # Debug print

                    # Create new results window if needed
                    if self.results_window is None:
                        print("Creating new results window")  # Debug print
                        self.results_window = ResultsWindow(self)

                    # Update results
                    self.results_window.update_results(
                        intensities,
                        points,
                        self.tiff_handler.current_frame
                    )
                    print("Updated results")  # Debug print

                    # Show window
                    self.results_window.show()
                    self.results_window.raise_()
                    print("Showed results window")  # Debug print

                    self.status_bar.showMessage("Edge intensity analysis complete")
                else:
                    print("Analysis failed")  # Debug print
                    self.status_bar.showMessage("Error in intensity analysis")
        else:
            self.status_bar.showMessage("Please detect cell edges first")

    def calculate_curvature(self):
        if self.edge_detector.contours is not None:
            self.status_bar.showMessage("Calculating membrane curvature...")
            curvature, smoothed_contour = self.curvature_analyzer.calculate_curvature(
                self.edge_detector.contours
            )
            if curvature is not None:
                self.update_display()
                self.status_bar.showMessage("Curvature calculation complete")

    def save_analysis(self):
        # Add save functionality here
        pass

    def toggle_overlay(self):
        # Add overlay toggle functionality here
        pass
