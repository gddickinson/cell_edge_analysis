import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from scipy.stats import pearsonr
from sklearn.cluster import KMeans
import pandas as pd

def multi_scale_consistency(contour, min_segment=5, max_segment=25, step=2):
    """
    Analyze curvature across multiple scales and identify consistent features.

    Parameters:
    -----------
    contour : ndarray
        Array of contour points (x, y)
    min_segment : int
        Minimum segment length to analyze
    max_segment : int
        Maximum segment length to analyze
    step : int
        Step size between segment lengths

    Returns:
    --------
    consistency_map : ndarray
        Consistency score for each point (higher = more consistent across scales)
    scale_curvatures : dict
        Dictionary of curvatures at each scale
    robust_curvature : ndarray
        Curvature values that are consistent across scales
    """
    # Generate segment lengths to test
    segment_lengths = list(range(min_segment, max_segment, step))

    # Ensure segment_lengths is not empty
    if not segment_lengths:
        print("Warning: Invalid segment length range, using default values")
        segment_lengths = [min(min_segment, 5)]

    # Calculate curvature at each scale
    scale_curvatures = {}
    for segment_length in segment_lengths:
        curvatures = calculate_curvature(contour, segment_length)
        scale_curvatures[segment_length] = curvatures

    # Convert to array for easier analysis
    curvature_array = np.array([scale_curvatures[s] for s in segment_lengths])

    # Handle NaN values in curvature array
    nan_mask = np.isnan(curvature_array)
    if np.any(nan_mask):
        print(f"Warning: {np.sum(nan_mask)} NaN values found across all scales, replacing with zeros")
        curvature_array = np.nan_to_num(curvature_array, nan=0.0)

    # Initialize consistency map
    consistency_map = np.zeros(len(contour))
    scale_correlation = np.zeros((len(segment_lengths), len(segment_lengths)))

    # Calculate correlation between scales - handle errors
    for i, s1 in enumerate(segment_lengths):
        for j, s2 in enumerate(segment_lengths):
            if i != j:
                try:
                    # Calculate correlation between scales with NaN handling
                    mask = ~(np.isnan(scale_curvatures[s1]) | np.isnan(scale_curvatures[s2]))
                    if np.sum(mask) > 2:  # Need at least 3 points for correlation
                        corr, _ = pearsonr(scale_curvatures[s1][mask], scale_curvatures[s2][mask])
                        scale_correlation[i, j] = corr if not np.isnan(corr) else 0.0
                    else:
                        scale_correlation[i, j] = 0.0
                except (ValueError, RuntimeWarning, FloatingPointError):
                    # If correlation fails, default to zero
                    scale_correlation[i, j] = 0.0

    # Calculate point-wise consistency (standard deviation across scales)
    # Handle cases with few scales
    if curvature_array.shape[0] > 1:
        consistency = np.std(curvature_array, axis=0)
        # Avoid division by zero
        consistency = 1.0 / (consistency + 1e-10)
    else:
        consistency = np.ones(len(contour))

    # Normalize to 0-1 range, handling all-zero case
    consistency_range = np.max(consistency) - np.min(consistency)
    if consistency_range > 0:
        consistency_map = (consistency - np.min(consistency)) / consistency_range
    else:
        consistency_map = np.ones_like(consistency) * 0.5  # Default mid-value

    # Generate robust curvature estimate (weighted average based on consistency)
    # Initialize weights
    weights = np.ones_like(curvature_array)

    # Calculate weights based on segment length and curvature magnitude
    for i, s in enumerate(segment_lengths):
        # Get curvature magnitude for this scale
        curvature_magnitude = np.abs(scale_curvatures[s])
        max_magnitude = np.max(curvature_magnitude) if np.max(curvature_magnitude) > 0 else 1.0

        if s < np.mean(segment_lengths):
            # For small segments, reduce weight in low curvature regions
            weights[i] = 1.0 + curvature_magnitude / max_magnitude
        else:
            # For large segments, reduce weight in high curvature regions
            weights[i] = 2.0 - curvature_magnitude / max_magnitude

    # Normalize weights - handle all zero case
    weights_sum = np.sum(weights, axis=0)
    mask = weights_sum > 0
    if np.any(mask):
        weights[:, mask] = weights[:, mask] / weights_sum[mask]

    # Calculate weighted average curvature
    robust_curvature = np.sum(curvature_array * weights, axis=0)

    # Final NaN check for all outputs
    consistency_map = np.nan_to_num(consistency_map, nan=0.5)
    robust_curvature = np.nan_to_num(robust_curvature, nan=0.0)

    return consistency_map, scale_curvatures, robust_curvature, scale_correlation

