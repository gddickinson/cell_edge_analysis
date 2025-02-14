#!/usr/bin/env python3
# src/gui/visualization_panel.py

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from typing import Optional

from ..utils.data_structures import (
    ImageData, EdgeData, CurvatureData, FluorescenceData, AnalysisParameters
)

class VisualizationPanel(QWidget):
    """Panel for visualization of analysis results."""

    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Create tab widget for different visualizations
        self.tab_widget = QTabWidget()

        # Create main analysis figure
        self.main_fig = Figure(figsize=(8, 8))
        self.main_canvas = FigureCanvas(self.main_fig)
        self.tab_widget.addTab(self.main_canvas, "Main View")

        # Create correlation plot figure
        self.corr_fig = Figure(figsize=(8, 8))
        self.corr_canvas = FigureCanvas(self.corr_fig)
        self.tab_widget.addTab(self.corr_canvas, "Correlation")

        # Create intensity profile figure
        self.profile_fig = Figure(figsize=(8, 8))
        self.profile_canvas = FigureCanvas(self.profile_fig)
        self.tab_widget.addTab(self.profile_canvas, "Intensity Profile")

        layout.addWidget(self.tab_widget)

        # Create custom colormaps
        colors = ['#0000FF', '#FFFFFF', '#FF0000']  # Blue to White to Red
        self.curvature_cmap = LinearSegmentedColormap.from_list('custom', colors)

    def plot_results(
        self,
        cell_data: ImageData,
        fluor_data: Optional[ImageData],
        edge_data: EdgeData,
        curvature_data: Optional[CurvatureData],
        fluorescence_data: Optional[FluorescenceData],
        params: AnalysisParameters
        ):
        """Update all visualizations with new results."""
        self._plot_main_view(
            cell_data, fluor_data, edge_data,
            curvature_data, fluorescence_data, params
        )

        if curvature_data is not None and fluorescence_data is not None:
            self._plot_correlation(curvature_data, fluorescence_data)
            self._plot_intensity_profile(fluorescence_data, curvature_data)

        # Refresh all canvases
        self.main_canvas.draw()
        self.corr_canvas.draw()
        self.profile_canvas.draw()

    def _plot_main_view(
        self,
        cell_data: ImageData,
        fluor_data: Optional[ImageData],
        edge_data: EdgeData,
        curvature_data: Optional[CurvatureData],
        fluorescence_data: Optional[FluorescenceData],
        params: AnalysisParameters
    ):
        """Plot main analysis view."""
        self.main_fig.clear()
        ax = self.main_fig.add_subplot(111)

        # Show background image
        if fluor_data is not None:
            ax.imshow(fluor_data.data, cmap='gray',
                     alpha=params.background_alpha)
        else:
            ax.imshow(cell_data.data, cmap='gray',
                     alpha=params.background_alpha)

        # Show cell edge if enabled
        if params.show_edge:
            if edge_data.smoothed_contour is not None:
                ax.plot(edge_data.smoothed_contour[:, 0],
                       edge_data.smoothed_contour[:, 1],
                       'y-', linewidth=1, alpha=0.8)
            else:
                ax.plot(edge_data.contour[:, 0],
                       edge_data.contour[:, 1],
                       'y-', linewidth=1, alpha=0.8)

        # Plot curvature data if available
        if curvature_data is not None:
            # Create symmetric colorbar around zero
            max_abs_curvature = max(abs(np.min(curvature_data.curvatures)),
                                  abs(np.max(curvature_data.curvatures)))
            norm = plt.Normalize(vmin=-max_abs_curvature,
                               vmax=max_abs_curvature)

            # Plot segments with curvature coloring
            for point, curvature, indices in zip(
                curvature_data.points,
                curvature_data.curvatures,
                curvature_data.segment_indices
            ):
                segment = edge_data.contour[indices]
                color = self.curvature_cmap(norm(curvature))
                ax.plot(segment[:, 0], segment[:, 1],
                       color=color, linewidth=params.line_width)

            # Add colorbar for curvature
            sm = plt.cm.ScalarMappable(cmap=self.curvature_cmap, norm=norm)
            colorbar = self.main_fig.colorbar(sm, ax=ax,
                                            label='Curvature (nm⁻¹)')

            # Add reference lines for typical biological curvatures
            ref_colors = ['g', 'r', 'y']
            for (name, value), color in zip(
                curvature_data.ref_curvatures.items(),
                ref_colors
            ):
                if abs(value) <= max_abs_curvature:
                    colorbar.ax.axhline(y=value, color=color,
                                      linestyle='--', alpha=0.5)
                    colorbar.ax.text(2.5, value,
                                   name.replace('_', ' '),
                                   color=color, va='center',
                                   ha='left')

        # Plot fluorescence data if available
        if fluorescence_data is not None:
            # Get intensity values for colormapping
            mean_intensities = fluorescence_data.mean_intensities

            # Calculate percentile-based range for better contrast
            min_val = np.percentile(mean_intensities, 1)
            max_val = np.percentile(mean_intensities, 99)
            norm = plt.Normalize(vmin=min_val, vmax=max_val)

            # Plot sampling rectangles
            for i, (data, rect_coords) in enumerate(zip(
                fluorescence_data.sampling_points,
                fluorescence_data.sampling_regions
            )):
                color = plt.cm.viridis(norm(data['mean']))

                # Create and add rectangle patch
                poly = patches.Polygon(
                    rect_coords,
                    facecolor=color,
                    alpha=params.rectangle_alpha,
                    edgecolor=color
                )
                ax.add_patch(poly)

                # Draw normal vector if available
                if 'normal' in data and 'center' in data:
                    vector_length = params.vector_depth
                    end_point = data['center'] + data['normal'] * vector_length
                    ax.plot([data['center'][0], end_point[0]],
                           [data['center'][1], end_point[1]],
                           'r-', linewidth=0.5, alpha=0.5)

            # Add colorbar for fluorescence
            sm = plt.cm.ScalarMappable(cmap='viridis', norm=norm)
            colorbar = self.main_fig.colorbar(
                sm, ax=ax, label='Mean Fluorescence Intensity'
            )

        ax.set_title('PIEZO1 Analysis')
        ax.set_aspect('equal')

    def _plot_correlation(
        self,
        curvature_data: CurvatureData,
        fluorescence_data: FluorescenceData
    ):
        """Plot correlation between curvature and fluorescence."""
        self.corr_fig.clear()
        ax = self.corr_fig.add_subplot(111)

        # Get valid data points (non-zero curvature)
        mask = curvature_data.curvatures != 0
        curvatures = curvature_data.curvatures[mask]
        intensities = fluorescence_data.mean_intensities[mask]

        # Create scatter plot
        ax.scatter(curvatures, intensities, alpha=0.5)

        # Add trend line
        z = np.polyfit(curvatures, intensities, 1)
        p = np.poly1d(z)
        x_range = np.linspace(min(curvatures), max(curvatures), 100)
        ax.plot(x_range, p(x_range), 'r--', alpha=0.8)

        # Calculate correlation coefficient
        corr_coef = np.corrcoef(curvatures, intensities)[0, 1]

        ax.set_xlabel('Curvature (nm⁻¹)')
        ax.set_ylabel('Mean Fluorescence Intensity')
        ax.set_title(f'Curvature vs Intensity (r = {corr_coef:.3f})')
        ax.grid(True, alpha=0.3)

    def _plot_intensity_profile(
        self,
        fluorescence_data: FluorescenceData,
        curvature_data: Optional[CurvatureData] = None
        ):
        """Plot intensity and curvature profiles along membrane."""
        self.profile_fig.clear()

        # Create two subplots sharing x axis
        ax1 = self.profile_fig.add_subplot(211)  # Top plot for intensity
        ax2 = self.profile_fig.add_subplot(212, sharex=ax1)  # Bottom plot for curvature

        # Plot intensity data
        positions = np.arange(len(fluorescence_data.intensity_values))

        # Mean intensity
        ax1.plot(positions, fluorescence_data.intensity_values,
                'b-', linewidth=2, label='Mean Intensity')

        # Min and max intensities
        min_values = [data['min'] for data in fluorescence_data.sampling_points]
        max_values = [data['max'] for data in fluorescence_data.sampling_points]

        ax1.fill_between(positions, min_values, max_values,
                        alpha=0.2, color='blue',
                        label='Min-Max Range')

        # Add error region using standard deviation
        std_values = [data['std'] for data in fluorescence_data.sampling_points]
        ax1.fill_between(
            positions,
            fluorescence_data.intensity_values - std_values,
            fluorescence_data.intensity_values + std_values,
            alpha=0.3, color='gray',
            label='±1 SD'
        )

        ax1.set_ylabel('Fluorescence Intensity')
        ax1.set_title('Intensity Profile')
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # Plot curvature data if available
        if curvature_data is not None:
            ax2.plot(positions, curvature_data.curvatures,
                    'r-', linewidth=2)

            # Add reference lines for typical biological curvatures
            ref_colors = ['g', 'r', 'y']
            for (name, value), color in zip(curvature_data.ref_curvatures.items(), ref_colors):
                ax2.axhline(y=value, color=color, linestyle='--', alpha=0.5,
                           label=name.replace('_', ' '))

            ax2.set_xlabel('Position Along Membrane')
            ax2.set_ylabel('Curvature (nm⁻¹)')
            ax2.set_title('Curvature Profile')
            ax2.grid(True, alpha=0.3)
            ax2.legend()

        # Adjust layout to prevent overlap
        self.profile_fig.tight_layout()
        self.profile_canvas.draw()
