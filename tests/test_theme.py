"""Tests for opencartograph.theme."""

from __future__ import annotations

from pathlib import Path

import pytest

from opencartograph.theme import get_available_themes, list_themes, load_theme


class TestGetAvailableThemes:
    def test_returns_sorted_list(self, themes_dir):
        themes = get_available_themes(Path(themes_dir))
        assert themes == ["alpha", "beta"]

    def test_empty_dir(self, tmp_path):
        empty = tmp_path / "empty_themes"
        empty.mkdir()
        themes = get_available_themes(empty)
        assert themes == []

    def test_nonexistent_dir_creates_it(self, tmp_path):
        new_dir = tmp_path / "new_themes"
        themes = get_available_themes(new_dir)
        assert themes == []
        assert new_dir.exists()

    def test_ignores_non_json(self, tmp_path):
        themes = tmp_path / "themes"
        themes.mkdir()
        (themes / "readme.txt").write_text("not a theme")
        (themes / "test.json").write_text('{"name": "Test"}')
        result = get_available_themes(themes)
        assert result == ["test"]


    def test_finds_themes_in_subdirectories(self, tmp_path):
        themes = tmp_path / "themes"
        themes.mkdir()
        (themes / "top.json").write_text('{"name": "Top"}')
        custom = themes / "custom"
        custom.mkdir()
        (custom / "deep.json").write_text('{"name": "Deep"}')
        result = get_available_themes(themes)
        assert "top" in result
        assert "custom/deep" in result

    def test_subdirectory_themes_sorted(self, tmp_path):
        themes = tmp_path / "themes"
        themes.mkdir()
        (themes / "zebra.json").write_text('{"name": "Z"}')
        sub = themes / "aaa"
        sub.mkdir()
        (sub / "first.json").write_text('{"name": "F"}')
        result = get_available_themes(themes)
        assert result == ["aaa/first", "zebra"]


class TestLoadTheme:
    def test_loads_valid_theme(self, themes_dir):
        theme = load_theme("alpha", Path(themes_dir))
        assert theme.name == "Alpha"

    def test_loads_subdirectory_theme(self, tmp_path, sample_theme_data):
        import json
        themes = tmp_path / "themes"
        sub = themes / "custom"
        sub.mkdir(parents=True)
        (sub / "my_theme.json").write_text(json.dumps(sample_theme_data))
        theme = load_theme("custom/my_theme", themes)
        assert theme.name == "Test Theme"

    def test_missing_theme_raises_error(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="not found"):
            load_theme("nonexistent", tmp_path)

    def test_invalid_json_raises_valueerror(self, tmp_path):
        import pytest
        bad_file = tmp_path / "broken.json"
        bad_file.write_text("{invalid json")
        with pytest.raises(ValueError, match="invalid JSON"):
            load_theme("broken", tmp_path)

    def test_missing_required_field_raises_valueerror(self, tmp_path):
        import pytest
        incomplete = tmp_path / "incomplete.json"
        incomplete.write_text('{"name": "Test", "description": "Missing fields"}')
        with pytest.raises(ValueError, match="missing required field"):
            load_theme("incomplete", tmp_path)

    def test_theme_has_road_colors(self, themes_dir):
        theme = load_theme("alpha", Path(themes_dir))
        assert theme.roads.motorway == "#FF0000"


class TestListThemes:
    def test_prints_themes(self, themes_dir, capsys):
        list_themes(Path(themes_dir))
        captured = capsys.readouterr()
        assert "alpha" in captured.out
        assert "beta" in captured.out

    def test_empty_dir(self, tmp_path, capsys):
        empty = tmp_path / "empty"
        empty.mkdir()
        list_themes(empty)
        captured = capsys.readouterr()
        assert "No themes found" in captured.out
