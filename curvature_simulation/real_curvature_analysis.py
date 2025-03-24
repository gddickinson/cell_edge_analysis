import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter, gaussian_filter1d
from skimage import measure, filters
from skimage.segmentation import active_contour
import pandas as pd

class MembraneCurvatureAnalyzer:
    """Analyze membrane curvature in microscopy images."""

    def __init__(self):
        # Parameters for curvature analysis
        self.base_segment_length = 9
        self.n_samples = 75
        self.smoothing_sigma = 1.0
        self.scale_factor = 100  # nm per pixel
        self.membrane_thickness = 4  # nm

        # Reference curvatures (in nm^-1)
        self.ref_curvatures = {
            'plasma_membrane': 1/(10000),  # typical plasma membrane
            'transport_vesicle': 1/(40),   # typical transport vesicle
            'endocytic_vesicle': 1/(100)   # typical endocytic vesicle
        }

    def extract_membrane(self, image, method='threshold'):
        """Extract cell membrane from microscopy image."""
        # Apply preprocessing
        blurred = gaussian_filter(image, sigma=1.0)

        if method == 'threshold':
            # Simple thresholding
            threshold = filters.threshold_otsu(blurred)
            binary = blurred > threshold
            contours = measure.find_contours(binary, 0.5)
            if not contours:
                raise ValueError("No contours found in the image")
            # Select largest contour
            contour = max(contours, key=len)

            # IMPORTANT: skimage contours are in (row, col) format, but we need (x, y) = (col, row)
            # Swap coordinates to convert from (row, col) to (x, y)
            contour = np.fliplr(contour)

        elif method == 'active_contour':
            # Initialize contour as a circle in the middle
            y, x = np.indices(image.shape)
            cy, cx = np.mean(y[blurred > filters.threshold_otsu(blurred)]), np.mean(x[blurred > filters.threshold_otsu(blurred)])
            r = np.sqrt(np.sum(blurred > filters.threshold_otsu(blurred))) / 3
            theta = np.linspace(0, 2*np.pi, 100)
            initial = np.array([cx + r*np.cos(theta), cy + r*np.sin(theta)]).T

            # Snake parameters
            contour = active_contour(
                filters.gaussian(blurred, 3),
                initial,
                alpha=0.015,  # Elasticity
                beta=10,      # Rigidity
                gamma=0.001   # Step size
            )
        else:
            raise ValueError(f"Unknown membrane extraction method: {method}")

        return contour

    def resample_contour(self, contour, n_samples=None):
        """Resample contour to have equal arc-length spacing."""
        if n_samples is None:
            n_samples = self.n_samples

        # Calculate cumulative arc length
        dx = np.diff(contour[:, 0])
        dy = np.diff(contour[:, 1])
        arc_lengths = np.sqrt(dx**2 + dy**2)
        cumulative_arc = np.concatenate(([0], np.cumsum(arc_lengths)))

        # Generate equally spaced points
        total_length = cumulative_arc[-1]
        equal_spaced = np.linspace(0, total_length, n_samples)

        # Interpolate new points
        x_interp = np.interp(equal_spaced, cumulative_arc, contour[:, 0])
        y_interp = np.interp(equal_spaced, cumulative_arc, contour[:, 1])

        return np.column_stack((x_interp, y_interp))

    def calculate_curvature(self, points, segment_length=None):
        """Calculate curvature at each sample point using circular arc fitting."""
        if segment_length is None:
            segment_length = self.base_segment_length

        curvatures = []
        n_points = len(points)
        half_segment = segment_length // 2

        for idx in range(n_points):
            # Get segment of points centered on current position
            indices = np.arange(idx - half_segment, idx + half_segment + 1) % n_points
            segment = points[indices]

            try:
                # Translate segment to origin
                center = segment.mean(axis=0)
                centered = segment - center

                # Apply smoothing if enabled
                if self.smoothing_sigma > 0:
                    # Apply gaussian filter to each dimension separately
                    x_smoothed = gaussian_filter1d(centered[:, 0], self.smoothing_sigma)
                    y_smoothed = gaussian_filter1d(centered[:, 1], self.smoothing_sigma)
                    centered = np.column_stack([x_smoothed, y_smoothed])

                # Fit circle using algebraic least squares
                x = centered[:, 0]
                y = centered[:, 1]
                z = x*x + y*y
                ZXY = np.column_stack((z, x, y))
                A = np.dot(ZXY.T, ZXY)
                B = np.array([[4, 0, 0], [0, 1, 0], [0, 0, 1]])

                # Solve eigenvalue problem
                eigenvalues, eigenvectors = np.linalg.eig(np.dot(np.linalg.inv(B), A))

                # Get eigenvector corresponding to smallest eigenvalue
                v = eigenvectors[:, np.argmin(eigenvalues)]

                # Calculate center and radius of fitted circle
                a = -v[1]/(2*v[0])
                b = -v[2]/(2*v[0])
                r = np.sqrt(a*a + b*b - v[0]/v[2])

                # Verify the fit is reasonable
                if r > 1000 * np.mean(np.linalg.norm(points, axis=1)) or r < segment_length/2:
                    curvature = 0
                else:
                    # Calculate outward-pointing normal
                    segment_dir = segment[-1] - segment[0]
                    normal = np.array([-segment_dir[1], segment_dir[0]])
                    normal = normal / np.linalg.norm(normal)

                    # Determine if normal points outward (from cell center)
                    center_point = np.array([a, b]) + center
                    to_center = center_point - segment.mean(axis=0)
                    to_center_norm = np.linalg.norm(to_center)

                    if to_center_norm > 0:
                        # Curvature is positive when bulging inward (cytosol)
                        sign = -np.sign(np.dot(to_center/to_center_norm, normal))
                        curvature = (1/r) * sign
                        # Convert to nm^-1 units
                        curvature = curvature / self.scale_factor
                    else:
                        curvature = 0

            except (ValueError, ZeroDivisionError):
                curvature = 0

            curvatures.append(curvature)

        return np.array(curvatures)

    def multi_scale_analysis(self, points, min_segment=5, max_segment=21, step=2):
        """Analyze curvature across multiple segment lengths."""
        scales = range(min_segment, max_segment, step)
        results = {}

        for segment_length in scales:
            curvatures = self.calculate_curvature(points, segment_length)
            results[segment_length] = curvatures

        return results

    def curvature_confidence(self, points, segment_length=None, bootstrap_samples=100):
        """Calculate confidence intervals for curvature estimates."""
        if segment_length is None:
            segment_length = self.base_segment_length

        # First calculate curvature on original points
        base_curvatures = self.calculate_curvature(points, segment_length)

        # If bootstrap_samples is 0 or None, just return the base curvature without CI
        if not bootstrap_samples:
            return base_curvatures, base_curvatures, base_curvatures

        # Initialize arrays for bootstrap results
        results = []
        n_points = len(points)

        # Perform bootstrapping
        for i in range(bootstrap_samples):
            try:
                # Add small random noise to points
                noise_level = 0.5  # pixel level noise
                noisy_points = points + np.random.normal(0, noise_level, points.shape)

                # Calculate curvature with noise
                curvatures = self.calculate_curvature(noisy_points, segment_length)
                results.append(curvatures)
            except Exception as e:
                print(f"Warning: Bootstrap sample {i} failed: {e}")
                # Use the base curvature if this sample fails
                results.append(base_curvatures)

        # Calculate mean and confidence intervals
        results_array = np.array(results)
        mean_curvature = np.mean(results_array, axis=0)
        lower_ci = np.percentile(results_array, 2.5, axis=0)
        upper_ci = np.percentile(results_array, 97.5, axis=0)

        return mean_curvature, lower_ci, upper_ci

    def visualize_curvature(self, image, contour, curvatures, confidence=None):
        """Visualize the original image with curvature overlay."""
        fig, ax = plt.subplots(figsize=(10, 8))

        # Display original image
        ax.imshow(image, cmap='gray')

        # Create symmetric colorbar around zero
        max_abs_curvature = max(abs(np.min(curvatures)), abs(np.max(curvatures)))
        if max_abs_curvature < 1e-6:  # Avoid division by zero
            max_abs_curvature = 1e-6

        norm = plt.Normalize(vmin=-max_abs_curvature, vmax=max_abs_curvature)

        # Custom colormap (blue=negative/outward, red=positive/inward)
        colors = ['#0000FF', '#FFFFFF', '#FF0000']
        cmap = LinearSegmentedColormap.from_list('custom', colors)

        # Plot contour with curvature coloring - use proper point by point plotting
        for i in range(len(contour)):
            # For each point, draw a small segment centered on it
            # This ensures curvature is shown exactly at the analyzed position
            idx_next = (i + 1) % len(contour)
            center_point = contour[i]

            # Calculate the color based on curvature at this point
            color = cmap(norm(curvatures[i]))

            # Draw a small line segment centered at this point
            # This keeps the coloring directly on the cell contour
            segment = np.array([contour[i], contour[idx_next]])
            ax.plot(segment[:, 0], segment[:, 1], color=color, linewidth=2.5)

        # Plot confidence intervals if provided
        if confidence is not None:
            lower_ci, upper_ci = confidence
            for i in range(len(contour)):
                if abs(lower_ci[i] - upper_ci[i]) > 0.0001:
                    # Draw error bar for points with significant uncertainty
                    ci_range = upper_ci[i] - lower_ci[i]
                    # Cap the marker size to avoid enormous markers
                    marker_size = min(20, 2 + 8 * (ci_range / max_abs_curvature))
                    ax.plot(contour[i, 0], contour[i, 1], 'ko', markersize=marker_size)

        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        colorbar = fig.colorbar(sm, ax=ax, label='Curvature (nm⁻¹)')

        # Add reference lines for typical biological curvatures
        ref_colors = ['g', 'r', 'y']
        for (name, value), color in zip(self.ref_curvatures.items(), ref_colors):
            if abs(value) <= max_abs_curvature:
                colorbar.ax.axhline(y=value, color=color, linestyle='--', alpha=0.5)
                colorbar.ax.text(2.5, value, name.replace('_', ' '),
                               color=color, va='center', ha='left', fontsize=8)

        # Add h/R ratio scale if membrane thickness is defined
        if self.membrane_thickness > 0:
            ax2 = colorbar.ax.twinx()
            h_over_r = np.abs(self.membrane_thickness * np.array([-max_abs_curvature, 0, max_abs_curvature]))
            ax2.set_ylim(h_over_r[0], h_over_r[2])
            ax2.set_ylabel('h/R ratio')

        ax.set_title('Cell Membrane Curvature Analysis')
        return fig

    def analyze_image(self, image, extraction_method='threshold', multi_scale=False, bootstrap_samples=20):
        """Full analysis pipeline for a single image."""
        try:
            # Extract membrane
            contour = self.extract_membrane(image, method=extraction_method)

            # Check if contour is valid
            if len(contour) < 10:
                raise ValueError("Extracted contour is too small for reliable analysis")

            # Resample to equal spacing
            resampled = self.resample_contour(contour)

            if multi_scale:
                # Multi-scale analysis
                scale_results = self.multi_scale_analysis(resampled)

                # Visualize results at different scales
                figs = []
                for segment_length, curvatures in scale_results.items():
                    fig = self.visualize_curvature(image, resampled, curvatures)
                    fig.suptitle(f'Segment Length: {segment_length}')
                    figs.append(fig)
                return figs, scale_results
            else:
                # Single scale with confidence intervals
                print(f"Calculating curvature with bootstrap_samples={bootstrap_samples}")
                mean_curvature, lower_ci, upper_ci = self.curvature_confidence(
                    resampled, bootstrap_samples=bootstrap_samples
                )

                # Visualize results
                fig = self.visualize_curvature(image, resampled, mean_curvature,
                                             confidence=(lower_ci, upper_ci))

                # Create results dataframe
                results = pd.DataFrame({
                    'position': range(len(resampled)),
                    'x': resampled[:, 0],
                    'y': resampled[:, 1],
                    'curvature': mean_curvature,
                    'lower_ci': lower_ci,
                    'upper_ci': upper_ci
                })

                return fig, results

        except Exception as e:
            # Create a figure with the error message
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.imshow(image, cmap='gray')
            ax.set_title(f"Analysis failed: {str(e)}")

            # Return empty results
            results = pd.DataFrame(columns=['position', 'x', 'y', 'curvature', 'lower_ci', 'upper_ci'])

            print(f"Error during analysis: {str(e)}")
            return fig, results

