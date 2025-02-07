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

        # Create figure
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Create subplots
        self.intensity_ax = self.figure.add_subplot(211)  # Intensity plot
        self.position_ax = self.figure.add_subplot(212)  # Position indicator

        self.figure.tight_layout()

    def update_plots(self, intensities, positions, current_frame):
        """Update plots with new data."""
        if intensities is None or positions is None:
            return

        # Clear entire figure
        self.figure.clear()

        # Recreate subplots
        self.intensity_ax = self.figure.add_subplot(211)
        self.position_ax = self.figure.add_subplot(212)

        # Plot intensities
        x = np.arange(len(intensities))
        self.intensity_ax.plot(x, intensities, 'b-', label='Intensity')
        self.intensity_ax.set_title('Edge Intensity Profile')
        self.intensity_ax.set_xlabel('Position along edge')
        self.intensity_ax.set_ylabel('Intensity')
        self.intensity_ax.grid(True)

        # Plot measurement positions with intensity-based coloring
        scatter = self.position_ax.scatter(positions[:, 0], positions[:, 1],
                                         c=intensities, cmap='viridis',
                                         s=100,  # Larger points
                                         label='Measurement Points')

        # Add colorbar
        self.figure.colorbar(scatter, ax=self.position_ax, label='Intensity')

        # Flip y-axis to match main display
        self.position_ax.invert_yaxis()

        self.position_ax.set_title('Measurement Positions')
        self.position_ax.set_aspect('equal')
        self.position_ax.grid(True)

        # Adjust layout
        self.figure.tight_layout()

        # Update canvas
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
        self.resize(800, 600)

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

    def update_results(self, intensities, positions, current_frame):
        """Update results display."""
        self.plots.update_plots(intensities, positions, current_frame)