def calculate_curvature(points, segment_length):
    """Calculate curvature at each sample point using circular arc fitting."""
    curvatures = []
    n_points = len(points)
    half_segment = segment_length // 2

    for idx in range(n_points):
        # Get segment centered on current position
        indices = np.arange(idx - half_segment, idx + half_segment + 1) % n_points
        segment = points[indices]

        try:
            # Center the segment
            center = segment.mean(axis=0)
            centered = segment - center

            # Apply smoothing
            x_smoothed = gaussian_filter1d(centered[:, 0], 1.0)
            y_smoothed = gaussian_filter1d(centered[:, 1], 1.0)
            centered = np.column_stack([x_smoothed, y_smoothed])

            # Fit circle using algebraic least squares
            x = centered[:, 0]
            y = centered[:, 1]
            z = x*x + y*y
            ZXY = np.column_stack((z, x, y))
            A = np.dot(ZXY.T, ZXY)
            B = np.array([[4, 0, 0], [0, 1, 0], [0, 0, 1]])

            # Avoid division by zero or near-zero
            try:
                # Solve eigenvalue problem
                eigenvalues, eigenvectors = np.linalg.eig(np.dot(np.linalg.inv(B), A))

                # Get eigenvector for smallest eigenvalue
                v = eigenvectors[:, np.argmin(eigenvalues)]

                # Check if v[0] is near zero - avoid division by near zero
                if abs(v[0]) < 1e-10:
                    raise ValueError("Division by near-zero value")

                # Calculate circle parameters
                a = -v[1]/(2*v[0])
                b = -v[2]/(2*v[0])

                # Check for valid v[2] before division
                if abs(v[2]) < 1e-10:
                    raise ValueError("Division by near-zero value in radius calculation")

                r = np.sqrt(a*a + b*b - v[0]/v[2])

                # Verify radius is reasonable
                if r < 1e-3 or not np.isfinite(r):
                    raise ValueError("Invalid radius value")

                # Calculate curvature (1/r) with sign
                curvature = 1/r

                # Determine sign based on normal direction
                center_of_curvature = np.array([a, b]) + center
                # Vector from point to center of circle
                vec_to_center = center_of_curvature - points[idx]
                # Vector from point to center of shape (approximate)
                vec_to_origin = points[idx] - np.mean(points, axis=0)

                # If these vectors point in same direction, curvature is positive (inward)
                if np.dot(vec_to_center, vec_to_origin) > 0:
                    curvature = abs(curvature)
                else:
                    curvature = -abs(curvature)
            except (ValueError, ZeroDivisionError, np.linalg.LinAlgError):
                # Any linear algebra error or division by zero results in zero curvature
                curvature = 0

        except (ValueError, ZeroDivisionError, np.linalg.LinAlgError) as e:
            curvature = 0

        curvatures.append(curvature)

    return np.array(curvatures)

