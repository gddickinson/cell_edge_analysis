import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from skimage import measure, filters
from scipy.ndimage import gaussian_filter
import pandas as pd
from multi_scale_curvature import (
    multi_scale_consistency, 
    identify_membrane_regions,
    visualize_multi_scale_analysis,
    visualize_membrane_regions
)

class MembraneDynamicsAnalyzer:
    """Analyze membrane dynamics from time-series microscopy images."""
    
    def __init__(self, scale_factor=100, min_segment=5, max_segment=25, step=2):
        """
        Initialize the analyzer.
        
        Parameters:
        -----------
        scale_factor : float
            Conversion factor from pixels to nm
        min_segment : int
            Minimum segment length to analyze
        max_segment : int
            Maximum segment length to analyze
        step : int
            Step size between segment lengths
        """
        self.scale_factor = scale_factor
        self.min_segment = min_segment
        self.max_segment = max_segment
        self.step = step
        
        # Reference curvatures (in nm^-1)
        self.ref_curvatures = {
            'plasma_membrane': 1/(10000),  # typical plasma membrane
            'transport_vesicle': 1/(40),   # typical transport vesicle
            'endocytic_vesicle': 1/(100)   # typical endocytic vesicle
        }
    
    def extract_contours_from_images(self, images):
        """
        Extract cell contours from a sequence of images.
        
        Parameters:
        -----------
        images : list or ndarray
            Sequence of images (time series)
            
        Returns:
        --------
        contours : list
            List of contour arrays for each time point
        """
        contours = []
        
        for i, image in enumerate(images):
            # Apply preprocessing
            blurred = gaussian_filter(image, sigma=1.0)
            
            # Simple thresholding
            threshold = filters.threshold_otsu(blurred)
            binary = blurred > threshold
            
            # Find contours
            found_contours = measure.find_contours(binary, 0.5)
            if not found_contours:
                print(f"Warning: No contours found in image {i}")
                # Use previous contour if available, otherwise skip
                if contours:
                    contours.append(contours[-1])
                continue
            
            # Select largest contour
            contour = max(found_contours, key=len)
            
            # Swap coordinates to convert from (row, col) to (x, y)
            contour = np.fliplr(contour)
            
            # Resample to have equal spacing
            contour = self.resample_contour(contour)
            
            contours.append(contour)
        
        return contours
    
    def resample_contour(self, contour, n_samples=100):
        """Resample contour to have equal arc-length spacing."""
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
    
    def analyze_time_series(self, images, times=None):
        """
        Analyze membrane dynamics from a time series of images.
        
        Parameters:
        -----------
        images : list or ndarray
            Sequence of images (time series)
        times : ndarray or None
            Time points for each image (if None, uses indices)
            
        Returns:
        --------
        results : dict
            Dictionary of analysis results including:
            - contours: list of contour arrays
            - dynamics: DataFrame of dynamics metrics
            - regions: list of region DataFrames
            - consistency: list of consistency arrays
            - robust_curvature: list of robust curvature arrays
        """
        if times is None:
            times = np.arange(len(images))
        
        # Extract contours
        contours = self.extract_contours_from_images(images)
        
        # Analysis results
        all_consistency = []
        all_scale_curvatures = []
        all_robust_curvature = []
        all_scale_correlations = []
        all_regions = []
        all_region_stats = []
        
        # Analyze each time point
        for contour in contours:
            # Multi-scale analysis
            consistency, scale_curvatures, robust_curvature, scale_correlation = \
                multi_scale_consistency(contour, self.min_segment, self.max_segment, self.step)
            
            # Region identification
            regions, region_stats = identify_membrane_regions(contour, robust_curvature, consistency)
            
            # Store results
            all_consistency.append(consistency)
            all_scale_curvatures.append(scale_curvatures)
            all_robust_curvature.append(robust_curvature)
            all_scale_correlations.append(scale_correlation)
            all_regions.append(regions)
            all_region_stats.append(region_stats)
        
        # Calculate dynamics metrics
        dynamics = []
        for t, (contour, curvature, consistency) in enumerate(zip(
                contours, all_robust_curvature, all_consistency)):
            metrics = {
                'time': times[t],
                'mean_curvature': np.mean(curvature),
                'curvature_std': np.std(curvature),
                'positive_curvature_area': np.sum(curvature > 0) / len(curvature),
                'negative_curvature_area': np.sum(curvature < 0) / len(curvature),
                'high_curvature_regions': np.sum(np.abs(curvature) > np.std(curvature)),
                'mean_consistency': np.mean(consistency),
                'contour_length': len(contour) * self.scale_factor,
                'contour_complexity': np.sum(np.abs(np.diff(curvature)))
            }
            
            # Calculate temporal metrics if not first time point
            if t > 0:
                prev_curvature = all_robust_curvature[t-1]
                curvature_change = curvature - prev_curvature
                metrics.update({
                    'mean_curvature_change': np.mean(curvature_change),
                    'max_curvature_increase': np.max(curvature_change),
                    'max_curvature_decrease': np.min(curvature_change),
                    'curvature_change_std': np.std(curvature_change)
                })
                
                # Detect potential extrusion/retraction events
                pos_change = curvature_change > 2 * np.std(curvature_change)
                neg_change = curvature_change < -2 * np.std(curvature_change)
                metrics.update({
                    'potential_extrusions': np.sum(neg_change),  # Negative change = outward movement
                    'potential_retractions': np.sum(pos_change)  # Positive change = inward movement
                })
            
            dynamics.append(metrics)
        
        # Return all results
        results = {
            'contours': contours,
            'dynamics': pd.DataFrame(dynamics),
            'regions': all_region_stats,
            'consistency': all_consistency,
            'robust_curvature': all_robust_curvature,
            'scale_curvatures': all_scale_curvatures,
            'scale_correlations': all_scale_correlations,
            'region_labels': all_regions
        }
        
        return results
    
    def visualize_dynamics(self, images, results, time_indices=None):
        """
        Create visualizations of membrane dynamics.
        
        Parameters:
        -----------
        images : list or ndarray
            Sequence of images (time series)
        results : dict
            Analysis results from analyze_time_series
        time_indices : list or None
            Specific time indices to visualize (if None, uses all)
            
        Returns:
        --------
        figs : dict
            Dictionary of figures
        """
        if time_indices is None:
            time_indices = range(len(images))
        
        figs = {'multi_scale': [], 'regions': [], 'dynamics': []}
        
        # Create visualizations for selected time points
        for t in time_indices:
            image = images[t]
            contour = results['contours'][t]
            consistency = results['consistency'][t]
            robust_curvature = results['robust_curvature'][t]
            scale_curvatures = results['scale_curvatures'][t]
            regions = results['region_labels'][t]
            region_stats = results['regions'][t]
            
            # Multi-scale analysis visualization
            fig_multi = visualize_multi_scale_analysis(
                image, contour, scale_curvatures, consistency, robust_curvature)
            fig_multi.suptitle(f'Time Point {t}')
            figs['multi_scale'].append(fig_multi)
            
            # Region visualization
            fig_regions = visualize_membrane_regions(
                image, contour, regions, region_stats)
            fig_regions.suptitle(f'Time Point {t}')
            figs['regions'].append(fig_regions)
        
        # Create dynamics plots
        dynamics_df = results['dynamics']
        
        # Overall dynamics
        fig_dynamics, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Plot mean curvature over time
        axes[0, 0].plot(dynamics_df['time'], dynamics_df['mean_curvature'], 'b-')
        axes[0, 0].set_title('Mean Curvature vs Time')
        axes[0, 0].set_xlabel('Time')
        axes[0, 0].set_ylabel('Mean Curvature')
        
        # Plot positive and negative curvature areas
        axes[0, 1].plot(dynamics_df['time'], dynamics_df['positive_curvature_area'], 'r-', 
                        label='Positive (inward)')
        axes[0, 1].plot(dynamics_df['time'], dynamics_df['negative_curvature_area'], 'b-', 
                        label='Negative (outward)')
        axes[0, 1].set_title('Curvature Distribution vs Time')
        axes[0, 1].set_xlabel('Time')
        axes[0, 1].set_ylabel('Area Fraction')
        axes[0, 1].legend()
        
        # Plot curvature complexity
        axes[1, 0].plot(dynamics_df['time'], dynamics_df['contour_complexity'], 'g-')
        axes[1, 0].set_title('Membrane Complexity vs Time')
        axes[1, 0].set_xlabel('Time')
        axes[1, 0].set_ylabel('Complexity')
        
        # Plot potential extrusion/retraction events if available
        if 'potential_extrusions' in dynamics_df:
            axes[1, 1].plot(dynamics_df['time'][1:], dynamics_df['potential_extrusions'][1:], 'b-', 
                            label='Extrusions')
            axes[1, 1].plot(dynamics_df['time'][1:], dynamics_df['potential_retractions'][1:], 'r-', 
                            label='Retractions')
            axes[1, 1].set_title('Membrane Events vs Time')
            axes[1, 1].set_xlabel('Time')
            axes[1, 1].set_ylabel('Event Count')
            axes[1, 1].legend()
        
        plt.tight_layout()
        figs['dynamics'].append(fig_dynamics)
        
        return figs
    
    def create_animation(self, images, results):
        """
        Create an animation of membrane dynamics.
        
        Parameters:
        -----------
        images : list or ndarray
            Sequence of images (time series)
        results : dict
            Analysis results from analyze_time_series
            
        Returns:
        --------
        anim : FuncAnimation
            Animation object
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Initialize plot
        ax.imshow(images[0], cmap='gray')
        
        # Create symmetric colormap around zero for curvature
        max_abs_curv = max([
            max(abs(np.min(curv)), abs(np.max(curv))) 
            for curv in results['robust_curvature']
        ])
        norm = plt.Normalize(vmin=-max_abs_curv, vmax=max_abs_curv)
        
        # Initial scatter plot
        contour = results['contours'][0]
        robust_curvature = results['robust_curvature'][0]
        scatter = ax.scatter(
            contour[:, 0], contour[:, 1], 
            c=robust_curvature, cmap='coolwarm', 
            norm=norm, s=10, alpha=0.7
        )
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Curvature')
        
        # Add time indicator
        time_text = ax.text(0.02, 0.98, 'Time: 0', transform=ax.transAxes, 
                           color='white', fontsize=12, va='top')
        
        def update(frame):
            # Update image
            ax.imshow(images[frame], cmap='gray')
            
            # Update contour points and colors
            contour = results['contours'][frame]
            robust_curvature = results['robust_curvature'][frame]
            
            # Update scatter plot
            scatter.set_offsets(contour)
            scatter.set_array(robust_curvature)
            
            # Update time text
            if 'time' in results['dynamics']:
                time_text.set_text(f"Time: {results['dynamics']['time'][frame]:.2f}")
            else:
                time_text.set_text(f"Frame: {frame}")
            
            return scatter, time_text
        
        # Create animation
        anim = FuncAnimation(fig, update, frames=len(images), 
                            interval=200, blit=True)
        
        return anim, fig
    
    def identify_key_events(self, results, threshold=2.0):
        """
        Identify key extrusion and retraction events.
        
        Parameters:
        -----------
        results : dict
            Analysis results from analyze_time_series
        threshold : float
            Threshold in standard deviations for event detection
            
        Returns:
        --------
        events : DataFrame
            DataFrame of detected events with timing and location
        """
        events = []
        dynamics = results['dynamics']
        
        # Skip first frame as we need difference data
        for t in range(1, len(results['contours'])):
            prev_time = dynamics['time'].iloc[t-1] if 'time' in dynamics else t-1
            curr_time = dynamics['time'].iloc[t] if 'time' in dynamics else t
            
            # Get curvatures for current and previous time
            prev_curve = results['robust_curvature'][t-1]
            curr_curve = results['robust_curvature'][t]
            
            # Calculate curvature change
            curve_change = curr_curve - prev_curve
            
            # Calculate threshold based on standard deviation
            std_threshold = threshold * np.std(curve_change)
            
            # Detect significant changes
            extrusion_mask = curve_change < -std_threshold  # negative change = outward motion
            retraction_mask = curve_change > std_threshold   # positive change = inward motion
            
            # Get contour coordinates
            contour = results['contours'][t]
            
            # Record extrusion events
            for idx in np.where(extrusion_mask)[0]:
                event = {
                    'time': curr_time,
                    'time_idx': t,
                    'type': 'extrusion',
                    'position_idx': idx,
                    'position_x': contour[idx, 0],
                    'position_y': contour[idx, 1],
                    'curvature_before': prev_curve[idx],
                    'curvature_after': curr_curve[idx],
                    'curvature_change': curve_change[idx],
                    'consistency': results['consistency'][t][idx]
                }
                events.append(event)
            
            # Record retraction events
            for idx in np.where(retraction_mask)[0]:
                event = {
                    'time': curr_time,
                    'time_idx': t,
                    'type': 'retraction',
                    'position_idx': idx,
                    'position_x': contour[idx, 0],
                    'position_y': contour[idx, 1],
                    'curvature_before': prev_curve[idx],
                    'curvature_after': curr_curve[idx],
                    'curvature_change': curve_change[idx],
                    'consistency': results['consistency'][t][idx]
                }
                events.append(event)
        
        events_df = pd.DataFrame(events)
        return events_df
    
    def visualize_events(self, images, results, events_df):
        """
        Visualize detected membrane events.
        
        Parameters:
        -----------
        images : list or ndarray
            Sequence of images (time series)
        results : dict
            Analysis results from analyze_time_series
        events_df : DataFrame
            DataFrame of detected events from identify_key_events
            
        Returns:
        --------
        figs : list
            List of event visualization figures
        """
        figs = []
        
        # Group events by time
        time_groups = events_df.groupby('time_idx')
        
        for time_idx, group in time_groups:
            if time_idx >= len(images):
                continue
                
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Show image
            ax.imshow(images[time_idx], cmap='gray')
            
            # Show contour with curvature coloring
            contour = results['contours'][time_idx]
            curvature = results['robust_curvature'][time_idx]
            
            # Create symmetric colormap
            max_abs_curv = max(abs(np.min(curvature)), abs(np.max(curvature)))
            norm = plt.Normalize(vmin=-max_abs_curv, vmax=max_abs_curv)
            
            # Plot contour
            scatter = ax.scatter(contour[:, 0], contour[:, 1], 
                                c=curvature, cmap='coolwarm', 
                                norm=norm, s=5, alpha=0.5)
            
            # Mark extrusions and retractions
            extrusions = group[group['type'] == 'extrusion']
            retractions = group[group['type'] == 'retraction']
            
            if not extrusions.empty:
                ax.scatter(extrusions['position_x'], extrusions['position_y'], 
                           color='blue', marker='o', s=100, alpha=0.7, 
                           label='Extrusion')
            
            if not retractions.empty:
                ax.scatter(retractions['position_x'], retractions['position_y'], 
                           color='red', marker='s', s=100, alpha=0.7,
                           label='Retraction')
            
            # Add colorbar and legend
            plt.colorbar(scatter, ax=ax, label='Curvature')
            ax.legend()
            
            # Add title
            ax.set_title(f'Membrane Events at Time {time_idx}')
            
            figs.append(fig)
        
        return figs