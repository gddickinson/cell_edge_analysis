#!/usr/bin/env python3
"""
Standalone PIEZO1 Analysis Script
--------------------------------
This script analyzes PIEZO1 distribution along cell edges in TIRF microscopy data.
It processes a single frame from binary segmentation and PIEZO1 fluorescence TIFF stacks.

Required packages:
- numpy
- matplotlib
- tifffile
- opencv-python (cv2)
- scipy
- skimage
"""

import numpy as np
import matplotlib.pyplot as plt
import tifffile
import cv2
from scipy.interpolate import splprep, splev
from scipy.ndimage import gaussian_filter1d, binary_fill_holes
from skimage import measure, morphology

def load_first_frames(cell_path, piezo_path):
    """Load first frames from both TIFF stacks."""
    cell_stack = tifffile.imread(cell_path)
    piezo_stack = tifffile.imread(piezo_path)

    # Handle both single images and stacks
    cell_frame = cell_stack[0] if cell_stack.ndim > 2 else cell_stack
    piezo_frame = piezo_stack[0] if piezo_stack.ndim > 2 else piezo_stack

    return cell_frame, piezo_frame

def detect_cell_edge(binary_image, min_size=100):
    """
    Detect cell edge from binary segmentation.
    Returns the edge image and contour points.
    """
    # Clean up binary image
    cleaned = morphology.remove_small_objects(binary_image > 0, min_size=min_size)
    cleaned = cleaned.astype(np.uint8)

    # Find contours using OpenCV
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    if contours:
        # Get largest contour by area
        largest_contour = max(contours, key=cv2.contourArea)

        # Create edge image
        edge_image = np.zeros_like(cleaned)
        cv2.drawContours(edge_image, [largest_contour], -1, 255, 2)

        return edge_image, largest_contour.squeeze()

    return None, None

