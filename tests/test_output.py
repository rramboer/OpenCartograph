"""Tests for opencartograph.output."""

from __future__ import annotations

import re
from unittest.mock import patch, MagicMock

from opencartograph.output import generate_output_filename, save_poster
from opencartograph.models import Coordinates, PosterConfig, Theme, RoadColors


class TestGenerateOutputFilename:
    def test_format_png(self, tmp_path):
        result = generate_output_filename("Paris", "noir", "png", output_dir=str(tmp_path))
        assert result.endswith(".png")
        assert "paris" in result
        assert "noir" in result

    def test_format_svg(self, tmp_path):
        result = generate_output_filename("London", "ocean", "svg", output_dir=str(tmp_path))
        assert result.endswith(".svg")

    def test_city_with_spaces(self, tmp_path):
        result = generate_output_filename("New York", "noir", "png", output_dir=str(tmp_path))
        assert "new_york" in result

    def test_creates_directory(self, tmp_path):
        out_dir = tmp_path / "new_output"
        generate_output_filename("Paris", "noir", "png", output_dir=str(out_dir))
        assert out_dir.exists()

    def test_timestamp_in_filename(self, tmp_path):
        result = generate_output_filename("Paris", "noir", "png", output_dir=str(tmp_path))
        assert re.search(r"\d{8}_\d{6}", result)

    def test_custom_output_dir(self, tmp_path):
        custom = tmp_path / "my_posters"
        result = generate_output_filename("Paris", "noir", "png", output_dir=str(custom))
        assert str(custom) in result


def _make_config(output_format: str = "png", dpi: int = 300, tmp_path: str = "/tmp") -> PosterConfig:
    """Create a minimal PosterConfig for testing."""
    theme = Theme(
        name="test",
        description="test theme",
        bg="#ffffff",
        text="#000000",
        gradient_color="#cccccc",
        water="#0000ff",
        parks="#00ff00",
        national_parks="#008800",
        airports="#ffff00",
        runways="#888888",
        buildings="#cccccc",
        stadiums="#00ffaa",
        roads=RoadColors(
            motorway="#333", primary="#444", secondary="#555",
            tertiary="#666", residential="#777", default="#888",
        ),
    )
    return PosterConfig(
        city="Paris",
        country="France",
        center=Coordinates(latitude=48.8, longitude=2.3),
        dist=18000,
        width=12.0,
        height=16.0,
        theme=theme,
        fonts=None,
        output_file=f"{tmp_path}/test.{output_format}",
        output_format=output_format,
        display_city="Paris",
        display_country="France",
        dpi=dpi,
    )


class TestSavePoster:
    @patch("opencartograph.output.plt")
    def test_png_uses_config_dpi(self, mock_plt):
        config = _make_config(output_format="png", dpi=600)
        save_poster(MagicMock(), config)
        call_kwargs = mock_plt.savefig.call_args[1]
        assert call_kwargs["dpi"] == 600

    @patch("opencartograph.output.plt")
    def test_pdf_uses_config_dpi(self, mock_plt):
        config = _make_config(output_format="pdf", dpi=600)
        save_poster(MagicMock(), config)
        call_kwargs = mock_plt.savefig.call_args[1]
        assert call_kwargs["dpi"] == 600

    @patch("opencartograph.output.plt")
    def test_svg_does_not_include_dpi(self, mock_plt):
        config = _make_config(output_format="svg", dpi=600)
        save_poster(MagicMock(), config)
        call_kwargs = mock_plt.savefig.call_args[1]
        assert "dpi" not in call_kwargs
