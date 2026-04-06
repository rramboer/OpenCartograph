"""Tests for opencartograph.theme."""

from __future__ import annotations

import json
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

    def test_finds_deeply_nested_themes(self, tmp_path):
        themes = tmp_path / "themes"
        deep = themes / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "nested.json").write_text('{"name": "Nested"}')
        result = get_available_themes(themes)
        assert "a/b/c/nested" in result

    def test_ignores_non_json_in_subdirectories(self, tmp_path):
        themes = tmp_path / "themes"
        sub = themes / "custom"
        sub.mkdir(parents=True)
        (sub / "readme.txt").write_text("not a theme")
        (sub / "valid.json").write_text('{"name": "Valid"}')
        result = get_available_themes(themes)
        assert result == ["custom/valid"]

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
        themes = tmp_path / "themes"
        sub = themes / "custom"
        sub.mkdir(parents=True)
        (sub / "my_theme.json").write_text(json.dumps(sample_theme_data))
        theme = load_theme("custom/my_theme", themes)
        assert theme.name == "Test Theme"

    def test_path_traversal_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="Invalid theme name"):
            load_theme("../../etc/passwd", tmp_path)

    def test_dotdot_in_subdir_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="Invalid theme name"):
            load_theme("custom/../../../etc/passwd", tmp_path)

    def test_empty_theme_name_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="Invalid theme name"):
            load_theme("", tmp_path)

    def test_dot_theme_name_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="Invalid theme name"):
            load_theme(".", tmp_path)

    def test_slash_only_theme_name_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="Invalid theme name"):
            load_theme("///", tmp_path)

    def test_backslash_traversal_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="Invalid theme name"):
            load_theme("custom\\..\\..\\etc\\passwd", tmp_path)

    def test_symlink_escape_rejected(self, tmp_path):
        themes = tmp_path / "themes"
        themes.mkdir()
        link = themes / "escape"
        try:
            link.symlink_to(tmp_path.parent)
        except (OSError, NotImplementedError) as exc:
            pytest.skip(f"Symlinks not supported: {exc}")
        secret = tmp_path.parent / "secret.json"
        secret.write_text('{"name": "Secret"}')
        with pytest.raises(ValueError, match="resolves outside"):
            load_theme("escape/secret", themes)

    def test_missing_theme_raises_error(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="not found"):
            load_theme("nonexistent", tmp_path)

    def test_invalid_json_raises_valueerror(self, tmp_path):
        bad_file = tmp_path / "broken.json"
        bad_file.write_text("{invalid json")
        with pytest.raises(ValueError, match="invalid JSON"):
            load_theme("broken", tmp_path)

    def test_missing_required_field_raises_valueerror(self, tmp_path):
        incomplete = tmp_path / "incomplete.json"
        incomplete.write_text('{"name": "Test", "description": "Missing fields"}')
        with pytest.raises(ValueError, match="invalid structure"):
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

    def test_prints_subdirectory_themes(self, tmp_path, capsys, sample_theme_data):
        themes = tmp_path / "themes"
        sub = themes / "custom"
        sub.mkdir(parents=True)
        (sub / "deep.json").write_text(json.dumps(sample_theme_data))
        list_themes(themes)
        captured = capsys.readouterr()
        assert "custom/deep" in captured.out

    def test_corrupt_theme_shows_warning(self, tmp_path, capsys):
        themes = tmp_path / "themes"
        sub = themes / "custom"
        sub.mkdir(parents=True)
        (sub / "broken.json").write_text("{invalid json")
        list_themes(themes)
        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "custom/broken" in captured.out

    def test_empty_dir(self, tmp_path, capsys):
        empty = tmp_path / "empty"
        empty.mkdir()
        list_themes(empty)
        captured = capsys.readouterr()
        assert "No themes found" in captured.out
