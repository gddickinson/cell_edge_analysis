# src/gui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QFileDialog, QMenuBar, QMenu,
                           QStatusBar, QDialog, QSpinBox)
from PyQt6.QtCore import Qt
from .image_view import ImageViewer
from .toolbar import ToolBar
from ..image_processing.tiff_handler import TiffHandler
from ..image_processing.overlay import ImageOverlay
from ..analysis.edge_detection import EdgeDetector
from ..analysis.curvature import CurvatureAnalyzer

class AnalysisSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analysis Settings")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Edge region width
        edge_layout = QHBoxLayout()
        edge_layout.addWidget(QLabel("Edge Region Width (px):"))
        self.edge_width_spin = QSpinBox()
        self.edge_width_spin.setRange(1, 50)
        self.edge_width_spin.setValue(10)
        edge_layout.addWidget(self.edge_width_spin)
        layout.addLayout(edge_layout)

        # Curvature window size
        curv_layout = QHBoxLayout()
        curv_layout.addWidget(QLabel("Curvature Window Size:"))
        self.curv_window_spin = QSpinBox()
        self.curv_window_spin.setRange(3, 50)
        self.curv_window_spin.setValue(10)
        curv_layout.addWidget(self.curv_window_spin)
        layout.addLayout(curv_layout)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PIEZO1 Analysis Tool")

        # Initialize handlers
        self.tiff_handler = TiffHandler()
        self.overlay_handler = ImageOverlay()
        self.edge_detector = EdgeDetector()
        self.curvature_analyzer = CurvatureAnalyzer()

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

        settings_action = analysis_menu.addAction("Analysis Settings")
        settings_action.triggered.connect(self.show_analysis_settings)

        detect_edges_action = analysis_menu.addAction("Detect Cell Edges")
        detect_edges_action.triggered.connect(self.detect_edges)

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
        cell_frame, piezo_frame = self.tiff_handler.get_current_frame()
        if cell_frame is not None and piezo_frame is not None:
            # Get edge image for current frame
            edge_image = self.edge_detector.get_edge_image(self.tiff_handler.current_frame)
            pixmap = self.overlay_handler.create_overlay(cell_frame, piezo_frame, edge_image)
            self.image_viewer.update_display(pixmap)

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

    def show_analysis_settings(self):
        dialog = AnalysisSettingsDialog(self)
        if dialog.exec():
            # Store settings for later use
            self.edge_width = dialog.edge_width_spin.value()
            self.curv_window = dialog.curv_window_spin.value()

    def detect_edges(self):
        if self.tiff_handler.cell_stack is not None:
            self.status_bar.showMessage("Detecting cell edges in all frames...")
            # Process entire stack
            success = self.edge_detector.detect_edges_stack(self.tiff_handler.cell_stack)
            if success:
                self.status_bar.showMessage("Edge detection complete for all frames")
            else:
                self.status_bar.showMessage("Error during edge detection")
            # Update display for current frame
            self.update_display()

    def calculate_curvature(self):
        if self.edge_detector.contours is not None:
            self.status_bar.showMessage("Calculating membrane curvature...")
            curvature, smoothed_contour = self.curvature_analyzer.calculate_curvature(
                self.edge_detector.contours
            )
            if curvature is not None:
                # Update display with curvature visualization
                self.update_display()
                self.status_bar.showMessage("Curvature calculation complete")

    def save_analysis(self):
        # Add save functionality here
        pass

    def toggle_overlay(self):
        # Add overlay toggle functionality here
        pass
