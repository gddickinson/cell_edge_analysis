import numpy as np
import matplotlib.pyplot as plt
from skimage import io, measure, filters
from scipy.ndimage import gaussian_filter
import os
import pandas as pd
import traceback
from multi_scale_curvature import (
    multi_scale_consistency,
    identify_membrane_regions,
    visualize_multi_scale_analysis,
    visualize_membrane_regions
)

from membrane_dynamics_analysis import MembraneDynamicsAnalyzer

# Example usage for a single image
def analyze_single_image(image_path, output_dir='./results'):
    """
    Analyze a single cell image using multi-scale curvature analysis.

    Parameters:
    -----------
    image_path : str
        Path to the image file
    output_dir : str
        Directory to save results
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Load image
        image = io.imread(image_path)

        # Ensure image is grayscale
        if len(image.shape) > 2:
            # Convert RGB to grayscale if needed
            image = np.mean(image, axis=2).astype(np.float32)

        print(f"Image loaded: shape={image.shape}, min={np.min(image)}, max={np.max(image)}")

        # Extract contour
        # Apply preprocessing
        blurred = gaussian_filter(image, sigma=1.0)

        # Simple thresholding
        threshold = filters.threshold_otsu(blurred)
        binary = blurred > threshold

        # Find contours
        contours = measure.find_contours(binary, 0.5)
        if not contours:
            print("No contours found in the image")
            return

        # Select largest contour
        contour = max(contours, key=len)
        print(f"Contour extracted: {len(contour)} points")

        # Swap coordinates to convert from (row, col) to (x, y)
        contour = np.fliplr(contour)

        # Resample to have equal spacing
        n_samples = 100
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

        contour = np.column_stack((x_interp, y_interp))
        print(f"Resampled contour: {len(contour)} points")

        # Save a simple contour visualization for verification
        plt.figure(figsize=(10, 8))
        plt.imshow(image, cmap='gray')
        plt.plot(contour[:, 0], contour[:, 1], 'r-', linewidth=2)
        plt.title('Extracted Contour')
        plt.savefig(os.path.join(output_dir, 'contour_verification.png'))
        plt.close()

        # Step 1: Multi-scale analysis with various segment lengths
        min_segment = 5
        max_segment = 25
        step = 2

        # Run multi-scale analysis
        print("Running multi-scale curvature analysis...")
        consistency, scale_curvatures, robust_curvature, scale_correlation = \
            multi_scale_consistency(contour, min_segment, max_segment, step)

        # Check for NaN values in results
        nan_count = np.sum(np.isnan(robust_curvature))
        if nan_count > 0:
            print(f"Warning: {nan_count} NaN values found in robust curvature estimation")
            # Replace NaNs with zeros for visualization
            robust_curvature = np.nan_to_num(robust_curvature, nan=0.0)

        # Step 2: Identify membrane regions
        print("Identifying membrane regions...")
        regions, region_stats = identify_membrane_regions(contour, robust_curvature, consistency)

        # Step 3: Visualize results
        print("Creating visualizations...")

        try:
            # Multi-scale analysis visualization
            fig_multi = visualize_multi_scale_analysis(
                image, contour, scale_curvatures, consistency, robust_curvature)
            fig_multi.savefig(os.path.join(output_dir, 'multi_scale_analysis.png'))
        except Exception as e:
            print(f"Error creating multi-scale visualization: {str(e)}")
            traceback.print_exc()

        try:
            # Region visualization
            fig_regions = visualize_membrane_regions(
                image, contour, regions, region_stats)
            fig_regions.savefig(os.path.join(output_dir, 'membrane_regions.png'))
        except Exception as e:
            print(f"Error creating region visualization: {str(e)}")
            traceback.print_exc()

        try:
            # Curvature visualization at different scales
            fig_scales = plt.figure(figsize=(15, 10))

            # Plot curvature at each scale
            segment_lengths = sorted(scale_curvatures.keys())
            for i, segment_length in enumerate(segment_lengths):
                if i < 12:  # Limit to 12 subplots
                    ax = fig_scales.add_subplot(3, 4, i+1)
                    curvature_values = scale_curvatures[segment_length]
                    # Replace NaNs with zeros for plotting
                    curvature_values = np.nan_to_num(curvature_values, nan=0.0)
                    ax.plot(curvature_values)
                    ax.set_title(f'Segment Length: {segment_length}')
                    ax.set_xlabel('Contour Position')
                    ax.set_ylabel('Curvature')
                    ax.grid(True)

            # Add consistency plot if space remains
            if len(segment_lengths) < 12:
                ax = fig_scales.add_subplot(3, 4, len(segment_lengths)+1)
                ax.plot(consistency)
                ax.set_title('Consistency Across Scales')
                ax.set_xlabel('Contour Position')
                ax.set_ylabel('Consistency')
                ax.grid(True)

            fig_scales.tight_layout()
            fig_scales.savefig(os.path.join(output_dir, 'scale_comparison.png'))
        except Exception as e:
            print(f"Error creating scale comparison visualization: {str(e)}")
            traceback.print_exc()

        try:
            # Scale correlation heatmap
            fig_corr = plt.figure(figsize=(8, 6))
            ax = fig_corr.add_subplot(111)
            # Replace NaNs with zeros for visualization
            scale_correlation_clean = np.nan_to_num(scale_correlation, nan=0.0)
            im = ax.imshow(scale_correlation_clean, cmap='viridis', vmin=-1, vmax=1)
            ax.set_title('Correlation Between Scales')

            segment_lengths = sorted(scale_curvatures.keys())
            ax.set_xticks(range(len(segment_lengths)))
            ax.set_yticks(range(len(segment_lengths)))
            ax.set_xticklabels(segment_lengths)
            ax.set_yticklabels(segment_lengths)
            ax.set_xlabel('Segment Length')
            ax.set_ylabel('Segment Length')
            plt.colorbar(im, ax=ax)
            fig_corr.tight_layout()
            fig_corr.savefig(os.path.join(output_dir, 'scale_correlation.png'))
        except Exception as e:
            print(f"Error creating correlation visualization: {str(e)}")
            traceback.print_exc()

        # Save numerical results
        try:
            results = {
                'robust_curvature': robust_curvature,
                'consistency': consistency,
                'region_stats': region_stats
            }

            # Save curvature profiles at each scale
            curvature_df = pd.DataFrame()
            for segment_length in sorted(scale_curvatures.keys()):
                curvature_df[f'segment_{segment_length}'] = scale_curvatures[segment_length]

            curvature_df['robust'] = robust_curvature
            curvature_df['consistency'] = consistency
            curvature_df['region'] = regions
            curvature_df.to_csv(os.path.join(output_dir, 'curvature_profiles.csv'))

            # Save region statistics
            region_stats.to_csv(os.path.join(output_dir, 'region_statistics.csv'))

            # Save scale correlation matrix
            pd.DataFrame(scale_correlation,
                        index=sorted(scale_curvatures.keys()),
                        columns=sorted(scale_curvatures.keys())).to_csv(
                os.path.join(output_dir, 'scale_correlation.csv'))
        except Exception as e:
            print(f"Error saving numerical results: {str(e)}")
            traceback.print_exc()

        print("Analysis complete. Results saved to", output_dir)

        return results

    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        traceback.print_exc()
        return None

# Example usage for a time series of images
def analyze_time_series(image_folder, output_dir='./results_time_series'):
    """
    Analyze a time series of cell images.

    Parameters:
    -----------
    image_folder : str
        Path to folder containing time series images
    output_dir : str
        Directory to save results
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # List image files
    image_files = sorted([f for f in os.listdir(image_folder)
                         if f.endswith(('.tif', '.jpg', '.png'))])

    if not image_files:
        print(f"No image files found in {image_folder}")
        return

    # Load images
    images = []
    for file in image_files:
        image = io.imread(os.path.join(image_folder, file))
        # Ensure image is grayscale
        if len(image.shape) > 2:
            image = np.mean(image, axis=2).astype(np.float32)
        images.append(image)

    # Create analyzer
    analyzer = MembraneDynamicsAnalyzer(
        scale_factor=100,  # Conversion factor from pixels to nm
        min_segment=5,
        max_segment=25,
        step=2
    )

    # Analyze time series
    print(f"Analyzing {len(images)} images...")
    results = analyzer.analyze_time_series(images)

    # Create visualizations
    print("Creating visualizations...")
    figs = analyzer.visualize_dynamics(images, results)

    # Save figures
    for i, fig in enumerate(figs['multi_scale']):
        fig.savefig(os.path.join(output_dir, f'multi_scale_t{i}.png'))

    for i, fig in enumerate(figs['regions']):
        fig.savefig(os.path.join(output_dir, f'regions_t{i}.png'))

    for i, fig in enumerate(figs['dynamics']):
        fig.savefig(os.path.join(output_dir, f'dynamics_{i}.png'))

    # Identify and visualize key events
    events_df = analyzer.identify_key_events(results)
    event_figs = analyzer.visualize_events(images, results, events_df)

    for i, fig in enumerate(event_figs):
        fig.savefig(os.path.join(output_dir, f'events_{i}.png'))

    # Save numerical results
    results['dynamics'].to_csv(os.path.join(output_dir, 'dynamics_metrics.csv'))
    events_df.to_csv(os.path.join(output_dir, 'membrane_events.csv'))

    # Create and save animation if more than one frame
    if len(images) > 1:
        print("Creating animation...")
        anim, fig = analyzer.create_animation(images, results)
        # Note: Saving animations may require additional libraries like ffmpeg
        try:
            anim.save(os.path.join(output_dir, 'membrane_dynamics.mp4'))
        except Exception as e:
            print(f"Could not save animation: {e}")
            print("Try: anim.save('animation.gif', writer='pillow')")

    print("Analysis complete. Results saved to", output_dir)

    return results, events_df

