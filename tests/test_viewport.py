"""Tests for opencartograph.rendering.viewport."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from opencartograph.rendering.viewport import get_crop_limits, setup_figure
from opencartograph.models import Coordinates


def _make_mock_graph(crs="EPSG:32633"):
    g = MagicMock()
    g.graph = {"crs": crs}
    return g


def _make_mock_fig(width_inches, height_inches):
    fig = MagicMock()
    fig.get_size_inches.return_value = (width_inches, height_inches)
    return fig


class TestGetCropLimits:
    @patch("opencartograph.rendering.viewport.ox.projection.project_geometry")
    def test_portrait_reduces_width(self, mock_project):
        mock_point = MagicMock()
        mock_point.x = 500000.0
        mock_point.y = 4000000.0
        mock_project.return_value = (mock_point, None)

        g = _make_mock_graph()
        fig = _make_mock_fig(12.0, 16.0)  # portrait
        center = Coordinates(latitude=40.0, longitude=-74.0)

        xlim, ylim = get_crop_limits(g, center, fig, dist=5000.0)

        # Portrait: width should be reduced, height stays at dist
        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]
        assert y_range == pytest.approx(10000.0)  # 2 * dist
        assert x_range < y_range  # width reduced
        assert x_range == pytest.approx(10000.0 * 12.0 / 16.0)

    @patch("opencartograph.rendering.viewport.ox.projection.project_geometry")
    def test_landscape_reduces_height(self, mock_project):
        mock_point = MagicMock()
        mock_point.x = 500000.0
        mock_point.y = 4000000.0
        mock_project.return_value = (mock_point, None)

        g = _make_mock_graph()
        fig = _make_mock_fig(16.0, 12.0)  # landscape
        center = Coordinates(latitude=40.0, longitude=-74.0)

        xlim, ylim = get_crop_limits(g, center, fig, dist=5000.0)

        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]
        assert x_range == pytest.approx(10000.0)
        assert y_range < x_range
        assert y_range == pytest.approx(10000.0 * 12.0 / 16.0)

    @patch("opencartograph.rendering.viewport.ox.projection.project_geometry")
    def test_square_no_reduction(self, mock_project):
        mock_point = MagicMock()
        mock_point.x = 500000.0
        mock_point.y = 4000000.0
        mock_project.return_value = (mock_point, None)

        g = _make_mock_graph()
        fig = _make_mock_fig(12.0, 12.0)  # square
        center = Coordinates(latitude=40.0, longitude=-74.0)

        xlim, ylim = get_crop_limits(g, center, fig, dist=5000.0)

        x_range = xlim[1] - xlim[0]
        y_range = ylim[1] - ylim[0]
        assert x_range == pytest.approx(y_range)

    @patch("opencartograph.rendering.viewport.ox.projection.project_geometry")
    def test_centered_on_projected_point(self, mock_project):
        mock_point = MagicMock()
        mock_point.x = 100.0
        mock_point.y = 200.0
        mock_project.return_value = (mock_point, None)

        g = _make_mock_graph()
        fig = _make_mock_fig(10.0, 10.0)
        center = Coordinates(latitude=0.0, longitude=0.0)

        xlim, ylim = get_crop_limits(g, center, fig, dist=50.0)

        assert (xlim[0] + xlim[1]) / 2 == pytest.approx(100.0)
        assert (ylim[0] + ylim[1]) / 2 == pytest.approx(200.0)


class TestSetupFigure:
    def test_returns_figure_and_axes(self, sample_config):
        import matplotlib
        matplotlib.use("Agg")
        fig, ax = setup_figure(sample_config)
        assert fig is not None
        assert ax is not None
        w, h = fig.get_size_inches()
        assert w == pytest.approx(sample_config.width)
        assert h == pytest.approx(sample_config.height)
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_axes_fills_figure(self, sample_config):
        import matplotlib
        matplotlib.use("Agg")
        fig, ax = setup_figure(sample_config)
        pos = ax.get_position()
        assert pos.x0 == pytest.approx(0.0)
        assert pos.y0 == pytest.approx(0.0)
        assert pos.width == pytest.approx(1.0)
        assert pos.height == pytest.approx(1.0)
        import matplotlib.pyplot as plt
        plt.close(fig)
