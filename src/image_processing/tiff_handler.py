# src/image_processing/tiff_handler.py
import numpy as np
import tifffile
from skimage import exposure

class TiffHandler:
    def __init__(self):
        self.cell_stack = None
        self.piezo_stack = None
        self.current_frame = 0
        self.n_frames = 0

    def load_cell_stack(self, file_path):
        """
        Load and preprocess cell segmentation TIFF stack.

        Args:
            file_path (str): Path to TIFF file

        Returns:
            bool: Success status
        """
        try:
            stack = tifffile.imread(file_path)

            # Handle single image vs stack
            if stack.ndim == 2:
                stack = stack[np.newaxis, ...]

            self.cell_stack = stack
            self.n_frames = len(stack)
            return True

        except Exception as e:
            print(f"Error loading cell stack: {e}")
            return False

    def load_piezo_stack(self, file_path):
        """
        Load and preprocess PIEZO1 TIFF stack.

        Args:
            file_path (str): Path to TIFF file

        Returns:
            bool: Success status
        """
        try:
            stack = tifffile.imread(file_path)

            # Handle single image vs stack
            if stack.ndim == 2:
                stack = stack[np.newaxis, ...]

            # Enhance contrast
            stack = exposure.rescale_intensity(stack)

            self.piezo_stack = stack
            return True

        except Exception as e:
            print(f"Error loading PIEZO1 stack: {e}")
            return False

    def get_current_frame(self):
        """Get current frames from both stacks."""
        if self.cell_stack is None or self.piezo_stack is None:
            return None, None

        return (self.cell_stack[self.current_frame],
                self.piezo_stack[self.current_frame])

    def next_frame(self):
        """Advance to next frame."""
        if self.n_frames > 0:
            self.current_frame = (self.current_frame + 1) % self.n_frames
            return True
        return False

    def previous_frame(self):
        """Go to previous frame."""
        if self.n_frames > 0:
            self.current_frame = (self.current_frame - 1) % self.n_frames
            return True
        return False

    def set_frame(self, frame_number):
        """Set specific frame number."""
        if 0 <= frame_number < self.n_frames:
            self.current_frame = frame_number
            return True
        return False


