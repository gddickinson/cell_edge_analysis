# src/gui/results_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QDockWidget,
                           QLabel, QPushButton)
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
        
        # Create figure with subplots
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
            
        # Clear previous plots
        self.intensity_ax.clear()
        self.position_ax.clear()
        
        # Plot intensities
        x = np.arange(len(intensities))
        self.intensity_ax.plot(x, intensities, 'b-', label='Intensity')
        self.intensity_ax.set_title('Edge Intensity Profile')
        self.intensity_ax.set_xlabel('Position along edge')
        self.intensity_ax.set_ylabel('Intensity')
        self.intensity_ax.grid(True)
        
        # Plot measurement positions
        self.position_ax.plot(positions[:, 0], positions[:, 1], 'r-', label='Edge')
        self.position_ax.set_title('Measurement Positions')
        self.position_ax.set_aspect('equal')
        self.position_ax.grid(True)
        
        # Update canvas
        self.canvas.draw()

class ResultsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analysis Results")
        self.setup_ui()
        
    def setup_ui(self):
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Add plots
        self.plots = ResultsPlot()
        self.layout.addWidget(self.plots)
        
        # Set window properties
        self.resize(800, 600)
        
    def update_results(self, intensities, positions, current_frame):
        """Update results display."""
        self.plots.update_plots(intensities, positions, current_frame)
