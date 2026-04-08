"""
Smoke tests for edge detection module.

Tests basic edge detection functionality with synthetic data.
"""

import sys
import os

import numpy as np
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.data_structures import ImageData, AnalysisParameters
from src.analysis.edge_detection import EdgeDetector


class TestEdgeDetector:
    """Tests for the EdgeDetector class."""

    def test_init(self):
        """Test EdgeDetector initialization."""
        params = AnalysisParameters()
        detector = EdgeDetector(params)
        assert detector.params == params

    def test_detect_edge_from_circle(self):
        """Test edge detection from a synthetic circular mask."""
        params = AnalysisParameters(min_size=50, smoothing_sigma=0)
        detector = EdgeDetector(params)

        # Create a synthetic binary mask with a filled circle
        mask = np.zeros((200, 200), dtype=np.uint8)
        y, x = np.ogrid[-100:100, -100:100]
        circle = (x ** 2 + y ** 2 <= 60 ** 2)
        mask[circle] = 255

        image_data = ImageData(data=mask, filename="test_circle.tif")
        edge_data = detector.detect_edge(image_data)

        assert edge_data is not None
        assert edge_data.contour is not None
        assert len(edge_data.contour) > 10
        assert edge_data.edge_image.shape == (200, 200)

    def test_detect_edge_empty_image(self):
        """Test edge detection returns None for empty image."""
        params = AnalysisParameters(min_size=50)
        detector = EdgeDetector(params)

        mask = np.zeros((100, 100), dtype=np.uint8)
        image_data = ImageData(data=mask, filename="test_empty.tif")
        edge_data = detector.detect_edge(image_data)

        assert edge_data is None

    def test_get_normal_vectors(self):
        """Test normal vector calculation."""
        params = AnalysisParameters(min_size=50, smoothing_sigma=0)
        detector = EdgeDetector(params)

        # Create circular mask for clean contour
        mask = np.zeros((200, 200), dtype=np.uint8)
        y, x = np.ogrid[-100:100, -100:100]
        circle = (x ** 2 + y ** 2 <= 60 ** 2)
        mask[circle] = 255

        image_data = ImageData(data=mask, filename="test.tif")
        edge_data = detector.detect_edge(image_data)

        if edge_data is not None:
            normals = detector.get_normal_vectors(edge_data, smooth=False)
            assert normals.shape[0] == len(edge_data.contour)
            assert normals.shape[1] == 2

            # Normal vectors should be unit vectors (approximately)
            magnitudes = np.linalg.norm(normals, axis=1)
            # Filter out zero-length tangents
            nonzero = magnitudes > 0
            np.testing.assert_allclose(magnitudes[nonzero], 1.0, atol=1e-6)

    def test_get_sampling_points(self):
        """Test sampling point generation."""
        params = AnalysisParameters(min_size=50, smoothing_sigma=1.0)
        detector = EdgeDetector(params)

        mask = np.zeros((200, 200), dtype=np.uint8)
        y, x = np.ogrid[-100:100, -100:100]
        circle = (x ** 2 + y ** 2 <= 60 ** 2)
        mask[circle] = 255

        image_data = ImageData(data=mask, filename="test.tif")
        edge_data = detector.detect_edge(image_data)

        if edge_data is not None:
            n_samples = 20
            points, normals = detector.get_sampling_points(edge_data, n_samples)

            assert points.shape == (n_samples, 2)
            assert normals.shape == (n_samples, 2)

    def test_debug_edge_detection(self):
        """Test debug info generation."""
        params = AnalysisParameters(min_size=50, smoothing_sigma=0)
        detector = EdgeDetector(params)

        mask = np.zeros((200, 200), dtype=np.uint8)
        y, x = np.ogrid[-100:100, -100:100]
        circle = (x ** 2 + y ** 2 <= 60 ** 2)
        mask[circle] = 255

        image_data = ImageData(data=mask, filename="test.tif")
        edge_data = detector.detect_edge(image_data)

        if edge_data is not None:
            debug = detector.debug_edge_detection(image_data, edge_data)
            assert 'n_points' in debug
            assert 'warnings' in debug


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
