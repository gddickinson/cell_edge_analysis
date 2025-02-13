#!/usr/bin/env python3
# src/gui/file_panel.py

import os
from typing import Optional, Tuple, List
import numpy as np
import tifffile
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QFileDialog, QSpinBox,
    QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..utils.data_structures import ImageData

class FilePanel(QWidget):
    """Panel for handling file operations."""

    # Signals for when images are loaded
    cell_mask_loaded = pyqtSignal(object)  # Emits ImageData
    fluorescence_loaded = pyqtSignal(object)  # Emits ImageData
    
    def __init__(self):
        super().__init__()
        self._init_ui()
        
        # Internal data storage
        self.cell_stack = None
        self.fluor_stack = None
        self.current_frame = 0
        
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Cell mask controls
        cell_group = QGroupBox("Cell Mask")
        cell_layout = QVBoxLayout()
        
        self.cell_label = QLabel("No file loaded")
        cell_layout.addWidget(self.cell_label)
        
        cell_buttons = QHBoxLayout()
        self.load_cell_button = QPushButton("Load Cell Mask")
        self.load_cell_button.clicked.connect(self.load_cell_mask)
        cell_buttons.addWidget(self.load_cell_button)
        
        self.save_cell_button = QPushButton("Save Cell Mask")
        self.save_cell_button.clicked.connect(self.save_cell_mask)
        self.save_cell_button.setEnabled(False)
        cell_buttons.addWidget(self.save_cell_button)
        
        cell_layout.addLayout(cell_buttons)
        cell_group.setLayout(cell_layout)
        layout.addWidget(cell_group)
        
        # Fluorescence controls
        fluor_group = QGroupBox("Fluorescence")
        fluor_layout = QVBoxLayout()
        
        self.fluor_label = QLabel("No file loaded")
        fluor_layout.addWidget(self.fluor_label)
        
        fluor_buttons = QHBoxLayout()
        self.load_fluor_button = QPushButton("Load Fluorescence")
        self.load_fluor_button.clicked.connect(self.load_fluorescence)
        fluor_buttons.addWidget(self.load_fluor_button)
        
        self.save_fluor_button = QPushButton("Save Fluorescence")
        self.save_fluor_button.clicked.connect(self.save_fluorescence)
        self.save_fluor_button.setEnabled(False)
        fluor_buttons.addWidget(self.save_fluor_button)
        
        fluor_layout.addLayout(fluor_buttons)
        fluor_group.setLayout(fluor_layout)
        layout.addWidget(fluor_group)
        
        # Frame controls
        frame_group = QGroupBox("Frame Control")
        frame_layout = QHBoxLayout()
        
        self.frame_spinner = QSpinBox()
        self.frame_spinner.setMinimum(0)
        self.frame_spinner.setMaximum(0)
        self.frame_spinner.valueChanged.connect(self.change_frame)
        frame_layout.addWidget(QLabel("Frame:"))
        frame_layout.addWidget(self.frame_spinner)
        
        self.frame_label = QLabel("0/0")
        frame_layout.addWidget(self.frame_label)
        
        frame_group.setLayout(frame_layout)
        layout.addWidget(frame_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
    def load_cell_mask(self):
        """Load cell mask image or stack."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Cell Mask",
            "",
            "TIFF files (*.tif *.tiff);;All files (*.*)"
        )
        
        if not file_path:
            return
            
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Load image
            image_stack = tifffile.imread(file_path)
            self.progress_bar.setValue(50)
            
            # Process stack
            if image_stack.ndim > 2:
                self.cell_stack = image_stack
                self.frame_spinner.setMaximum(len(image_stack) - 1)
                current_image = image_stack[self.current_frame]
            else:
                self.cell_stack = image_stack[np.newaxis, ...]
                current_image = image_stack
                
            # Create ImageData object
            image_data = ImageData(
                data=current_image,
                filename=os.path.basename(file_path),
                is_stack=self.cell_stack.ndim > 2,
                current_frame=self.current_frame
            )
            
            # Update UI
            self.cell_label.setText(f"Loaded: {os.path.basename(file_path)}")
            self.save_cell_button.setEnabled(True)
            self._update_frame_label()
            
            # Emit signal
            self.cell_mask_loaded.emit(image_data)
            
            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Error loading cell mask: {str(e)}")
            
    def load_fluorescence(self):
        """Load fluorescence image or stack."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Fluorescence Image",
            "",
            "TIFF files (*.tif *.tiff);;All files (*.*)"
        )
        
        if not file_path:
            return
            
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Load image
            image_stack = tifffile.imread(file_path)
            self.progress_bar.setValue(50)
            
            # Process stack
            if image_stack.ndim > 2:
                self.fluor_stack = image_stack
                self.frame_spinner.setMaximum(len(image_stack) - 1)
                current_image = image_stack[self.current_frame]
            else:
                self.fluor_stack = image_stack[np.newaxis, ...]
                current_image = image_stack
                
            # Validate dimensions match cell mask if loaded
            if self.cell_stack is not None:
                if self.fluor_stack.shape[1:] != self.cell_stack.shape[1:]:
                    raise ValueError("Fluorescence image dimensions do not match cell mask")
                    
            # Create ImageData object
            image_data = ImageData(
                data=current_image,
                filename=os.path.basename(file_path),
                is_stack=self.fluor_stack.ndim > 2,
                current_frame=self.current_frame
            )
            
            # Update UI
            self.fluor_label.setText(f"Loaded: {os.path.basename(file_path)}")
            self.save_fluor_button.setEnabled(True)
            self._update_frame_label()
            
            # Emit signal
            self.fluorescence_loaded.emit(image_data)
            
            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Error loading fluorescence image: {str(e)}")
            
    def save_cell_mask(self):
        """Save cell mask to file."""
        if self.cell_stack is None:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Cell Mask",
            "",
            "TIFF files (*.tif *.tiff)"
        )
        
        if file_path:
            try:
                tifffile.imwrite(file_path, self.cell_stack)
                QMessageBox.information(self, "Success", "Cell mask saved successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving cell mask: {str(e)}")
                
    def save_fluorescence(self):
        """Save fluorescence image to file."""
        if self.fluor_stack is None:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Fluorescence Image",
            "",
            "TIFF files (*.tif *.tiff)"
        )
        
        if file_path:
            try:
                tifffile.imwrite(file_path, self.fluor_stack)
                QMessageBox.information(self, "Success", "Fluorescence image saved successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving fluorescence image: {str(e)}")
                
    def change_frame(self, frame_number: int):
        """Change the current frame number."""
        if frame_number == self.current_frame:
            return
            
        self.current_frame = frame_number
        self._update_frame_label()
        
        # Emit signals with new frame data if available
        if self.cell_stack is not None:
            self.cell_mask_loaded.emit(ImageData(
                data=self.cell_stack[frame_number],
                filename=self.cell_label.text().replace("Loaded: ", ""),
                is_stack=True,
                current_frame=frame_number
            ))
            
        if self.fluor_stack is not None:
            self.fluorescence_loaded.emit(ImageData(
                data=self.fluor_stack[frame_number],
                filename=self.fluor_label.text().replace("Loaded: ", ""),
                is_stack=True,
                current_frame=frame_number
            ))
            
    def _update_frame_label(self):
        """Update the frame counter label."""
        max_frames = max(
            len(self.cell_stack) if self.cell_stack is not None else 1,
            len(self.fluor_stack) if self.fluor_stack is not None else 1
        )
        self.frame_label.setText(f"{self.current_frame + 1}/{max_frames}")
        
    def get_current_images(self) -> Tuple[Optional[ImageData], Optional[ImageData]]:
        """Get current frame data for both channels."""
        cell_data = None
        if self.cell_stack is not None:
            cell_data = ImageData(
                data=self.cell_stack[self.current_frame],
                filename=self.cell_label.text().replace("Loaded: ", ""),
                is_stack=self.cell_stack.ndim > 2,
                current_frame=self.current_frame
            )
            
        fluor_data = None
        if self.fluor_stack is not None:
            fluor_data = ImageData(
                data=self.fluor_stack[self.current_frame],
                filename=self.fluor_label.text().replace("Loaded: ", ""),
                is_stack=self.fluor_stack.ndim > 2,
                current_frame=self.current_frame
            )
            
        return cell_data, fluor_data