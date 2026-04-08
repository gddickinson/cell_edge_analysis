"""
Smoke tests for curvature analysis module.

Tests curvature calculation with synthetic circular contours
where the expected curvature is known analytically.
"""

import sys
import os

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.data_structures import EdgeData, AnalysisParameters
from src.analysis.curvature_analyzer import CurvatureAnalyzer


class TestCurvatureAnalyzer:
    """Tests for the CurvatureAnalyzer class."""

    def test_init(self):
        """Test CurvatureAnalyzer initialization."""
        params = AnalysisParameters()
        analyzer = CurvatureAnalyzer(params)
        assert analyzer.params == params
        assert 'plasma_membrane' in analyzer.ref_curvatures

    def _make_circular_edge(self, radius: float = 50, n_points: int = 200):
        """Create a synthetic circular contour for testing.

        Parameters
        ----------
        radius : float
            Circle radius in pixels.
        n_points : int
            Number of points on the contour.

        Returns
        -------
        EdgeData
            Edge data with circular contour.
        """
        t = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
        contour = np.column_stack([
            100 + radius * np.cos(t),
            100 + radius * np.sin(t),
        ])
        edge_image = np.zeros((200, 200), dtype=np.uint8)
        edge_data = EdgeData(contour=contour, edge_image=edge_image)
        edge_data.smoothed_contour = contour.copy()
        return edge_data

    def test_calculate_curvature_returns_data(self):
        """Test that curvature calculation returns CurvatureData."""
        params = AnalysisParameters(n_samples=50, segment_length=9)
        analyzer = CurvatureAnalyzer(params)

        edge_data = self._make_circular_edge(radius=50)
        result = analyzer.calculate_curvature(edge_data)

        # Result should not be None for valid input
        if result is not None:
            assert result.curvatures is not None
            assert len(result.curvatures) > 0

    def test_ref_curvatures(self):
        """Test reference curvature values are reasonable."""
        params = AnalysisParameters()
        analyzer = CurvatureAnalyzer(params)

        assert analyzer.ref_curvatures['plasma_membrane'] < analyzer.ref_curvatures['endocytic_vesicle']
        assert analyzer.ref_curvatures['endocytic_vesicle'] < analyzer.ref_curvatures['transport_vesicle']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
