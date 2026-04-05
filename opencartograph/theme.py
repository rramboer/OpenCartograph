"""
Theme loading and management.

Themes are JSON files in the themes/ directory that define colors for
all visual elements of the poster.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from . import constants
from .models import Theme


def get_available_themes(themes_dir: Path | None = None) -> list[str]:
    """
    Scan the themes directory and return a list of available theme names.

    Args:
        themes_dir: Override themes directory path

    Returns:
        Sorted list of theme names (without .json extension)
    """
    themes_dir = themes_dir or constants.THEMES_DIR
    if not os.path.exists(themes_dir):
        os.makedirs(themes_dir)
        return []

    themes = []
    for dirpath, _dirnames, filenames in os.walk(themes_dir):
        for file in filenames:
            if file.endswith(".json"):
                rel = os.path.relpath(os.path.join(dirpath, file), themes_dir)
                # Use forward slash as separator and strip .json
                name = rel.replace(os.sep, "/")[:-5]
                themes.append(name)
    return sorted(themes)


def load_theme(
    theme_name: str = "terracotta", themes_dir: Path | None = None
) -> Theme:
    """
    Load theme from JSON file in themes directory.

    Args:
        theme_name: Name of the theme (without .json extension)
        themes_dir: Override themes directory path

    Returns:
        Theme dataclass with all color values
    """
    themes_dir = themes_dir or constants.THEMES_DIR
    # Validate theme name: reject path traversal attempts
    parts = [p for p in theme_name.split("/") if p]
    if not parts or ".." in parts:
        raise ValueError(f"Invalid theme name: {theme_name!r}")
    theme_file = os.path.realpath(os.path.join(themes_dir, *parts) + ".json")
    if not theme_file.startswith(os.path.realpath(str(themes_dir)) + os.sep):
        raise ValueError(f"Invalid theme name: {theme_name!r}")

    if not os.path.exists(theme_file):
        available = get_available_themes(themes_dir)
        raise FileNotFoundError(
            f"Theme file '{theme_file}' not found. "
            f"Available themes: {', '.join(available)}"
        )

    try:
        with open(theme_file, "r", encoding=constants.FILE_ENCODING) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Theme file '{theme_file}' contains invalid JSON: {e}") from e

    try:
        theme = Theme.from_dict(data)
    except KeyError as e:
        raise ValueError(f"Theme file '{theme_file}' is missing required field: {e}") from e

    print(f"\u2713 Loaded theme: {data.get('name', theme_name)}")
    if "description" in data:
        print(f"  {data['description']}")
    return theme


def list_themes(themes_dir: Path | None = None) -> None:
    """
    Print all available themes with descriptions.

    Args:
        themes_dir: Override themes directory path
    """
    themes_dir = themes_dir or constants.THEMES_DIR
    available = get_available_themes(themes_dir)
    if not available:
        print("No themes found in 'themes/' directory.")
        return

    print("\nAvailable Themes:")
    print("-" * 60)
    for theme_name in available:
        theme_path = os.path.join(themes_dir, *theme_name.split("/")) + ".json"
        try:
            with open(theme_path, "r", encoding=constants.FILE_ENCODING) as f:
                theme_data = json.load(f)
                display_name = theme_data.get("name", theme_name)
                description = theme_data.get("description", "")
        except (OSError, json.JSONDecodeError) as e:
            print(f"  Warning: Could not read theme file '{theme_name}.json': {e}")
            display_name = theme_name
            description = "(error reading theme file)"
        print(f"  {theme_name}")
        print(f"    {display_name}")
        if description:
            print(f"    {description}")
        print()
