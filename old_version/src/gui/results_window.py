#!/usr/bin/env python3
# src/gui/results_window.py

import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTabWidget, QFileDialog
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd

class ResultsWindow(QMainWindow):
    """Window to display batch analysis results."""
    
    def __init__(self, all_curvatures, all_intensities, all_correlations, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PIEZO1 Analysis Results")
        
        # Store data
        self.all_curvatures = all_curvatures
        self.all_intensities = all_intensities
        self.all_correlations = all_correlations
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget for different result views
        tabs = QTabWidget()
        
        # Add tabs
        summary_tab = self._create_summary_tab()
        plots_tab = self._create_plots_tab()
        correlation_tab = self._create_correlation_tab()
        
        tabs.addTab(summary_tab, "Summary")
        tabs.addTab(plots_tab, "Frame Analysis")
        tabs.addTab(correlation_tab, "Correlation")
        
        layout.addWidget(tabs)
        
        # Add export section
        export_layout = self._create_export_section()
        layout.addLayout(export_layout)
        
    def _create_summary_tab(self):
        """Create summary statistics view."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Calculate statistics
        stats = self._calculate_summary_statistics()
        
        # Create summary figure
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        
        # Plot summary data
        self._plot_summary(fig)
        
        # Add statistics text
        stats_text = self._format_statistics(stats)
        stats_label = QLabel(stats_text)
        layout.addWidget(stats_label)
        
        return tab
        
    def _create_plots_tab(self):
        """Create frame-by-frame analysis plots."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        fig = Figure(figsize=(10, 8))
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        
        # Create subplots
        gs = fig.add_gridspec(2, 1)
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
        
        # Plot frame-by-frame data
        self._plot_frame_analysis(ax1, ax2)
        
        fig.tight_layout()
        canvas.draw()
        
        return tab
        
    def _create_correlation_tab(self):
        """Create correlation analysis view."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        fig = Figure(figsize=(10, 8))
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        
        # Plot correlation data
        self._plot_correlation_analysis(fig)
        
        canvas.draw()
        
        return tab
        
    def _create_export_section(self):
        """Create export buttons layout."""
        export_layout = QHBoxLayout()
        
        # CSV Export
        csv_button = QPushButton("Export CSV")
        csv_button.clicked.connect(self.export_csv)
        export_layout.addWidget(csv_button)
        
        # Excel Export
        excel_button = QPushButton("Export Excel")
        excel_button.clicked.connect(self.export_excel)
        export_layout.addWidget(excel_button)
        
        # Figure Export
        figures_button = QPushButton("Export Figures")
        figures_button.clicked.connect(self.export_figures)
        export_layout.addWidget(figures_button)
        
        return export_layout
        
    def _calculate_summary_statistics(self):
        """Calculate summary statistics for all measurements."""
        stats = {
            'curvature_mean': np.mean([np.mean(c) for c in self.all_curvatures]),
            'curvature_std': np.std([np.mean(c) for c in self.all_curvatures]),
            'intensity_mean': np.mean([np.mean(i) for i in self.all_intensities]),
            'intensity_std': np.std([np.mean(i) for i in self.all_intensities]),
            'correlation_mean': np.mean(self.all_correlations),
            'correlation_std': np.std(self.all_correlations),
            'n_frames': len(self.all_curvatures)
        }
        return stats
        
    def _format_statistics(self, stats):
        """Format statistics for display."""
        return f"""
        Summary Statistics:
        ------------------
        Curvature: {stats['curvature_mean']:.3f} ± {stats['curvature_std']:.3f} nm⁻¹
        Intensity: {stats['intensity_mean']:.1f} ± {stats['intensity_std']:.1f} a.u.
        Correlation: {stats['correlation_mean']:.3f} ± {stats['correlation_std']:.3f}
        
        Total Frames Analyzed: {stats['n_frames']}
        """
        
    def _plot_summary(self, fig):
        """Create summary plots."""
        gs = fig.add_gridspec(1, 2)
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])
        
        # Plot distributions
        ax1.hist([np.mean(c) for c in self.all_curvatures], bins=20)
        ax1.set_xlabel('Mean Curvature (nm⁻¹)')
        ax1.set_ylabel('Count')
        
        ax2.hist([np.mean(i) for i in self.all_intensities], bins=20)
        ax2.set_xlabel('Mean Intensity (a.u.)')
        ax2.set_ylabel('Count')
        
        fig.tight_layout()
        
    def _plot_frame_analysis(self, ax1, ax2):
        """Plot frame-by-frame analysis."""
        frames = range(len(self.all_curvatures))
        
        # Plot mean curvature per frame
        curvature_means = [np.mean(c) for c in self.all_curvatures]
        ax1.plot(frames, curvature_means, 'b-')
        ax1.set_ylabel('Mean Curvature (nm⁻¹)')
        
        # Plot mean intensity per frame
        intensity_means = [np.mean(i) for i in self.all_intensities]
        ax2.plot(frames, intensity_means, 'r-')
        ax2.set_ylabel('Mean Intensity (a.u.)')
        ax2.set_xlabel('Frame Number')
        
    def _plot_correlation_analysis(self, fig):
        """Plot correlation analysis."""
        ax = fig.add_subplot(111)
        
        # Combine all frame data
        all_curvatures = np.concatenate(self.all_curvatures)
        all_intensities = np.concatenate(self.all_intensities)
        
        # Create scatter plot
        ax.scatter(all_curvatures, all_intensities, alpha=0.5)
        ax.set_xlabel('Curvature (nm⁻¹)')
        ax.set_ylabel('Intensity (a.u.)')
        
        # Add trend line
        z = np.polyfit(all_curvatures, all_intensities, 1)
        p = np.poly1d(z)
        x_range = np.linspace(min(all_curvatures), max(all_curvatures), 100)
        ax.plot(x_range, p(x_range), 'r--', alpha=0.8)
        
        # Add correlation coefficient
        corr = np.corrcoef(all_curvatures, all_intensities)[0, 1]
        ax.set_title(f'Curvature vs Intensity (r = {corr:.3f})')
        
    def export_csv(self):
        """Export data to CSV file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV files (*.csv)")
            
        if filename:
            data = {
                'Frame': [],
                'Curvature': [],
                'Intensity': [],
                'Correlation': []
            }
            
            for i in range(len(self.all_curvatures)):
                data['Frame'].extend([i] * len(self.all_curvatures[i]))
                data['Curvature'].extend(self.all_curvatures[i])
                data['Intensity'].extend(self.all_intensities[i])
                data['Correlation'].extend([self.all_correlations[i]] * len(self.all_curvatures[i]))
                
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            
    def export_excel(self):
        """Export data to Excel file with multiple sheets."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Excel", "", "Excel files (*.xlsx)")
            
        if filename:
            with pd.ExcelWriter(filename) as writer:
                # Raw data sheet
                raw_data = {
                    'Frame': [],
                    'Curvature': [],
                    'Intensity': [],
                    'Correlation': []
                }
                
                for i in range(len(self.all_curvatures)):
                    raw_data['Frame'].extend([i] * len(self.all_curvatures[i]))
                    raw_data['Curvature'].extend(self.all_curvatures[i])
                    raw_data['Intensity'].extend(self.all_intensities[i])
                    raw_data['Correlation'].extend([self.all_correlations[i]] * len(self.all_curvatures[i]))
                    
                pd.DataFrame(raw_data).to_excel(writer, sheet_name='Raw Data', index=False)
                
                # Summary statistics sheet
                stats = self._calculate_summary_statistics()
                pd.DataFrame([stats]).to_excel(writer, sheet_name='Summary Stats')
                
                # Frame statistics sheet
                frame_stats = {
                    'Frame': range(len(self.all_curvatures)),
                    'Mean Curvature': [np.mean(c) for c in self.all_curvatures],
                    'Mean Intensity': [np.mean(i) for i in self.all_intensities],
                    'Correlation': self.all_correlations
                }
                pd.DataFrame(frame_stats).to_excel(writer, sheet_name='Frame Stats', index=False)
                
    def export_figures(self):
        """Export figures in publication-ready format."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory for Figures")
            
        if directory:
            # Export summary figure
            fig = Figure(figsize=(10, 6))
            self._plot_summary(fig)
            fig.savefig(f"{directory}/summary_plots.png", dpi=300, bbox_inches='tight')
            
            # Export frame analysis figure
            fig = Figure(figsize=(10, 8))
            gs = fig.add_gridspec(2, 1)
            ax1 = fig.add_subplot(gs[0])
            ax2 = fig.add_subplot(gs[1])
            self._plot_frame_analysis(ax1, ax2)
            fig.savefig(f"{directory}/frame_analysis.png", dpi=300, bbox_inches='tight')
            
            # Export correlation figure
            fig = Figure(figsize=(10, 8))
            self._plot_correlation_analysis(fig)
            fig.savefig(f"{directory}/correlation_analysis.png", dpi=300, bbox_inches='tight')