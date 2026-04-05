"""Tests for opencartograph.cli."""

from __future__ import annotations

import pytest

from opencartograph.cli import build_parser, main


class TestBuildParser:
    def test_all_args_present(self):
        parser = build_parser()
        # Parse with all required args
        args = parser.parse_args(["--city", "Paris", "--country", "France"])
        assert args.city == "Paris"
        assert args.country == "France"

    def test_short_flags(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "Tokyo", "-C", "Japan", "-t", "noir"])
        assert args.city == "Tokyo"
        assert args.country == "Japan"
        assert args.theme == "noir"

    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y"])
        assert args.theme == "terracotta"
        assert args.distance == 18000
        assert args.width is None
        assert args.height is None
        assert args.format == "png"

    def test_quality_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y", "--quality", "low"])
        assert args.quality == "low"

    def test_quality_short_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y", "-q", "ultra"])
        assert args.quality == "ultra"

    def test_quality_default_none(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y"])
        assert args.quality is None

    def test_quality_invalid_rejected(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-c", "X", "-C", "Y", "-q", "invalid"])

    def test_output_dir_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y", "--output-dir", "/tmp/my_posters"])
        assert args.output_dir == "/tmp/my_posters"

    def test_output_dir_short_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y", "-o", "/tmp/out"])
        assert args.output_dir == "/tmp/out"

    def test_output_dir_default_none(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y"])
        assert args.output_dir is None

    def test_all_themes_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y", "--all-themes"])
        assert args.all_themes is True

    def test_list_themes_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--list-themes"])
        assert args.list_themes is True

    def test_display_city_and_country(self):
        parser = build_parser()
        args = parser.parse_args([
            "-c", "Tokyo", "-C", "Japan",
            "-dc", "東京", "-dC", "日本",
        ])
        assert args.display_city == "東京"
        assert args.display_country == "日本"

    def test_font_family(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y", "--font-family", "Noto Sans JP"])
        assert args.font_family == "Noto Sans JP"

    def test_format_choices(self):
        parser = build_parser()
        for fmt in ["png", "svg", "pdf"]:
            args = parser.parse_args(["-c", "X", "-C", "Y", "-f", fmt])
            assert args.format == fmt

    def test_invalid_format(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-c", "X", "-C", "Y", "-f", "bmp"])

    def test_no_text_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y", "--no-text"])
        assert args.no_text is True

    def test_no_text_default_false(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y"])
        assert args.no_text is False

    def test_line_scale_flag(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y", "--line-scale", "2.5"])
        assert args.line_scale == 2.5

    def test_line_scale_default(self):
        parser = build_parser()
        args = parser.parse_args(["-c", "X", "-C", "Y"])
        assert args.line_scale == 1.0

    def test_latitude_longitude(self):
        parser = build_parser()
        args = parser.parse_args([
            "-c", "X", "-C", "Y",
            "-lat", "40.7128", "-long", "-74.0060",
        ])
        assert args.latitude == "40.7128"
        assert args.longitude == "-74.0060"


class TestMain:
    def test_list_themes_returns_0(self):
        result = main(["--list-themes"])
        assert result == 0

    def test_zero_line_scale_returns_1(self):
        result = main(["--city", "X", "--country", "Y", "--line-scale", "0"])
        assert result == 1

    def test_negative_line_scale_returns_1(self):
        result = main(["--city", "X", "--country", "Y", "--line-scale", "-1"])
        assert result == 1

    def test_quality_preset_applies_dimensions_and_dpi(self):
        from unittest.mock import patch
        from opencartograph.models import Coordinates
        coords = Coordinates(latitude=48.8, longitude=2.3)
        with patch("opencartograph.cli.get_coordinates", return_value=coords), \
             patch("opencartograph.cli.compose_poster") as mock_compose:
            main(["--city", "Paris", "--country", "France", "-q", "low"])
            config = mock_compose.call_args[0][0]
            assert config.width == 6.0
            assert config.height == 8.0
            assert config.dpi == 150

    def test_quality_preset_overridden_by_explicit_width(self):
        from unittest.mock import patch
        from opencartograph.models import Coordinates
        coords = Coordinates(latitude=48.8, longitude=2.3)
        with patch("opencartograph.cli.get_coordinates", return_value=coords), \
             patch("opencartograph.cli.compose_poster") as mock_compose:
            main(["--city", "Paris", "--country", "France", "-q", "low", "-W", "10"])
            config = mock_compose.call_args[0][0]
            assert config.width == 10.0  # explicit override
            assert config.height == 8.0  # from preset
            assert config.dpi == 150     # from preset

    def test_missing_city_returns_1(self):
        result = main(["--country", "France"])
        assert result == 1

    def test_missing_country_returns_1(self):
        result = main(["--city", "Paris"])
        assert result == 1

    def test_invalid_theme_returns_1(self):
        result = main(["--city", "Paris", "--country", "France", "--theme", "nonexistent_theme_xyz"])
        assert result == 1
