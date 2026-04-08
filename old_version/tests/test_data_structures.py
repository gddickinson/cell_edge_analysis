"""
Smoke tests for data structures module.

Tests dataclass creation and basic methods.
"""

import sys
import os

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.data_structures import (
    ImageData, EdgeData, CurvatureData, FluorescenceData, AnalysisParameters
)


class TestImageData:
    """Tests for ImageData dataclass."""

    def test_creation(self):
        """Test basic ImageData creation."""
        data = np.zeros((100, 100), dtype=np.uint8)
        img = ImageData(data=data, filename="test.tif")
        assert img.shape == (100, 100)
        assert img.filename == "test.tif"
        assert img.is_stack is False
        assert img.current_frame == 0

    def test_stack(self):
        """Test ImageData with stack flag."""
        data = np.zeros((10, 100, 100), dtype=np.uint8)
        img = ImageData(data=data, filename="stack.tif", is_stack=True)
        assert img.shape == (10, 100, 100)
        assert img.is_stack is True


class TestEdgeData:
    """Tests for EdgeData dataclass."""

    def test_creation(self):
        """Test EdgeData creation."""
        contour = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        edge_image = np.zeros((10, 10), dtype=np.uint8)
        edge = EdgeData(contour=contour, edge_image=edge_image)

        assert len(edge.contour) == 4
        assert edge.smoothed_contour is None

    def test_smooth_contour(self):
        """Test contour smoothing."""
        # Create a noisy circular contour
        t = np.linspace(0, 2 * np.pi, 100, endpoint=False)
        contour = np.column_stack([
            50 + 30 * np.cos(t) + np.random.randn(100),
            50 + 30 * np.sin(t) + np.random.randn(100),
        ])
        edge_image = np.zeros((100, 100), dtype=np.uint8)

        edge = EdgeData(contour=contour, edge_image=edge_image)
        smoothed = edge.smooth_contour(sigma=3.0)

        assert smoothed is not None
        assert smoothed.shape == contour.shape
        # Smoothed should have less variance than original
        assert np.std(smoothed) <= np.std(contour) + 1.0


class TestAnalysisParameters:
    """Tests for AnalysisParameters dataclass."""

    def test_defaults(self):
        """Test default parameter values."""
        params = AnalysisParameters()
        assert params.n_samples == 75
        assert params.smoothing_sigma == 1.0
        assert params.min_size == 100
        assert params.pixel_size == 100.0

    def test_radius_scale(self):
        """Test radius_scale property."""
        params = AnalysisParameters(pixel_size=150.0)
        assert params.radius_scale == 150.0

    def test_custom_params(self):
        """Test custom parameter creation."""
        params = AnalysisParameters(
            n_samples=50,
            segment_length=15,
            vector_width=10,
        )
        assert params.n_samples == 50
        assert params.segment_length == 15
        assert params.vector_width == 10


class TestCurvatureData:
    """Tests for CurvatureData dataclass."""

    def test_creation(self):
        """Test CurvatureData creation."""
        curv = CurvatureData(
            points=np.zeros((10, 2)),
            curvatures=np.zeros(10),
            segment_indices=[[0, 1, 2]],
            ref_curvatures={'test': 0.01},
        )
        assert curv.radius_scale == 100


class TestFluorescenceData:
    """Tests for FluorescenceData dataclass."""

    def test_mean_intensities(self):
        """Test mean_intensities property."""
        sampling_points = [
            {'mean': 10.0, 'center': [0, 0]},
            {'mean': 20.0, 'center': [1, 1]},
        ]
        fluor = FluorescenceData(
            sampling_points=sampling_points,
            intensity_values=np.array([10.0, 20.0]),
            sampling_regions=[np.zeros((5, 5))],
            interior_overlaps=[0.5],
        )
        np.testing.assert_array_equal(fluor.mean_intensities, [10.0, 20.0])

    def test_sampling_coordinates(self):
        """Test sampling_coordinates property."""
        sampling_points = [
            {'mean': 10.0, 'center': [5, 10]},
        ]
        fluor = FluorescenceData(
            sampling_points=sampling_points,
            intensity_values=np.array([10.0]),
            sampling_regions=[np.zeros((5, 5))],
            interior_overlaps=[0.5],
        )
        np.testing.assert_array_equal(fluor.sampling_coordinates, [[5, 10]])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
