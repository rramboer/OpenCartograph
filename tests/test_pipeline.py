"""Tests for opencartograph.rendering.pipeline."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import MagicMock, patch

from opencartograph.rendering.pipeline import MapData, compose_poster


class TestComposePoster:
    """Test that compose_poster conditionally renders typography."""

    @patch("opencartograph.rendering.pipeline.plt")
    @patch("opencartograph.rendering.pipeline.save_poster")
    @patch("opencartograph.rendering.pipeline.render_typography")
    @patch("opencartograph.rendering.pipeline.render_gradients")
    @patch("opencartograph.rendering.pipeline.apply_viewport")
    @patch("opencartograph.rendering.pipeline.render_roads")
    @patch("opencartograph.rendering.pipeline.render_parks")
    @patch("opencartograph.rendering.pipeline.render_water")
    @patch("opencartograph.rendering.pipeline.render_ocean")
    @patch("opencartograph.rendering.pipeline.build_ocean_polygons", return_value=None)
    @patch("opencartograph.rendering.pipeline.get_crop_limits", return_value=((0, 1), (0, 1)))
    @patch("opencartograph.rendering.pipeline.ox.project_graph")
    @patch("opencartograph.rendering.pipeline.setup_figure")
    @patch("opencartograph.rendering.pipeline.fetch_map_data")
    def test_typography_rendered_when_no_text_false(
        self, mock_fetch, mock_setup, mock_project, mock_crop,
        mock_build_ocean, mock_render_ocean, mock_water, mock_parks,
        mock_roads, mock_viewport, mock_gradients, mock_typo,
        mock_save, mock_plt, sample_config,
    ):
        mock_fetch.return_value = MapData(
            graph=MagicMock(), water=None, parks=None,
            national_parks=None, airports=None, runways=None,
            buildings=None, stadiums=None, coastline=None,
        )
        mock_setup.return_value = (MagicMock(), MagicMock())

        config = replace(sample_config, no_text=False)
        compose_poster(config)

        mock_typo.assert_called_once()

    @patch("opencartograph.rendering.pipeline.plt")
    @patch("opencartograph.rendering.pipeline.save_poster")
    @patch("opencartograph.rendering.pipeline.render_typography")
    @patch("opencartograph.rendering.pipeline.render_gradients")
    @patch("opencartograph.rendering.pipeline.apply_viewport")
    @patch("opencartograph.rendering.pipeline.render_roads")
    @patch("opencartograph.rendering.pipeline.render_parks")
    @patch("opencartograph.rendering.pipeline.render_water")
    @patch("opencartograph.rendering.pipeline.render_ocean")
    @patch("opencartograph.rendering.pipeline.build_ocean_polygons", return_value=None)
    @patch("opencartograph.rendering.pipeline.get_crop_limits", return_value=((0, 1), (0, 1)))
    @patch("opencartograph.rendering.pipeline.ox.project_graph")
    @patch("opencartograph.rendering.pipeline.setup_figure")
    @patch("opencartograph.rendering.pipeline.fetch_map_data")
    def test_typography_skipped_when_no_text_true(
        self, mock_fetch, mock_setup, mock_project, mock_crop,
        mock_build_ocean, mock_render_ocean, mock_water, mock_parks,
        mock_roads, mock_viewport, mock_gradients, mock_typo,
        mock_save, mock_plt, sample_config,
    ):
        mock_fetch.return_value = MapData(
            graph=MagicMock(), water=None, parks=None,
            national_parks=None, airports=None, runways=None,
            buildings=None, stadiums=None, coastline=None,
        )
        mock_setup.return_value = (MagicMock(), MagicMock())

        config = replace(sample_config, no_text=True)
        compose_poster(config)

        mock_typo.assert_not_called()
