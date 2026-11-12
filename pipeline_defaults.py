"""Pipeline defaults: the ONE place every entry point reads them from.

run_all_steps.py (PIPELINE_CONFIG), each stepN_*.py script's CONFIG, the Tk GUI's initial widget values and the web
app (web/analysis.py) all take their defaults from DEFAULTS. Change a value here and every entry point follows.
Keys match the step scripts' command-line options (key 'a_b' -> --a-b). Lengths are in pixels.
"""
import copy

FILE_PATTERNS = {
    'IMAGE_PATTERNS': ['*piezo1.tif', '*Piezo1.tif', '*PIEZO1.tif'],
    'MASK_PATTERNS': ['*Mask.tif', '*mask.tif', '*MASK.tif'],
}

DEFAULTS = {
    # Step 1: Data Loading
    'step1': {
        'normalize_frames': True,
        'normalization_scale': 100.0,  # Scaling factor after normalization
        'subtract_background': True,  # Subtract background before normalization
        'background_percentile': 10,  # Percentile for background (0-100)
        'create_verification_figures': True
    },
    # Step 2: Edge Detection
    'step2': {
        'smooth_edges': True,  # Apply Gaussian smoothing to edges
        'smoothing_sigma': 20.0,  # Sigma for Gaussian smoothing (higher = more smoothing)
        'create_verification_figures': True
    },
    # Step 3: Displacement Calculation
    'step3': {
        'min_movement_pixels': 5,
        'arrow_scale': 1,
        'arrow_head_width': 40,
        'arrow_head_length': 15,
        'arrow_point_forward': True,
        'create_verification_figures': True
    },
    # Step 4: Movement Classification
    'step4': {
        'movement_threshold': 5,
        'show_edges': True,
        'show_arrows': True,
        'arrow_scale': 1,
        'arrow_head_width': 20,
        'arrow_head_length': 10,
        'arrow_point_forward': True,
        'create_verification_figures': True
    },
    # Step 5: Edge Sampling
    'step5': {
        'n_points': 12,  # for per_frame and fixed_x
        'exclude_endpoints': True,
        'sampling_method': 'displacement_like',  # Options: per_frame, fixed_x, dense, displacement_like
        'target_points_displacement': 20,
        'y_selection': 'uppermost',  # Options: uppermost, lowermost
        'create_verification_figures': True
    },
    # Step 6: Sampling Rectangles
    'step6': {
        'depth': 50,
        'width': 25,
        'min_cell_coverage': 0.8,
        'rotation_method': 'vertical',  # Options: none, flip, search, vertical
        'rotation_search_angles': 18,
        'create_verification_figures': True
    },
    # Step 7: Intensity Extraction
    'step7': {
        'show_edge': True,
        'create_verification_figures': True
    },
    # Step 8: Movement Assignment
    'step8': {
        'temporal_direction': 'future',  # Options: past, future
        'create_verification_figures': True
    },
    # Step 9: Correlation Analysis
    'step9': {
        'binning_method': 'equal_count',  # Options: equal_count, equal_width, dynamic
        'n_bins': 10,
        'min_bin_count': 5,
        'movement_threshold': 5,  # Should match step4
        'create_verification_figures': True
    },
}


def step_defaults(step):
    """A copy of one step's defaults, e.g. step_defaults('step5')."""
    return copy.deepcopy(DEFAULTS[step])
