#!/usr/bin/env python3
# src/utils/image_processing.py

import numpy as np
import cv2
from scipy import ndimage
from skimage import filters, morphology, measure
from typing import Optional, Tuple, List
from ..utils.data_structures import ImageData

class ImageProcessor:
    """Class for handling common image processing operations."""
    
    @staticmethod
    def normalize_image(image: np.ndarray) -> np.ndarray:
        """Normalize image to 0-1 range."""
        if image.dtype == bool:
            return image.astype(np.float32)
            
        img_min = np.min(image)
        img_max = np.max(image)
        
        if img_max == img_min:
            return np.zeros_like(image, dtype=np.float32)
            
        return ((image - img_min) / (img_max - img_min)).astype(np.float32)

    @staticmethod
    def enhance_contrast(
        image: np.ndarray,
        percentile_low: float = 1,
        percentile_high: float = 99
    ) -> np.ndarray:
        """Enhance image contrast using percentile-based normalization."""
        p_low = np.percentile(image, percentile_low)
        p_high = np.percentile(image, percentile_high)
        
        enhanced = np.clip(image, p_low, p_high)
        return ImageProcessor.normalize_image(enhanced)

    @staticmethod
    def denoise_image(
        image: np.ndarray,
        method: str = 'gaussian',
        sigma: float = 1.0
    ) -> np.ndarray:
        """Apply denoising to image."""
        if method == 'gaussian':
            return filters.gaussian(image, sigma=sigma)
        elif method == 'median':
            return filters.median(image, morphology.disk(int(sigma)))
        elif method == 'bilateral':
            # Convert to uint8 for bilateral filter
            img_norm = (ImageProcessor.normalize_image(image) * 255).astype(np.uint8)
            return cv2.bilateralFilter(img_norm, d=int(sigma), sigmaColor=75, sigmaSpace=75)
        else:
            raise ValueError(f"Unknown denoising method: {method}")

    @staticmethod
    def segment_cells(
        image: np.ndarray,
        threshold_method: str = 'otsu',
        min_size: int = 100,
        remove_border: bool = True
    ) -> np.ndarray:
        """Segment cells from background."""
        # Normalize and denoise
        img_norm = ImageProcessor.normalize_image(image)
        img_smooth = ImageProcessor.denoise_image(img_norm, method='gaussian', sigma=1.0)
        
        # Apply thresholding
        if threshold_method == 'otsu':
            threshold = filters.threshold_otsu(img_smooth)
        elif threshold_method == 'adaptive':
            threshold = filters.threshold_local(img_smooth, block_size=35, method='gaussian')
        else:
            raise ValueError(f"Unknown thresholding method: {threshold_method}")
            
        binary = img_smooth > threshold
        
        # Clean up binary image
        binary = morphology.remove_small_objects(binary, min_size=min_size)
        binary = morphology.remove_small_holes(binary, min_size=min_size)
        
        if remove_border:
            binary = morphology.clear_border(binary)
            
        return binary

    @staticmethod
    def extract_largest_cell(binary_image: np.ndarray) -> np.ndarray:
        """Extract the largest connected component."""
        labels = measure.label(binary_image)
        if labels.max() == 0:
            return np.zeros_like(binary_image)
            
        largest_component = None
        max_area = 0
        
        for region in measure.regionprops(labels):
            if region.area > max_area:
                max_area = region.area
                largest_component = region.label
                
        return labels == largest_component

    @staticmethod
    def measure_intensity_profile(
        image: np.ndarray,
        mask: np.ndarray,
        distance_bins: int = 50
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Measure intensity profile from cell edge."""
        # Calculate distance transform
        distance = ndimage.distance_transform_edt(~mask)
        
        # Create distance bins
        max_distance = np.max(distance)
        bin_edges = np.linspace(0, max_distance, distance_bins + 1)
        bin_centers = (bin_edges[1:] + bin_edges[:-1]) / 2
        
        # Measure mean intensity in each distance bin
        intensities = []
        for i in range(len(bin_centers)):
            bin_mask = (distance >= bin_edges[i]) & (distance < bin_edges[i+1])
            if np.any(bin_mask):
                mean_intensity = np.mean(image[bin_mask])
                intensities.append(mean_intensity)
            else:
                intensities.append(0)
                
        return bin_centers, np.array(intensities)

    @staticmethod
    def analyze_cell_morphology(
        binary_image: np.ndarray
    ) -> dict:
        """Analyze cell morphology metrics."""
        # Get cell contour
        contours, _ = cv2.findContours(
            binary_image.astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_NONE
        )
        
        if not contours:
            return {}
            
        contour = max(contours, key=cv2.contourArea)
        
        # Calculate metrics
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
        
        # Fit ellipse
        if len(contour) >= 5:
            (x, y), (major, minor), angle = cv2.fitEllipse(contour)
            eccentricity = np.sqrt(1 - (minor/major)**2) if major > 0 else 0
        else:
            eccentricity = 0
            angle = 0
            
        return {
            'area': area,
            'perimeter': perimeter,
            'circularity': circularity,
            'eccentricity': eccentricity,
            'orientation': angle
        }

    @staticmethod
    def measure_background(
        image: np.ndarray,
        mask: np.ndarray,
        margin: int = 10
    ) -> dict:
        """Measure background statistics."""
        # Dilate mask to create background region
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (margin*2+1, margin*2+1))
        dilated = cv2.dilate(mask.astype(np.uint8), kernel)
        
        # Background is region outside dilated mask
        background_mask = ~dilated.astype(bool)
        background_values = image[background_mask]
        
        if len(background_values) == 0:
            return {
                'mean': 0,
                'std': 0,
                'median': 0
            }
            
        return {
            'mean': np.mean(background_values),
            'std': np.std(background_values),
            'median': np.median(background_values)
        }

    @staticmethod
    def correct_illumination(
        image: np.ndarray,
        sigma: float = 50.0
    ) -> np.ndarray:
        """Correct uneven illumination using background estimation."""
        # Estimate background using large-scale Gaussian blur
        background = filters.gaussian(image, sigma=sigma)
        
        # Subtract background and rescale
        corrected = image - background
        corrected = corrected - np.min(corrected)
        
        if np.max(corrected) > 0:
            corrected = corrected / np.max(corrected)
            
        return corrected

    @staticmethod
    def detect_focus_quality(image: np.ndarray) -> float:
        """Estimate image focus quality using variance of Laplacian."""
        return cv2.Laplacian(image.astype(np.float32), cv2.CV_64F).var()

    @staticmethod
    def validate_image_pair(
        image1: ImageData,
        image2: ImageData
    ) -> bool:
        """Validate that two images are compatible for analysis."""
        if image1.data.shape != image2.data.shape:
            return False
            
        if image1.is_stack != image2.is_stack:
            return False
            
        if image1.is_stack and image1.data.shape[0] != image2.data.shape[0]:
            return False
            
        return True