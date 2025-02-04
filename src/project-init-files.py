# main.py
import sys
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow

def main():
    """Initialize and run the PIEZO1 Analysis application."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("PIEZO1 Analysis Tool")
    app.setOrganizationName("Lab")
    app.setOrganizationDomain("lab.org")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

# src/__init__.py
"""
PIEZO1 Analysis Tool - A Python application for analyzing PIEZO1 protein distribution
in relation to cell membrane curvature using TIRF microscopy data.
"""

__version__ = '0.1.0'
__author__ = 'Lab'

# src/gui/__init__.py
"""
GUI components for the PIEZO1 Analysis Tool.
Contains the main window, image viewer, and toolbar implementations.
"""

from .main_window import MainWindow
from .image_view import ImageViewer
from .toolbar import ToolBar

__all__ = ['MainWindow', 'ImageViewer', 'ToolBar']

# src/image_processing/__init__.py
"""
Image processing modules for handling TIFF stacks and creating image overlays.
"""

from .tiff_handler import TiffHandler
from .overlay import ImageOverlay

__all__ = ['TiffHandler', 'ImageOverlay']

# src/analysis/__init__.py
"""
Analysis modules for cell edge detection and curvature calculation.
"""

from .edge_detection import EdgeDetector
from .curvature import CurvatureAnalyzer

__all__ = ['EdgeDetector', 'CurvatureAnalyzer']
