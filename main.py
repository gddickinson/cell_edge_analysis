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