def load_multiframe_tiff(tiff_path):
    """
    Load a multi-frame TIFF file.

    Parameters:
    -----------
    tiff_path : str
        Path to the multi-frame TIFF file

    Returns:
    --------
    frames : list
        List of image frames
    """
    try:
        from tifffile import TiffFile

        frames = []
        with TiffFile(tiff_path) as tif:
            for page in tif.pages:
                frames.append(page.asarray())

        print(f"Loaded {len(frames)} frames from {tiff_path}")
        return frames
    except ImportError:
        print("tifffile module not found. Please install it with: pip install tifffile")
        # Fallback to using scikit-image, which may not handle all formats correctly
        from skimage import io
        try:
            # Try to load as multi-page TIFF
            image = io.imread(tiff_path)
            if image.ndim > 2:
                # First dimension could be frames
                if image.shape[0] > 1:
                    frames = [image[i] for i in range(image.shape[0])]
                    print(f"Loaded {len(frames)} frames from {tiff_path}")
                    return frames

            # If we got here, it's a single frame or failed to detect multiple frames
            print(f"Warning: Could only load a single frame from {tiff_path}")
            return [image]
        except Exception as e:
            print(f"Error loading multi-frame TIFF: {e}")
            return None

if __name__ == "__main__":
    # Check for command line arguments
    import sys

    # Default settings
    image_path = "your_cell_image.tif"
    num_frames = 0  # 0 means analyze all frames, 1 means single frame analysis

    # Parse command line arguments
    if len(sys.argv) > 1:
        # First argument is the image path
        image_path = sys.argv[1]
        print(f"Using image from command line: {image_path}")

        # Check for second argument (number of frames)
        if len(sys.argv) > 2:
            try:
                num_frames = int(sys.argv[2])
                print(f"Will analyze {num_frames} frames" if num_frames > 0 else "Will analyze all frames")
            except ValueError:
                print(f"Invalid number of frames: {sys.argv[2]}, will analyze all frames")
                num_frames = 0
    else:
        print(f"No image specified, trying default: {image_path}")

    # Create output directory with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"results_{timestamp}"

    def load_multiframe_tiff(tiff_path, max_frames=0):
        """
        Load a multi-frame TIFF file.

        Parameters:
        -----------
        tiff_path : str
            Path to the multi-frame TIFF file
        max_frames : int
            Maximum number of frames to load (0 = all frames)

        Returns:
        --------
        frames : list
            List of image frames
        """
        try:
            from tifffile import TiffFile

            frames = []
            with TiffFile(tiff_path) as tif:
                for i, page in enumerate(tif.pages):
                    if max_frames > 0 and i >= max_frames:
                        break
                    frames.append(page.asarray())

            print(f"Loaded {len(frames)} frames from {tiff_path}")
            return frames
        except ImportError:
            print("tifffile module not found. Please install it with: pip install tifffile")
            # Fallback to using scikit-image, which may not handle all formats correctly
            from skimage import io
            try:
                # Try to load as multi-page TIFF
                image = io.imread(tiff_path)
                if image.ndim > 2:
                    # First dimension could be frames
                    if image.shape[0] > 1:
                        if max_frames > 0:
                            frames = [image[i] for i in range(min(max_frames, image.shape[0]))]
                        else:
                            frames = [image[i] for i in range(image.shape[0])]
                        print(f"Loaded {len(frames)} frames from {tiff_path}")
                        return frames

                # If we got here, it's a single frame or failed to detect multiple frames
                print(f"Warning: Could only load a single frame from {tiff_path}")
                return [image]
            except Exception as e:
                print(f"Error loading multi-frame TIFF: {e}")
                return None

    # Analyze real image if it exists
    if os.path.exists(image_path):
        print(f"Loading image: {image_path}")

        # Force single frame analysis if requested
        if num_frames == 1:
            print("Single frame analysis requested")
            try:
                # Start with very verbose mode
                import logging
                logging.basicConfig(level=logging.DEBUG)

                results = analyze_single_image(image_path, output_dir=output_dir)

                if results is not None:
                    print("Analysis completed successfully")
                else:
                    print("Analysis failed or returned no results")
            except Exception as e:
                print(f"Error during analysis: {str(e)}")
                traceback.print_exc()
        else:
            # Try multi-frame analysis
            try:
                # Try loading as multi-frame
                frames = load_multiframe_tiff(image_path, max_frames=num_frames)

                if frames and len(frames) > 1:
                    print(f"Detected multi-frame TIFF with {len(frames)} frames")
                    # Use time series analysis
                    try:
                        # Import the necessary analyzer
                        from membrane_dynamics_analysis import MembraneDynamicsAnalyzer

                        # Create output directory for time series
                        ts_output_dir = f"timeseries_{timestamp}"
                        os.makedirs(ts_output_dir, exist_ok=True)

                        # Create analyzer
                        analyzer = MembraneDynamicsAnalyzer(
                            scale_factor=100,  # Adjust based on your microscope calibration
                            min_segment=7,     # Adjust based on your cell type
                            max_segment=25,    # Adjust based on your cell type
                            step=3             # Adjust as needed
                        )

                        # Analyze time series
                        print(f"Analyzing {len(frames)} frames...")
                        results = analyzer.analyze_time_series(frames)

                        # Create visualizations
                        print("Creating time series visualizations...")
                        figs = analyzer.visualize_dynamics(frames, results)

                        # Save figures
                        for i, fig in enumerate(figs['multi_scale']):
                            if i < 10:  # Only save first 10 frames to avoid too many files
                                fig.savefig(os.path.join(ts_output_dir, f'multi_scale_t{i}.png'))

                        for i, fig in enumerate(figs['regions']):
                            if i < 10:  # Only save first 10 frames
                                fig.savefig(os.path.join(ts_output_dir, f'regions_t{i}.png'))

                        for i, fig in enumerate(figs['dynamics']):
                            fig.savefig(os.path.join(ts_output_dir, f'dynamics_{i}.png'))

                        # Identify and visualize key events
                        events_df = analyzer.identify_key_events(results)
                        event_figs = analyzer.visualize_events(frames, results, events_df)

                        for i, fig in enumerate(event_figs):
                            fig.savefig(os.path.join(ts_output_dir, f'events_{i}.png'))

                        # Save numerical results
                        results['dynamics'].to_csv(os.path.join(ts_output_dir, 'dynamics_metrics.csv'))
                        events_df.to_csv(os.path.join(ts_output_dir, 'membrane_events.csv'))

                        # Create and save animation if not too many frames
                        if len(frames) <= 100:
                            print("Creating animation...")
                            try:
                                anim, fig = analyzer.create_animation(frames, results)
                                # Try different formats if one fails
                                try:
                                    anim.save(os.path.join(ts_output_dir, 'membrane_dynamics.mp4'))
                                except:
                                    try:
                                        anim.save(os.path.join(ts_output_dir, 'membrane_dynamics.gif'),
                                                 writer='pillow', fps=5)
                                    except Exception as e:
                                        print(f"Could not save animation: {e}")
                            except Exception as e:
                                print(f"Error creating animation: {e}")

                        print(f"Time series analysis complete. Results saved to {ts_output_dir}")

                    except Exception as e:
                        print(f"Error in time series analysis: {e}")
                        traceback.print_exc()

                        # Fall back to analyzing first frame only
                        print("Falling back to single frame analysis")
                        first_frame = frames[0]
                        # Save first frame temporarily
                        temp_path = os.path.join(output_dir, "temp_first_frame.tif")
                        os.makedirs(output_dir, exist_ok=True)
                        io.imsave(temp_path, first_frame)
                        # Analyze first frame
                        results = analyze_single_image(temp_path, output_dir=output_dir)
                        # Clean up
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                else:
                    # Single frame analysis
                    print("Processing as single frame")
                    try:
                        # Start with very verbose mode
                        import logging
                        logging.basicConfig(level=logging.DEBUG)

                        results = analyze_single_image(image_path, output_dir=output_dir)

                        if results is not None:
                            print("Analysis completed successfully")
                        else:
                            print("Analysis failed or returned no results")
                    except Exception as e:
                        print(f"Error during analysis: {str(e)}")
                        traceback.print_exc()
            except Exception as e:
                print(f"Error detecting multi-frame TIFF: {e}")
                # Fall back to single image analysis
                try:
                    results = analyze_single_image(image_path, output_dir=output_dir)
                except Exception as e:
                    print(f"Error during analysis: {str(e)}")
                    traceback.print_exc()
    else:
        print(f"Image file not found: {image_path}")
        print("Using test mode with simulated cell...")

        # Create test output directory
        test_output_dir = f"test_results_{timestamp}"

        # Create test image with a circular cell and blebs
        size = 512
        center = size // 2
        radius = 180

        image = np.zeros((size, size))
        y, x = np.ogrid[:size, :size]
        dist_from_center = np.sqrt((x - center)**2 + (y - center)**2)
        circle_mask = dist_from_center <= radius
        image[circle_mask] = 1

        # Add blebs with different shapes
        for angle in [0, np.pi/2, np.pi, 3*np.pi/2]:
            # Distance from center
            bleb_distance = radius * 0.9

            # Bleb center
            bleb_x = center + int(bleb_distance * np.cos(angle))
            bleb_y = center + int(bleb_distance * np.sin(angle))

            # Vary bleb size and shape
            if angle == 0:
                # Larger circular bleb
                bleb_radius = 40
                bleb_distance = np.sqrt((x - bleb_x)**2 + (y - bleb_y)**2)
                bleb_mask = bleb_distance <= bleb_radius
            elif angle == np.pi/2:
                # Elliptical bleb
                bleb_mask = ((x - bleb_x)**2/900 + (y - bleb_y)**2/400) <= 1
            elif angle == np.pi:
                # Small circular bleb
                bleb_radius = 25
                bleb_distance = np.sqrt((x - bleb_x)**2 + (y - bleb_y)**2)
                bleb_mask = bleb_distance <= bleb_radius
            else:
                # Irregular shape
                bleb_radius = 30
                bleb_distance = np.sqrt((x - bleb_x)**2 + (y - bleb_y)**2)
                # Add some randomness to the border
                random_factor = np.random.normal(0, 0.15, size=image.shape)
                bleb_mask = bleb_distance <= (bleb_radius * (1 + random_factor))

            # Add bleb
            image[bleb_mask] = 1

        # Add noise
        image = image + np.random.normal(0, 0.05, image.shape)

        # Ensure values are in valid range
        image = np.clip(image, 0, 1)

        # Save test image
        test_image_path = 'test_cell.tif'
        io.imsave(test_image_path, (image * 255).astype(np.uint8))
        print(f"Created test image: {test_image_path}")

        # Analyze test image
        try:
            results = analyze_single_image(test_image_path, output_dir=test_output_dir)
            print(f"Test analysis completed, results in: {test_output_dir}")
        except Exception as e:
            print(f"Error during test analysis: {str(e)}")
            traceback.print_exc()

    # Keep figures open if run interactively
    plt.show()
