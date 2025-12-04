#!/usr/bin/env python3
# src/gui/file_panel.py

import os
from typing import Optional, Tuple, List
import numpy as np
import tifffile
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QFileDialog, QSpinBox,
    QMessageBox, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..utils.data_structures import ImageData
from ..gui.results_window import ResultsWindow

class FilePanel(QWidget):
    """Panel for handling file operations."""

    # Add signals for when images are loaded
    cell_mask_loaded = pyqtSignal(object)  # Emits ImageData
    fluorescence_loaded = pyqtSignal(object)  # Emits ImageData
    files_ready = pyqtSignal()  # Signal when both files are loaded and ready for analysis


    def __init__(self, edge_detector, curvature_analyzer, fluorescence_analyzer, params, parent=None):
        super().__init__(parent)

        # Store analyzers and parameters
        self.edge_detector = edge_detector
        self.curvature_analyzer = curvature_analyzer
        self.fluorescence_analyzer = fluorescence_analyzer
        self.params = params

        # Internal data storage
        self.cell_stack = None
        self.fluor_stack = None
        self.current_frame = 0

        self._init_ui()


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

        # Add batch analysis section
        batch_group = QGroupBox("Batch Analysis")
        batch_layout = QVBoxLayout()

        # Progress display
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        batch_layout.addWidget(self.progress_bar)

        # Analyze Stack button
        self.analyze_stack_button = QPushButton("Analyze All Frames")
        self.analyze_stack_button.clicked.connect(self.analyze_stack)
        self.analyze_stack_button.setEnabled(False)  # Enable only when stacks are loaded
        batch_layout.addWidget(self.analyze_stack_button)

        batch_group.setLayout(batch_layout)
        layout.addWidget(batch_group)

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
            self._update_buttons()

            # Emit signal for loaded cell mask
            self.cell_mask_loaded.emit(image_data)

            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)

            # Emit files_ready if both files are loaded
            if self.fluor_stack is not None:
                self.files_ready.emit()

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
            self._update_buttons()

            # Emit signal for loaded fluorescence image
            self.fluorescence_loaded.emit(image_data)

            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)

            # Emit files_ready if both files are loaded
            if self.cell_stack is not None:
                self.files_ready.emit()

        except Exception as e:
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Error loading fluorescence image: {str(e)}")

    def change_frame(self, frame_number: int):
        """Change the current frame number."""
        if frame_number == self.current_frame:
            return

        self.current_frame = frame_number
        self._update_frame_label()

        # Emit signals with new frame data
        if self.cell_stack is not None:
            cell_data = ImageData(
                data=self.cell_stack[frame_number],
                filename=self.cell_label.text().replace("Loaded: ", ""),
                is_stack=True,
                current_frame=frame_number
            )
            self.cell_mask_loaded.emit(cell_data)

        if self.fluor_stack is not None:
            fluor_data = ImageData(
                data=self.fluor_stack[frame_number],
                filename=self.fluor_label.text().replace("Loaded: ", ""),
                is_stack=True,
                current_frame=frame_number
            )
            self.fluorescence_loaded.emit(fluor_data)

        # Emit files_ready signal if both files are loaded
        if self.cell_stack is not None and self.fluor_stack is not None:
            self.files_ready.emit()

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


    def show_results_window(self, all_curvatures, all_intensities, all_correlations):
        self.results_window = ResultsWindow(
            all_curvatures,
            all_intensities,
            all_correlations,
            parent=self
        )
        self.results_window.show()

    def analyze_stack(self):
        """Process all frames in the stack using current parameters."""
        if self.cell_stack is None:
            QMessageBox.warning(self, "Warning", "Please load cell mask stack first.")
            return

        try:
            # Create progress dialog
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            total_frames = len(self.cell_stack)

            # Storage for frame-by-frame results
            all_curvatures = []
            all_intensities = []
            all_correlations = []

            # Process each frame
            for frame in range(total_frames):
                # Update progress
                self.progress_bar.setValue(int((frame / total_frames) * 100))
                QApplication.processEvents()  # Keep UI responsive

                # Get current frame data
                cell_data = ImageData(
                    data=self.cell_stack[frame],
                    filename=self.cell_label.text().replace("Loaded: ", ""),
                    is_stack=True,
                    current_frame=frame
                )

                fluor_data = None
                if self.fluor_stack is not None:
                    fluor_data = ImageData(
                        data=self.fluor_stack[frame],
                        filename=self.fluor_label.text().replace("Loaded: ", ""),
                        is_stack=True,
                        current_frame=frame
                    )

                # Run edge detection
                edge_data = self.edge_detector.detect_edge(cell_data)
                if edge_data is None:
                    continue

                # Generate sampling points
                contour = edge_data.smoothed_contour if edge_data.smoothed_contour is not None else edge_data.contour
                n_points = len(contour)
                sample_indices = np.linspace(0, n_points-1, self.params.n_samples, dtype=int)

                # Calculate intensities first (to get valid sampling points)
                frame_intensities = []
                valid_indices = []

                if fluor_data is not None:
                    for idx in sample_indices:
                        # Get segment for normal calculation
                        half_segment = self.params.edge_segment // 2
                        segment_indices = np.arange(idx - half_segment, idx + half_segment + 1) % n_points
                        segment = contour[segment_indices]

                        intensity_data = self.fluorescence_analyzer._calculate_single_intensity(
                            segment,  # Pass full segment for normal calculation
                            fluor_data.data,
                            cell_data.data,
                            border_margin=20
                        )

                        if intensity_data is not None:
                            frame_intensities.append(intensity_data['mean'])
                            valid_indices.append(idx)

                    if not valid_indices:
                        continue

                    # Now calculate curvature only for valid intensity points
                    frame_curvatures = []
                    for idx in valid_indices:
                        half_segment = self.params.segment_length // 2
                        segment_indices = np.arange(idx - half_segment, idx + half_segment + 1) % n_points
                        segment = contour[segment_indices]

                        curvature = self.curvature_analyzer._fit_circle_to_segment(segment)
                        frame_curvatures.append(curvature)

                    frame_intensities = np.array(frame_intensities)
                    frame_curvatures = np.array(frame_curvatures)

                    # Only keep points where curvature is valid
                    valid_curv = frame_curvatures != 0
                    if np.any(valid_curv):
                        all_curvatures.append(frame_curvatures[valid_curv])
                        all_intensities.append(frame_intensities[valid_curv])
                        correlation = np.corrcoef(frame_curvatures[valid_curv],
                                               frame_intensities[valid_curv])[0, 1]
                        all_correlations.append(correlation)
                else:
                    # Calculate just curvature for all points
                    frame_curvatures = []
                    for idx in sample_indices:
                        half_segment = self.params.segment_length // 2
                        segment_indices = np.arange(idx - half_segment, idx + half_segment + 1) % n_points
                        segment = contour[segment_indices]

                        curvature = self.curvature_analyzer._fit_circle_to_segment(segment)
                        if curvature != 0:
                            frame_curvatures.append(curvature)

                    if frame_curvatures:
                        all_curvatures.append(np.array(frame_curvatures))

            # Show results window
            if all_curvatures:
                print(f"Frame analysis complete:")
                print(f"  Number of frames analyzed: {len(all_curvatures)}")
                if all_intensities:
                    print(f"  Points per frame: {[len(c) for c in all_curvatures]}")
                    print(f"  Average correlation: {np.mean(all_correlations):.3f}")

                self.results_window = ResultsWindow(
                    all_curvatures=all_curvatures,
                    all_intensities=all_intensities if all_intensities else None,
                    all_correlations=all_correlations if all_correlations else None,
                    parent=self
                )
                self.results_window.show()

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Analysis failed: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)

    def _update_buttons(self):
        """Update the state of all buttons based on loaded data."""
        # Update save buttons
        self.save_cell_button.setEnabled(self.cell_stack is not None)
        self.save_fluor_button.setEnabled(self.fluor_stack is not None)

        # Update batch analysis button
        self.analyze_stack_button.setEnabled(self.cell_stack is not None)

        # Trigger analysis on the current frame if both files are loaded
        if self.cell_stack is not None and self.fluor_stack is not None:
            self.files_ready.emit()
