import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QSlider, QLabel, QGroupBox)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter1d

class BlebSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulated Bleb Curvature Analysis")

        # Parameters for the simulation
        self.radius = 100  # Base cell radius in arbitrary units
        self.bleb_size = 50  # Default bleb size
        self.bleb_pos = np.pi/4  # Position of the bleb
        self.bleb_width = np.pi/8  # Width of the bleb
        self.segment_length = 9  # Default segment length
        self.n_samples = 75  # Default number of samples
        self.smoothing_sigma = 1.0  # Default smoothing

        # Biological reference values (in nm)
        self.membrane_thickness = 4  # nm
        self.radius_scale = 100  # Scale factor to convert drawing units to nm

        # Reference curvatures
        self.ref_curvatures = {
            'plasma_membrane': 1/(10000),  # typical plasma membrane
            'transport_vesicle': 1/(40),   # typical transport vesicle
            'endocytic_vesicle': 1/(100)   # typical endocytic vesicle
        }

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Create matplotlib figure
        self.fig = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        # Create control panels
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)

        # Membrane shape controls
        shape_group = QGroupBox("Membrane Shape")
        shape_layout = QVBoxLayout()

        # Bleb size slider
        self.bleb_label = QLabel(f"Bleb Size: {self.bleb_size} (- inward, + outward)")
        self.bleb_slider = QSlider(Qt.Orientation.Horizontal)
        self.bleb_slider.setMinimum(-100)  # Allow negative values for inward blebs
        self.bleb_slider.setMaximum(100)
        self.bleb_slider.setValue(self.bleb_size)
        self.bleb_slider.valueChanged.connect(self.update_bleb_size)
        shape_layout.addWidget(self.bleb_label)
        shape_layout.addWidget(self.bleb_slider)

        # Bleb width slider
        self.width_label = QLabel(f"Bleb Width: {int(self.bleb_width*180/np.pi)}°")
        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setMinimum(5)
        self.width_slider.setMaximum(90)
        self.width_slider.setValue(int(self.bleb_width*180/np.pi))
        self.width_slider.valueChanged.connect(self.update_bleb_width)
        shape_layout.addWidget(self.width_label)
        shape_layout.addWidget(self.width_slider)

        shape_group.setLayout(shape_layout)
        controls_layout.addWidget(shape_group)

        # Analysis controls
        analysis_group = QGroupBox("Analysis Parameters")
        analysis_layout = QVBoxLayout()

        # Segment length slider
        self.segment_label = QLabel(f"Segment Length: {self.segment_length}")
        self.segment_slider = QSlider(Qt.Orientation.Horizontal)
        self.segment_slider.setMinimum(5)
        self.segment_slider.setMaximum(20)
        self.segment_slider.setValue(self.segment_length)
        self.segment_slider.valueChanged.connect(self.update_segment_length)
        analysis_layout.addWidget(self.segment_label)
        analysis_layout.addWidget(self.segment_slider)

        # Number of samples slider
        self.samples_label = QLabel(f"Number of Samples: {self.n_samples}")
        self.samples_slider = QSlider(Qt.Orientation.Horizontal)
        self.samples_slider.setMinimum(20)
        self.samples_slider.setMaximum(150)
        self.samples_slider.setValue(self.n_samples)
        self.samples_slider.valueChanged.connect(self.update_n_samples)
        analysis_layout.addWidget(self.samples_label)
        analysis_layout.addWidget(self.samples_slider)

        # Smoothing slider
        self.smoothing_label = QLabel(f"Smoothing σ: {self.smoothing_sigma:.1f}")
        self.smoothing_slider = QSlider(Qt.Orientation.Horizontal)
        self.smoothing_slider.setMinimum(0)
        self.smoothing_slider.setMaximum(50)
        self.smoothing_slider.setValue(int(self.smoothing_sigma * 10))
        self.smoothing_slider.valueChanged.connect(self.update_smoothing)
        analysis_layout.addWidget(self.smoothing_label)
        analysis_layout.addWidget(self.smoothing_slider)

        analysis_group.setLayout(analysis_layout)
        controls_layout.addWidget(analysis_group)

        # Add controls to main layout
        layout.addWidget(controls_widget)

        # Create custom colormap for curvature (red=positive/inward, blue=negative/outward)
        colors = ['#0000FF', '#FFFFFF', '#FF0000']  # Blue (outward) to White (flat) to Red (inward)
        self.curvature_cmap = LinearSegmentedColormap.from_list('custom', colors)

        # Initial plot
        self.update_plot()

    def generate_cell_outline(self):
        """Generate a cell outline with a bleb."""
        # Generate base circle
        t = np.linspace(0, 2*np.pi, 1000)
        x = self.radius * np.cos(t)
        y = self.radius * np.sin(t)

        # Add bleb using a more pronounced shape
        bleb_mask = np.abs(t - self.bleb_pos) < self.bleb_width/2

        # Create sharper bleb deformation with steeper sides
        bleb = abs(self.bleb_size) * (np.cos((t - self.bleb_pos)/(self.bleb_width/2) * np.pi) + 1) / 2
        bleb[~bleb_mask] = 0

        # Add bleb with tangential component
        # For inward blebs (negative size), we subtract instead of add
        angle = t[bleb_mask]
        sign = np.sign(self.bleb_size)  # Use sign to determine inward or outward
        x[bleb_mask] += sign * bleb[bleb_mask] * np.cos(angle)
        y[bleb_mask] += sign * bleb[bleb_mask] * np.sin(angle)

        # Smooth transition at bleb edges
        smooth_width = self.bleb_width/8
        edge_mask = (np.abs(t - (self.bleb_pos - self.bleb_width/2)) < smooth_width) | \
                   (np.abs(t - (self.bleb_pos + self.bleb_width/2)) < smooth_width)
        if np.any(edge_mask):
            points = np.column_stack((x, y))
            edge_indices = np.where(edge_mask)[0]
            for _ in range(2):
                points[edge_indices] = 0.25 * (points[(edge_indices-1)%len(points)] +
                                             2*points[edge_indices] +
                                             points[(edge_indices+1)%len(points)])
            x, y = points.T

        return np.column_stack((x, y))

    def calculate_curvature(self, points, segment_length):
        """Calculate curvature at each sample point using circular arc fitting."""
        curvatures = []
        n_points = len(points)
        half_segment = segment_length // 2

        # Generate evenly spaced sample points
        sample_indices = np.linspace(0, n_points-1, self.n_samples, dtype=int)

        for idx in sample_indices:
            # Get segment of points centered on current position
            indices = np.arange(idx - half_segment, idx + half_segment + 1) % n_points
            segment = points[indices]

            try:
                # Translate segment to origin
                center = segment.mean(axis=0)
                centered = segment - center

                # Apply smoothing if enabled
                if self.smoothing_sigma > 0:
                    centered = gaussian_filter1d(centered, self.smoothing_sigma, axis=0)

                # Fit circle using algebraic least squares
                x = centered[:, 0]
                y = centered[:, 1]
                z = x*x + y*y
                ZXY = np.column_stack((z, x, y))
                A = np.dot(ZXY.T, ZXY)
                B = np.array([[4, 0, 0], [0, 1, 0], [0, 0, 1]])
                eigenvalues, eigenvectors = np.linalg.eig(np.dot(np.linalg.inv(B), A))

                # Get eigenvector corresponding to smallest eigenvalue
                v = eigenvectors[:, np.argmin(eigenvalues)]

                # Calculate center and radius of fitted circle
                a = -v[1]/(2*v[0])
                b = -v[2]/(2*v[0])
                r = np.sqrt(a*a + b*b - v[0]/v[2])

                # Verify the fit is reasonable
                if r > 1000 * self.radius or r < self.segment_length/2:
                    curvature = 0
                else:
                    # Calculate outward-pointing normal
                    segment_dir = segment[-1] - segment[0]
                    normal = np.array([-segment_dir[1], segment_dir[0]])
                    normal = normal / np.linalg.norm(normal)

                    # Determine if normal points outward
                    center_point = np.array([a, b]) + center
                    to_center = center_point - segment.mean(axis=0)
                    to_center_norm = np.linalg.norm(to_center)

                    if to_center_norm > 0:
                        # Curvature is positive when bulging inward (cytosol)
                        sign = -np.sign(np.dot(to_center/to_center_norm, normal))
                        curvature = (1/r) * sign
                        # Convert to nm^-1 units
                        curvature = curvature / self.radius_scale
                    else:
                        curvature = 0

            except (ValueError, ZeroDivisionError):
                curvature = 0

            curvatures.append(curvature)

        return np.array(curvatures)

    def update_plot(self):
        """Update the visualization."""
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        # Generate and plot cell outline
        points = self.generate_cell_outline()

        # Calculate curvature
        curvatures = self.calculate_curvature(points, self.segment_length)

        # Plot segments with curvature coloring
        n_points = len(points)
        sample_indices = np.linspace(0, n_points-1, self.n_samples, dtype=int)

        # Create symmetric colorbar around zero
        max_abs_curvature = max(abs(np.min(curvatures)), abs(np.max(curvatures)))
        norm = plt.Normalize(vmin=-max_abs_curvature, vmax=max_abs_curvature)

        for i, (idx, curvature) in enumerate(zip(sample_indices, curvatures)):
            # Calculate segment indices ensuring they wrap around properly
            segment_indices = np.arange(idx - self.segment_length//2,
                                      idx + self.segment_length//2 + 1) % n_points
            segment = points[segment_indices]
            color = self.curvature_cmap(norm(curvature))

            # Plot segment
            ax.plot(segment[:, 0], segment[:, 1], color=color, linewidth=2)

            # Plot sample point
            ax.plot(points[idx, 0], points[idx, 1], 'k.', markersize=4)

        # Add colorbar with reference values
        sm = plt.cm.ScalarMappable(cmap=self.curvature_cmap, norm=norm)
        colorbar = self.fig.colorbar(sm, ax=ax, label='Curvature (nm⁻¹)')

        # Add reference lines for typical biological curvatures
        ref_colors = ['g', 'r', 'y']
        for (name, value), color in zip(self.ref_curvatures.items(), ref_colors):
            if abs(value) <= max_abs_curvature:
                colorbar.ax.axhline(y=value, color=color, linestyle='--', alpha=0.5)
                colorbar.ax.text(2.5, value, name.replace('_', ' '),
                               color=color, va='center', ha='left')

        # Add h/R ratio scale
        ax2 = colorbar.ax.twinx()
        h_over_r = np.abs(self.membrane_thickness * np.array([-max_abs_curvature, 0, max_abs_curvature]))
        ax2.set_ylim(h_over_r[0], h_over_r[2])
        ax2.set_ylabel('h/R ratio')

        ax.set_title('Simulated Cell with Bleb - Curvature Analysis')
        ax.set_aspect('equal')
        self.canvas.draw()

    def update_bleb_size(self, value):
        """Update bleb size parameter."""
        self.bleb_size = value
        direction = "inward" if value < 0 else "outward"
        self.bleb_label.setText(f"Bleb Size: {value} ({direction})")
        self.update_plot()

    def update_bleb_width(self, value):
        """Update bleb width parameter."""
        self.bleb_width = value * np.pi/180
        self.width_label.setText(f"Bleb Width: {value}°")
        self.update_plot()

    def update_segment_length(self, value):
        """Update segment length parameter."""
        self.segment_length = value
        self.segment_label.setText(f"Segment Length: {value}")
        self.update_plot()

    def update_n_samples(self, value):
        """Update number of samples parameter."""
        self.n_samples = value
        self.samples_label.setText(f"Number of Samples: {value}")
        self.update_plot()

    def update_smoothing(self, value):
        """Update smoothing parameter."""
        self.smoothing_sigma = value / 10
        self.smoothing_label.setText(f"Smoothing σ: {self.smoothing_sigma:.1f}")
        self.update_plot()

def main():
    app = QApplication([])
    window = BlebSimulator()
    window.resize(1200, 1000)
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
