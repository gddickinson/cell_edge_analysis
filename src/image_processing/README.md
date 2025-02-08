
## User Guide

### Understanding the Image Processing Module

This module handles how the program works with your microscopy images. It takes care of:
- Loading your TIFF files
- Showing both channels together
- Managing memory efficiently
- Creating the visualization you see

### Key Components

#### TIFF Handler (`tiff_handler.py`)
This handles your image files:
- Loads cell and PIEZO1 image stacks
- Keeps track of which frame you're viewing
- Makes sure both channels line up correctly
- Handles memory efficiently for large files

What it does:
1. **Loading Images**
   - Opens your TIFF stacks
   - Checks they're the right format
   - Gets them ready for display
   - Manages memory efficiently

2. **Frame Navigation**
   - Keeps track of current frame
   - Lets you move between frames
   - Makes sure both channels stay synchronized
   - Handles memory efficiently

3. **Image Preparation**
   - Adjusts contrast automatically
   - Removes background noise
   - Makes images display-ready
   - Standardizes image formats

#### Overlay Display (`overlay.py`)
This creates the image display you see:
- Combines cell and PIEZO1 channels
- Handles transparency
- Shows measurement vectors
- Updates in real-time

Features:
1. **Image Display**
   - Shows both channels together
   - Lets you adjust transparency
   - Updates smoothly as you work
   - Shows measurements on top

2. **Visual Elements**
   - Blue line for cell edge
   - Yellow arrows for measurements
   - Color coding for intensity
   - Smooth updates

3. **Display Controls**
   - Adjust transparency
   - Toggle different elements
   - Zoom and pan
   - Real-time updates

### For Developers

#### Adding New Features
1. Loading New File Types:
```python
def load_new_format(file_path):
    # Your loading code here
    return processed_data
```

2. Adding New Visualizations:
```python
def add_new_overlay(image_data):
    # Your visualization code here
    return overlay_image
```

#### Best Practices
1. Memory Management:
   - Use lazy loading for large files
   - Clean up unused data
   - Monitor memory usage

2. Performance:
   - Cache frequently used data
   - Update only what's needed
   - Use efficient algorithms

### Troubleshooting

Common Issues:
1. Images not loading:
   - Check file format
   - Verify file permissions
   - Check available memory

2. Display problems:
   - Check image dimensions match
   - Verify bit depth
   - Check memory availability

3. Slow performance:
   - Reduce file size if possible
   - Close unused applications
   - Check system resources

### Tips and Tricks
1. Working with large files:
   - Load subset of frames first
   - Use frame skipping for preview
   - Close other applications

2. Getting the best display:
   - Adjust contrast before analysis
   - Use appropriate zoom level
   - Toggle overlays as needed

3. Memory efficiency:
   - Don't load more frames than needed
   - Clear memory when switching files
   - Use frame skipping for navigation

### Getting Help
- Check console for error messages
- Look for warning messages
- Verify file formats match expectations
- Monitor system resources