def identify_membrane_regions(contour, curvatures, consistency, n_regions=5):
    """
    Identify distinct regions of the membrane based on curvature patterns.

    Parameters:
    -----------
    contour : ndarray
        Array of contour points (x, y)
    curvatures : ndarray
        Curvature values for each point
    consistency : ndarray
        Consistency scores for each point
    n_regions : int
        Number of regions to identify

    Returns:
    --------
    regions : ndarray
        Region labels for each point
    region_stats : DataFrame
        Statistical summary of each region
    """
    # Handle NaN values in curvatures
    curvature_valid = np.copy(curvatures)
    nan_mask = np.isnan(curvature_valid)
    if np.any(nan_mask):
        print(f"Warning: {np.sum(nan_mask)} NaN values found in curvature data, replacing with zeros")
        curvature_valid[nan_mask] = 0.0

    # Handle NaN values in consistency
    consistency_valid = np.copy(consistency)
    nan_mask = np.isnan(consistency_valid)
    if np.any(nan_mask):
        print(f"Warning: {np.sum(nan_mask)} NaN values found in consistency data, replacing with zeros")
        consistency_valid[nan_mask] = 0.0

    # Create feature matrix: position, curvature, consistency
    # Convert contour position to angle from center
    center = np.mean(contour, axis=0)
    angles = np.arctan2(contour[:,1] - center[1], contour[:,0] - center[0])

    # Add distance from center as a feature
    distances = np.sqrt(np.sum((contour - center)**2, axis=1))
    # Check for valid min/max before normalization
    dist_min, dist_max = np.min(distances), np.max(distances)
    if dist_max > dist_min:
        distances = (distances - dist_min) / (dist_max - dist_min)
    else:
        distances = np.zeros_like(distances)

    # Create feature matrix
    features = np.column_stack([
        np.cos(angles),      # x position on unit circle
        np.sin(angles),      # y position on unit circle
        distances,           # normalized distance from center
        curvature_valid,     # curvature value (NaN-free)
        consistency_valid    # consistency score (NaN-free)
    ])

    # Normalize features - check for zero standard deviation first
    feature_means = np.mean(features, axis=0)
    feature_stds = np.std(features, axis=0)

    # Replace zero standard deviations with 1 to avoid division by zero
    feature_stds = np.where(feature_stds < 1e-10, 1.0, feature_stds)

    # Normalize features
    features_normalized = (features - feature_means) / feature_stds

    # Final check for any remaining NaN or infinite values
    features_normalized = np.nan_to_num(features_normalized, nan=0.0, posinf=0.0, neginf=0.0)

    # Apply clustering
    kmeans = KMeans(n_clusters=n_regions, random_state=42, n_init=10)
    regions = kmeans.fit_predict(features_normalized)

    # Calculate statistics for each region
    region_stats = []
    for i in range(n_regions):
        mask = regions == i
        if np.sum(mask) > 0:
            # Use the original curvatures for statistics but handle NaN values
            region_curvatures = curvatures[mask]
            region_curvatures_clean = region_curvatures[~np.isnan(region_curvatures)]

            # If all values are NaN, use zeros
            if len(region_curvatures_clean) == 0:
                region_curvatures_clean = np.zeros(1)

            stats = {
                'region_id': i,
                'size': np.sum(mask),
                'mean_curvature': np.mean(region_curvatures_clean),
                'std_curvature': np.std(region_curvatures_clean),
                'min_curvature': np.min(region_curvatures_clean),
                'max_curvature': np.max(region_curvatures_clean),
                'mean_consistency': np.mean(consistency_valid[mask]),
                'contour_indices': np.where(mask)[0].tolist()  # Convert to list for serialization
            }
            region_stats.append(stats)

    return regions, pd.DataFrame(region_stats)

def analyze_membrane_dynamics(contours, times=None, scale_factor=1.0):
    """
    Analyze membrane dynamics across multiple time points.

    Parameters:
    -----------
    contours : list
        List of contour arrays for each time point
    times : ndarray or None
        Time points for each contour
    scale_factor : float
        Conversion factor from pixels to physical units

    Returns:
    --------
    dynamics : DataFrame
        Membrane dynamics metrics for each time point
    region_tracking : list
        Tracked regions across time points
    """
    if times is None:
        times = np.arange(len(contours))

    # Analysis results for each time point
    dynamics = []
    all_regions = []

    # Analyze each time point
    for t, contour in zip(times, contours):
        # Multi-scale analysis
        consistency, scale_curvatures, robust_curvature, _ = multi_scale_consistency(contour)

        # Region identification
        regions, region_stats = identify_membrane_regions(contour, robust_curvature, consistency)

        # Store region information
        region_stats['time'] = t
        all_regions.append(region_stats)

        # Calculate membrane activity metrics
        metrics = {
            'time': t,
            'mean_curvature': np.mean(robust_curvature),
            'curvature_std': np.std(robust_curvature),
            'positive_curvature_area': np.sum(robust_curvature > 0) / len(robust_curvature),
            'negative_curvature_area': np.sum(robust_curvature < 0) / len(robust_curvature),
            'high_curvature_regions': np.sum(np.abs(robust_curvature) > np.std(robust_curvature)),
            'mean_consistency': np.mean(consistency),
            'contour_length': len(contour) * scale_factor,
            'contour_complexity': np.sum(np.abs(np.diff(robust_curvature)))
        }
        dynamics.append(metrics)

    # Create dynamics DataFrame
    dynamics_df = pd.DataFrame(dynamics)

    # Track regions across time points (if multiple time points)
    region_tracking = None
    if len(contours) > 1:
        # Implementation of region tracking would go here
        # This would match regions between time points based on position and curvature
        region_tracking = []

    return dynamics_df, all_regions, region_tracking