def analyze_edge_intensity(piezo_image, contour, sampling_depth=20, vector_width=5,
                         interval=20, smoothing_sigma=3, border_margin=20):
    """
    Analyze PIEZO1 intensity along the cell edge.
    Returns intensity measurements and sampling points.
    """
    try:
        # Ensure contour is properly shaped
        if contour is None or len(contour) < 3:
            raise ValueError("Invalid contour")

        # Create binary mask of cell interior
        binary_mask = np.zeros_like(piezo_image, dtype=np.uint8)
        cv2.drawContours(binary_mask, [contour.astype(np.int32)], -1, 1, thickness=-1)
        binary_mask = binary_fill_holes(binary_mask).astype(np.uint8)

        # Resample contour points at regular intervals
        contour_length = len(contour)
        sample_indices = np.linspace(0, contour_length - 1, contour_length // interval, dtype=int)
        points = contour[sample_indices]

        intensities = []
        normals = []
        filtered_points = []

        # Calculate intensities along contour
        for i in range(len(points)):
            current = points[i]
            next_point = points[(i + 1) % len(points)]

            # Skip points near image border
            x, y = current.astype(int)
            if (x < border_margin or x > piezo_image.shape[1] - border_margin or
                y < border_margin or y > piezo_image.shape[0] - border_margin):
                continue

            # Calculate normal vector
            dx = next_point[0] - current[0]
            dy = next_point[1] - current[1]
            normal = np.array([dy, -dx])
            norm = np.sqrt(np.sum(normal**2))
            if norm > 0:
                normal = normal / norm
            else:
                continue

            # Verify normal points into cell
            test_point = current + normal * 5
            x, y = test_point.astype(int)
            if 0 <= x < binary_mask.shape[1] and 0 <= y < binary_mask.shape[0]:
                if not binary_mask[y, x]:
                    normal = -normal

            # Check if sampling vector stays within image bounds and away from border
            end_point = current + normal * sampling_depth
            end_x, end_y = end_point.astype(int)
            if (end_x < border_margin or end_x > piezo_image.shape[1] - border_margin or
                end_y < border_margin or end_y > piezo_image.shape[0] - border_margin):
                continue

            # Sample intensity
            valid_point = True
            intensities_along_normal = []

            for depth in range(sampling_depth):
                sample_point = current + normal * depth
                x, y = sample_point.astype(int)

                if 0 <= x < piezo_image.shape[1] and 0 <= y < piezo_image.shape[0]:
                    if binary_mask[y, x]:  # Only sample inside the cell
                        intensities_along_normal.append(piezo_image[y, x])
                    else:
                        valid_point = False
                        break
                else:
                    valid_point = False
                    break

            if valid_point and intensities_along_normal:
                intensities.append(np.mean(intensities_along_normal))
                normals.append(normal)
                filtered_points.append(current)

        if not filtered_points:
            raise ValueError("No valid measurement points found")

        print(f"Found {len(filtered_points)} valid measurement points "
              f"(filtered {len(points) - len(filtered_points)} edge points)")

        return (np.array(intensities),
                np.array(filtered_points),
                np.array(normals))

    except Exception as e:
        print(f"Error in intensity analysis: {e}")
        return None, None, None

def calculate_curvature(contour, intensity_points=None, smoothing_sigma=3, resample_size=500):
    """
    Calculate curvature along the cell edge.

    Args:
        contour: Original cell contour
        intensity_points: Points where intensity was measured (optional)
        smoothing_sigma: Smoothing parameter for Gaussian filter

    Returns:
        curvature values and smoothed contour
    """

    try:
        # Ensure contour is properly shaped
        if contour is None or len(contour) < 3:
            raise ValueError("Invalid contour")

        # If intensity points are provided, calculate curvature at those points
        if intensity_points is not None:
            print(f"Calculating curvature at {len(intensity_points)} intensity measurement points")

            # First smooth the entire contour
            x = gaussian_filter1d(contour[:, 0], smoothing_sigma)
            y = gaussian_filter1d(contour[:, 1], smoothing_sigma)

            # Calculate derivatives along the full contour
            dx = np.gradient(x)
            dy = np.gradient(y)
            d2x = np.gradient(dx)
            d2y = np.gradient(dy)

            # Interpolate derivatives at intensity points
            # First, create parameter along the curve
            t = np.arange(len(x))

            # Create interpolators for derivatives
            from scipy.interpolate import interp1d
            dx_interp = interp1d(t, dx, bounds_error=False, fill_value="extrapolate")
            dy_interp = interp1d(t, dy, bounds_error=False, fill_value="extrapolate")
            d2x_interp = interp1d(t, d2x, bounds_error=False, fill_value="extrapolate")
            d2y_interp = interp1d(t, d2y, bounds_error=False, fill_value="extrapolate")

            # Find closest points on the contour for each intensity point
            curvature = np.zeros(len(intensity_points))
            for i, point in enumerate(intensity_points):
                # Find closest point in the contour
                dists = np.sum((contour - point)**2, axis=1)
                closest_idx = np.argmin(dists)

                # Get interpolated derivatives
                dx_i = dx_interp(closest_idx)
                dy_i = dy_interp(closest_idx)
                d2x_i = d2x_interp(closest_idx)
                d2y_i = d2y_interp(closest_idx)

                # Calculate curvature
                denominator = (dx_i * dx_i + dy_i * dy_i)**1.5
                if denominator > 1e-10:
                    curvature[i] = (dx_i * d2y_i - dy_i * d2x_i) / denominator
                else:
                    curvature[i] = 0

            print(f"Curvature range: [{np.min(curvature)}, {np.max(curvature)}]")
            return curvature, contour

        else:
            # Original calculation for the full contour
            print("No intensity points provided, calculating curvature for full contour")


            # Resample contour to have fewer points
            # Calculate current arc lengths
            diff = np.diff(contour, axis=0)
            segment_lengths = np.sqrt(np.sum(diff**2, axis=1))
            arc_lengths = np.concatenate(([0], np.cumsum(segment_lengths)))

            # Create new sample points
            total_length = arc_lengths[-1]
            sample_distances = np.linspace(0, total_length, resample_size)

            # Interpolate x and y coordinates
            resampled_x = np.interp(sample_distances, arc_lengths, contour[:, 0])
            resampled_y = np.interp(sample_distances, arc_lengths, contour[:, 1])

            # Smooth coordinates
            x = gaussian_filter1d(resampled_x, smoothing_sigma)
            y = gaussian_filter1d(resampled_y, smoothing_sigma)

            # Calculate derivatives using finite differences
            dx = np.gradient(x)
            dy = np.gradient(y)

            # Second derivatives
            d2x = np.gradient(dx)
            d2y = np.gradient(dy)

            # Calculate curvature
            denominator = (dx * dx + dy * dy)**1.5
            curvature = np.zeros_like(x)
            valid_indices = denominator > 1e-10
            curvature[valid_indices] = (dx[valid_indices] * d2y[valid_indices] -
                                      dy[valid_indices] * d2x[valid_indices]) / denominator[valid_indices]

            # Create smoothed contour
            smoothed_contour = np.column_stack((x, y))

            print(f"Curvature calculated with {len(curvature)} points")
            print(f"Curvature range: [{np.min(curvature)}, {np.max(curvature)}]")

            return curvature, smoothed_contour

    except Exception as e:
        print(f"Error in curvature calculation: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def plot_results(cell_image, piezo_image, edge_image, intensities, points,
                normals, curvature, smoothed_contour):
    """Create and save analysis figures."""
    # Figure 1: Edge Detection
    plt.figure(figsize=(10, 10))
    plt.imshow(cell_image, cmap='gray')
    # Create a blue edge overlay
    edge_overlay = np.zeros((*cell_image.shape, 4))  # RGBA
    edge_overlay[edge_image > 0] = [0, 0, 1, 0.5]  # Blue with alpha=0.5
    plt.imshow(edge_overlay)
    plt.title('Cell Edge Detection')
    plt.axis('equal')
    plt.savefig('figure1_edge_detection.png')
    plt.close()

    # Figure 2: Sampling Vectors
    plt.figure(figsize=(10, 10))
    plt.imshow(piezo_image, cmap='viridis')
    # Plot sampling vectors
    for point, normal in zip(points, normals):
        end_point = point + normal * 20
        plt.plot([point[0], end_point[0]],
                [point[1], end_point[1]], 'y-', alpha=0.5)
    # Plot smoothed contour
    plt.plot(smoothed_contour[:, 0], smoothed_contour[:, 1], 'b--', alpha=0.5)
    plt.title('PIEZO1 Signal with Sampling Vectors')
    plt.axis('equal')
    plt.savefig('figure2_sampling_vectors.png')
    plt.close()

    # Figure 3: Intensity and Curvature Profiles
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # Intensity profile
    ax1.plot(intensities, 'b-')
    ax1.set_title('Edge Intensity Profile')
    ax1.set_xlabel('Position along edge')
    ax1.set_ylabel('Intensity')
    ax1.grid(True)

    # Curvature profile
    ax2.plot(curvature, 'r-')
    ax2.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    ax2.set_title('Edge Curvature Profile')
    ax2.set_xlabel('Position along edge')
    ax2.set_ylabel('Curvature')
    ax2.grid(True)

    plt.tight_layout()
    plt.savefig('figure3_profiles.png')
    plt.close()

    # Figure 4: Correlation
    plt.figure(figsize=(8, 8))
    plt.scatter(curvature, intensities, c='purple', alpha=0.5)
    plt.title('Intensity vs Curvature')
    plt.xlabel('Curvature')
    plt.ylabel('Intensity')
    correlation = np.corrcoef(curvature, intensities)[0, 1]
    plt.text(0.05, 0.95, f'r = {correlation:.3f}',
            transform=plt.gca().transAxes,
            verticalalignment='top')
    plt.grid(True)
    plt.savefig('figure4_correlation.png')
    plt.close()

    print("All figures saved successfully")

def main():
    try:
        # File paths - replace with your actual file paths
        cell_path = "/Users/george/Documents/python_projects/cell_edge_analysis/151_2019_07_29_TIRF_mKera_scratch_Pos7_DIC_Mask_test.tif"
        piezo_path = "/Users/george/Documents/python_projects/cell_edge_analysis/151_2019_07_29_TIRF_mKera_scratch_1_MMStack_Pos7_piezo1.tif"

        # Load first frames
        print("Loading image data...")
        cell_frame, piezo_frame = load_first_frames(cell_path, piezo_path)

        # Detect cell edge
        print("Detecting cell edge...")
        edge_image, contour = detect_cell_edge(cell_frame)
        if edge_image is None:
            print("Error: No cell edge detected")
            return

        print(f"Edge detected with {len(contour)} points")

        # Analyze edge intensity
        print("Analyzing edge intensity...")
        result = analyze_edge_intensity(piezo_frame, contour)
        if result[0] is None:
            print("Error: Intensity analysis failed")
            return
        intensities, points, normals = result

        print(f"Analyzed {len(points)} measurement points")

        # Calculate curvature at intensity measurement points
        print("Calculating edge curvature...")
        curvature, smoothed_contour = calculate_curvature(contour, intensity_points=points)
        if curvature is None:
            print("Error: Curvature calculation failed")
            return

        print(f"Calculated curvature at {len(curvature)} points")

        # Create figures
        print("Creating figures...")
        plot_results(cell_frame, piezo_frame, edge_image, intensities, points,
                    normals, curvature, smoothed_contour)

        print("Analysis complete. Figures have been saved.")

    except Exception as e:
        print(f"Error in analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
