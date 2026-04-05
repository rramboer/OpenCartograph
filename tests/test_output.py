"""Tests for opencartograph.output."""

from __future__ import annotations

import re

from opencartograph.output import generate_output_filename


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
