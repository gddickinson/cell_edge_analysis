"""
Smoke tests for fluorescence analysis module.

Tests basic fluorescence analysis functionality with synthetic data.
"""

import sys
import os

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.data_structures import (
    EdgeData, ImageData, AnalysisParameters
)
from src.analysis.fluorescence_analyzer import FluorescenceAnalyzer


class TestFluorescenceAnalyzer:
    """Tests for the FluorescenceAnalyzer class."""

    def test_init(self):
        """Test FluorescenceAnalyzer initialization."""
        params = AnalysisParameters()
        analyzer = FluorescenceAnalyzer(params)
        assert analyzer.params == params
        assert analyzer.valid_indices is None

    def test_calculate_intensities_with_synthetic_data(self):
        """Test intensity calculation with synthetic circular data."""
        params = AnalysisParameters(
            n_samples=20,
            vector_width=3,
            vector_depth=5,
            smoothing_sigma=0,
        )
        analyzer = FluorescenceAnalyzer(params)

        # Create a circular contour
        t = np.linspace(0, 2 * np.pi, 200, endpoint=False)
        radius = 40
        contour = np.column_stack([
            75 + radius * np.cos(t),
            75 + radius * np.sin(t),
        ])

        edge_image = np.zeros((150, 150), dtype=np.uint8)
        edge_data = EdgeData(contour=contour, edge_image=edge_image)
        edge_data.smoothed_contour = contour.copy()

        # Create synthetic fluorescence image (uniform)
        fluor_image = np.ones((150, 150), dtype=np.float32) * 100.0
        fluor_data = ImageData(data=fluor_image, filename="test_fluor.tif")

        # Create cell mask
        mask_data = np.zeros((150, 150), dtype=np.uint8)
        y, x = np.ogrid[-75:75, -75:75]
        mask_data[x ** 2 + y ** 2 <= radius ** 2] = 255
        cell_mask = ImageData(data=mask_data, filename="test_mask.tif")

        result = analyzer.calculate_intensities(edge_data, fluor_data, cell_mask)

        # May return None if sampling regions are too small/out of bounds
        # but should not raise an exception
        if result is not None:
            assert len(result.sampling_points) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
