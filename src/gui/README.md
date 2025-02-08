# GUI Module Guide

## Overview
This folder contains all the graphical interface components of the PIEZO1 Analysis Tool. The GUI provides an intuitive way to load, view, and analyze TIRF microscopy data.

## Files and Their Purpose

### `main_window.py`
The main application window that you see when starting the program. It contains:
- Menu bar with File and Analysis options
- Toolbar with common controls
- Main image display area
- Status bar showing current operations

Key features:
- Load cell and PIEZO1 image stacks
- Navigate through frames
- Adjust display settings
- Run analysis operations

### `image_view.py`
Handles the display of microscopy images:
- Shows overlaid cell and PIEZO1 channels
- Supports zoom and pan
- Displays sampling vectors and cell edges
- Updates in real-time as you analyze

Controls:
- Mouse wheel: Zoom in/out
- Left click + drag: Pan around the image
- Mouse hover: Shows intensity values

### `results_window.py`
Shows analysis results and plots:
- Intensity profile along the cell edge
- Curvature measurements when calculated
- Position maps showing where measurements were taken
- Correlation between intensity and curvature

Features:
- Interactive plots
- Toggle between different views
- Real-time updates as you adjust parameters
- Color-coded visualization of measurements

### `analysis_dialog.py`
Dialog window for setting analysis parameters:
- Sampling depth into the cell
- Width of sampling regions
- Measurement interval along the edge
- Type of intensity measurement (mean/min/max)

Tips:
- Hover over parameters for tooltips
- Preview changes before applying
- Reset button to restore defaults

### `toolbar.py`
Contains controls for common operations:
- Frame navigation
- Opacity adjustment
- Zoom level control
- Edge smoothing adjustment

## For Developers

### Adding New Features
1. Each window/dialog is a separate class inheriting from PyQt6
2. Follow the existing pattern of separating UI setup from functionality
3. Use signals and slots for communication between components

Example of adding a new button:
```python
# In any window class
def setup_ui(self):
    # Create button
    new_button = QPushButton("New Feature")
    new_button.clicked.connect(self.handle_new_feature)
    self.layout.addWidget(new_button)

def handle_new_feature(self):
    # Your code here
    pass
```

### Modifying Existing Features
1. UI elements are created in the `setup_ui()` method of each class
2. Event handlers are named after their function (e.g., `update_display()`)
3. Most display updates happen through the `update_display()` method

### Best Practices
1. Keep the UI responsive:
   - Use worker threads for long operations
   - Update the status bar to show progress
   - Don't block the main thread

2. Handle errors gracefully:
   - Show meaningful error messages
   - Provide recovery options
   - Log errors for debugging

3. Maintain consistency:
   - Follow existing naming conventions
   - Keep similar features in similar locations
   - Use standard Qt widgets when possible

## Common Tasks

### Adding a New Plot
```python
# In results_window.py
def add_new_plot(self, data):
    ax = self.figure.add_subplot(111)
    ax.plot(data)
    self.canvas.draw()
```

### Adding a New Dialog
```python
# New file: my_dialog.py
from PyQt6.QtWidgets import QDialog

class MyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        # Add your widgets here
        pass
```

### Updating the Display
```python
# In any window class
def update_my_display(self):
    # Update your display elements
    self.update_display()  # Call main update method
```

## Troubleshooting

### Common Issues
1. Window doesn't update:
   - Check if `update_display()` is being called
   - Verify data is being passed correctly
   - Make sure the window is visible

2. Plots not showing:
   - Confirm data is not None
   - Check plot dimensions
   - Call canvas.draw() after updates

3. Controls not responding:
   - Verify connections are properly set up
   - Check for errors in event handlers
   - Make sure widgets are enabled

### Getting Help
- Check the debug output in the console
- Look for status bar messages
- Add print statements for debugging
- Review the technical documentation for details

## Tips and Tricks
1. Use keyboard shortcuts:
   - Left/Right: Navigate frames
   - Ctrl+Mouse Wheel: Adjust opacity
   - Space: Toggle overlay

2. Efficient analysis:
   - Set parameters before running analysis
   - Use the preview feature when available
   - Save commonly used settings

3. Working with plots:
   - Click legends to toggle elements
   - Drag to pan
   - Right-click for context menu