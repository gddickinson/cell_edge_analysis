# src/gui/results_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QDockWidget,
                           QLabel, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class ResultsPlot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Create figure with appropriate size
        self.figure = Figure(figsize=(15, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

    def update_plots(self, intensities, positions, current_frame, curvature=None, smoothed_contour=None):
        """Update plots with new data."""
        if intensities is None or positions is None:
            return

        # Clear entire figure
        self.figure.clear()

        if curvature is not None:
            # Three row layout with intensity profile, curvature profile, and three plots at bottom
            gs = self.figure.add_gridspec(3, 3, height_ratios=[1, 1, 1], hspace=0.4, wspace=0.4)

            # Intensity profile spanning all columns in first row
            ax_intensity = self.figure.add_subplot(gs[0, :])

            # Curvature profile spanning all columns in second row
            ax_curv = self.figure.add_subplot(gs[1, :])

            # Position plots and correlation in bottom row
            ax_pos_int = self.figure.add_subplot(gs[2, 0])  # Intensity map
            ax_pos_curv = self.figure.add_subplot(gs[2, 1])  # Curvature map
            ax_corr = self.figure.add_subplot(gs[2, 2])  # Correlation plot

            # Plot curvature profile
            x = np.arange(len(curvature))
            ax_curv.plot(x, curvature, 'r-', label='Curvature')
            ax_curv.axhline(y=0, color='k', linestyle='--', alpha=0.3)
            ax_curv.set_title('Edge Curvature Profile')
            ax_curv.set_xlabel('Position along edge')
            ax_curv.set_ylabel('Curvature')
            ax_curv.grid(True)
            ax_curv.legend()

            # Plot position colored by curvature
            scatter_curv = ax_pos_curv.scatter(positions[:, 0], positions[:, 1],
                                             c=curvature, cmap='RdBu_r',
                                             s=100)
            if smoothed_contour is not None:
                ax_pos_curv.plot(smoothed_contour[:, 0], smoothed_contour[:, 1],
                               'k--', alpha=0.5)
            ax_pos_curv.set_title('Curvature Map')
            self.figure.colorbar(scatter_curv, ax=ax_pos_curv, label='Curvature')
            ax_pos_curv.invert_yaxis()
            ax_pos_curv.set_aspect('equal')

            # Plot correlation
            ax_corr.scatter(curvature, intensities, c='purple', alpha=0.5)
            ax_corr.set_title('Intensity vs Curvature')
            ax_corr.set_xlabel('Curvature')
            ax_corr.set_ylabel('Intensity')
            ax_corr.grid(True)
            correlation = np.corrcoef(curvature, intensities)[0, 1]
            ax_corr.text(0.05, 0.95, f'r = {correlation:.3f}',
                        transform=ax_corr.transAxes,
                        verticalalignment='top')

        else:
            # Two subplot layout for intensity only
            gs = self.figure.add_gridspec(2, 1, height_ratios=[1, 1], hspace=0.4)
            ax_intensity = self.figure.add_subplot(gs[0])
            ax_pos_int = self.figure.add_subplot(gs[1])

        # Plot intensity profile
        x = np.arange(len(intensities))
        ax_intensity.plot(x, intensities, 'b-', label='Intensity')
        ax_intensity.set_title('Edge Intensity Profile')
        ax_intensity.set_xlabel('Position along edge')
        ax_intensity.set_ylabel('Intensity')
        ax_intensity.grid(True)
        ax_intensity.legend()

        # Plot position colored by intensity (always shown)
        scatter_int = ax_pos_int.scatter(positions[:, 0], positions[:, 1],
                                       c=intensities, cmap='viridis',
                                       s=100)
        if smoothed_contour is not None:
            ax_pos_int.plot(smoothed_contour[:, 0], smoothed_contour[:, 1],
                           'r--', alpha=0.5)
        ax_pos_int.set_title('Intensity Map')
        self.figure.colorbar(scatter_int, ax=ax_pos_int, label='Intensity')
        ax_pos_int.invert_yaxis()
        ax_pos_int.set_aspect('equal')

        # Update canvas
        self.figure.tight_layout()
        self.canvas.draw()

class ResultsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analysis Results")
        self.parent = parent
        self.show_vectors = False
        self.show_smoothed = False
        self.setup_ui()

    def setup_ui(self):
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create button layout
        button_layout = QHBoxLayout()

        # Add vector toggle button
        self.vector_button = QPushButton("Toggle Sampling Vectors")
        self.vector_button.setCheckable(True)
        self.vector_button.clicked.connect(self.toggle_vectors)
        button_layout.addWidget(self.vector_button)

        # Add smoothed line toggle button
        self.smoothed_button = QPushButton("Toggle Smoothed Line")
        self.smoothed_button.setCheckable(True)
        self.smoothed_button.clicked.connect(self.toggle_smoothed)
        button_layout.addWidget(self.smoothed_button)

        # Add button layout to main layout
        self.layout.addLayout(button_layout)

        # Add plots
        self.plots = ResultsPlot()
        self.layout.addWidget(self.plots)

        # Set window properties
        self.resize(1200, 800)

    def toggle_vectors(self):
        """Toggle the display of sampling vectors."""
        self.show_vectors = self.vector_button.isChecked()
        if self.parent:
            self.parent.update_display()

    def toggle_smoothed(self):
        """Toggle the display of smoothed line."""
        self.show_smoothed = self.smoothed_button.isChecked()
        if self.parent:
            self.parent.update_display()

    def update_results(self, intensities, positions, current_frame, curvature=None, smoothed_contour=None):
        """Update results display."""
        self.plots.update_plots(intensities, positions, current_frame,
                              curvature=curvature, smoothed_contour=smoothed_contour)