def visualize_multi_scale_analysis(image, contour, scale_curvatures, consistency, robust_curvature):
    """Visualize the multi-scale curvature analysis results."""
    n_scales = len(scale_curvatures)

    # Create figure with subplots for each scale plus consistency and robust estimate
    fig = plt.figure(figsize=(15, 10))

    # Main subplot for consistency map
    ax_main = plt.subplot2grid((3, 4), (0, 0), colspan=2, rowspan=2)
    ax_main.imshow(image, cmap='gray')

    # Plot contour with consistency coloring
    points = np.array(range(len(contour)))
    ax_main.scatter(contour[:, 0], contour[:, 1], c=consistency, cmap='viridis',
                   s=10, alpha=0.7)

    # Add colorbar
    cbar = plt.colorbar(ax_main.collections[0], ax=ax_main)
    cbar.set_label('Consistency across scales')
    ax_main.set_title('Membrane Consistency Map')

    # Robust curvature subplot
    ax_robust = plt.subplot2grid((3, 4), (0, 2), colspan=2, rowspan=2)
    ax_robust.imshow(image, cmap='gray')

    # Create symmetric colormap around zero for curvature
    max_abs_curv = max(abs(np.min(robust_curvature)), abs(np.max(robust_curvature)))
    norm = plt.Normalize(vmin=-max_abs_curv, vmax=max_abs_curv)

    # Plot contour with curvature coloring
    robust_points = ax_robust.scatter(contour[:, 0], contour[:, 1],
                                    c=robust_curvature, cmap='coolwarm',
                                    norm=norm, s=10, alpha=0.7)

    # Add colorbar
    cbar_robust = plt.colorbar(robust_points, ax=ax_robust)
    cbar_robust.set_label('Robust Curvature Estimate')
    ax_robust.set_title('Multi-Scale Robust Curvature')

    # Subplots for individual scales
    scale_axes = []
    scale_values = sorted(scale_curvatures.keys())
    for i, scale in enumerate(scale_values):
        if i < 4:  # Show up to 4 scales
            ax_scale = plt.subplot2grid((3, 4), (2, i))
            scale_axes.append(ax_scale)

            # Show curvature at this scale
            curvatures = scale_curvatures[scale]
            scale_points = ax_scale.scatter(contour[:, 0], contour[:, 1],
                                           c=curvatures, cmap='coolwarm',
                                           norm=norm, s=5, alpha=0.7)

            ax_scale.set_title(f'Segment Length: {scale}')
            ax_scale.axis('equal')

    # Adjust layout
    plt.tight_layout()
    return fig

def visualize_membrane_regions(image, contour, regions, region_stats):
    """Visualize the identified membrane regions."""
    fig, ax = plt.subplots(figsize=(10, 8))

    # Display image
    ax.imshow(image, cmap='gray')

    # Create colormap for regions
    unique_regions = np.unique(regions)
    colors = plt.cm.tab10(np.linspace(0, 1, len(unique_regions)))

    # Plot contour with region coloring
    for i, r in enumerate(unique_regions):
        mask = regions == r
        ax.scatter(contour[mask, 0], contour[mask, 1], color=colors[i],
                  s=20, alpha=0.7, label=f'Region {r}')

    # Add region labels at centroid of each region
    for _, row in region_stats.iterrows():
        region_id = row['region_id']
        indices = row['contour_indices']
        centroid = np.mean(contour[indices], axis=0)
        ax.text(centroid[0], centroid[1], str(region_id),
               color='white', fontsize=12, ha='center', va='center',
               bbox=dict(facecolor='black', alpha=0.7, boxstyle='round'))

    # Add legend
    ax.legend(title='Membrane Regions')
    ax.set_title('Identified Membrane Regions')

    return fig
