#!/usr/bin/env python3
# main.py

import sys
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow

def main():
    """Run the PIEZO1 analysis application."""
    # Create application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("PIEZO1 Analysis Tool")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Lab")
    app.setOrganizationDomain("lab.org")
    
    # Create and show main window
    window = MainWindow()
    window.resize(1400, 1000)
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()