# Example usage:
if __name__ == "__main__":
# =============================================================================
#     # Create test image with a circular cell
#     size = 512
#     center = size // 2
#     radius = 180
#
#     image = np.zeros((size, size))
#     y, x = np.ogrid[:size, :size]
#     dist_from_center = np.sqrt((x - center)**2 + (y - center)**2)
#     circle_mask = dist_from_center <= radius
#     image[circle_mask] = 1
#
#     # Add a bleb (small protrusion)
#     bleb_center_y, bleb_center_x = center - 30, center + 170
#     bleb_radius = 40
#
#     # Ensure bleb center is within image bounds
#     bleb_center_y = np.clip(bleb_center_y, 0, size-1)
#     bleb_center_x = np.clip(bleb_center_x, 0, size-1)
#
#     # Create bleb mask
#     bleb_distance = np.sqrt((x - bleb_center_x)**2 + (y - bleb_center_y)**2)
#     bleb_mask = bleb_distance <= bleb_radius
#     image[bleb_mask] = 1
# =============================================================================

    # Load your microscopy image
    image = plt.imread('/Users/george/Documents/python_projects/cell_edge_analysis/151_2019_07_29_TIRF_mKera_scratch_Pos7_DIC_Mask_test.tif')


    # Add noise
    image = image + np.random.normal(0, 0.05, image.shape)

    # Analyze
    analyzer = MembraneCurvatureAnalyzer()

    # For testing, use fewer bootstrap samples
    fig, results = analyzer.analyze_image(image, bootstrap_samples=10)

    # Print high curvature regions
    high_curvature = results[abs(results['curvature']) > 0.005]
    print(f"Found {len(high_curvature)} high curvature points")

    # Save the figure
    plt.savefig('curvature_analysis_result.png')
    print("Analysis complete - check curvature_analysis_result.png")

    # Show plot if running interactively
    plt.show()
