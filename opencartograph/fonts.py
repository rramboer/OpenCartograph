"""
Font loading and Google Fonts integration.

Handles downloading fonts from Google Fonts API, local font loading,
and caching downloaded font files.
"""

from __future__ import annotations

import os
import re
from typing import Optional

import requests

from . import constants
from .models import FontSet

# Weight names mapped to numeric values
WEIGHT_NAMES = {300: "light", 400: "regular", 700: "bold"}
DEFAULT_WEIGHTS = [300, 400, 700]


def download_google_font(
    font_family: str, weights: list[int] | None = None
) -> Optional[dict[str, str]]:
    """
    Download a font family from Google Fonts and cache it locally.

    Args:
        font_family: Google Fonts family name (e.g., 'Noto Sans JP', 'Open Sans')
        weights: List of font weights to download (300=light, 400=regular, 700=bold)

    Returns:
        Dict with 'light', 'regular', 'bold' keys mapping to font file paths,
        or None if download fails
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    # Create fonts cache directory
    try:
        constants.FONTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"\u26a0 Cannot create font cache directory '{constants.FONTS_CACHE_DIR}': {e}")
        return None

    # Normalize font family name for file paths
    font_name_safe = font_family.replace(" ", "_").lower()

    font_files: dict[str, str] = {}

    # Google Fonts API endpoint - request all weights at once
    weights_str = ";".join(map(str, weights))
    api_url = "https://fonts.googleapis.com/css2"

    params = {"family": f"{font_family}:wght@{weights_str}"}
    headers = {
        "User-Agent": "Mozilla/5.0"  # Browser-like UA so Google Fonts returns woff2
    }

    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"\u26a0 Could not reach Google Fonts API for '{font_family}': {e}")
        return None

    css_content = response.text

    # Parse CSS to extract weight-specific URLs
    weight_url_map: dict[int, str] = {}
    font_face_blocks = re.split(r"@font-face\s*\{", css_content)

    for block in font_face_blocks[1:]:  # Skip first empty split
        weight_match = re.search(r"font-weight:\s*(\d+)", block)
        if not weight_match:
            continue

        weight = int(weight_match.group(1))

        url_match = re.search(r"url\((https://[^)]+\.(woff2|ttf))\)", block)
        if url_match:
            weight_url_map[weight] = url_match.group(1)

    # Download each weight
    for weight in weights:
        weight_key = WEIGHT_NAMES.get(weight, "regular")

        weight_url = weight_url_map.get(weight)

        # If exact weight not found, try closest
        if not weight_url and weight_url_map:
            closest_weight = min(
                weight_url_map.keys(), key=lambda x: abs(x - weight)
            )
            weight_url = weight_url_map[closest_weight]
            print(
                f"  Using weight {closest_weight} for {weight_key} "
                f"(requested {weight} not available)"
            )

        if weight_url:
            file_ext = "woff2" if weight_url.endswith(".woff2") else "ttf"
            font_filename = f"{font_name_safe}_{weight_key}.{file_ext}"
            font_path = constants.FONTS_CACHE_DIR / font_filename

            if not font_path.exists():
                print(f"  Downloading {font_family} {weight_key} ({weight})...")
                try:
                    font_response = requests.get(weight_url, timeout=10)
                    font_response.raise_for_status()
                    font_path.write_bytes(font_response.content)
                except (requests.RequestException, OSError) as e:
                    print(f"  \u26a0 Failed to download/save {weight_key}: {e}")
                    continue
            else:
                print(f"  Using cached {font_family} {weight_key}")

            font_files[weight_key] = str(font_path)

    # Ensure we have at least regular weight
    if "regular" not in font_files and font_files:
        font_files["regular"] = list(font_files.values())[0]
        print(f"  Using {list(font_files.keys())[0]} weight as regular")

    # If we don't have all three weights, duplicate available ones
    if "bold" not in font_files and "regular" in font_files:
        font_files["bold"] = font_files["regular"]
        print("  Using regular weight as bold")
    if "light" not in font_files and "regular" in font_files:
        font_files["light"] = font_files["regular"]
        print("  Using regular weight as light")

    return font_files if font_files else None


FONT_EXTENSIONS = (".ttf", ".otf", ".woff", ".woff2")

# Weight name patterns (case-insensitive substrings that indicate a weight)
WEIGHT_PATTERNS = {
    "bold": ("bold", "heavy", "black"),
    "light": ("light", "thin"),
    "regular": ("regular", "normal", "book", "medium"),
}


def load_local_font(font_path: str) -> Optional[dict[str, str]]:
    """
    Load fonts from a local file or directory.

    If `font_path` is a single font file, uses it for all three weights.
    If `font_path` is a directory, searches for files matching bold/regular/
    light weight patterns in their filenames. Files without a weight marker
    are used as the regular fallback.

    Args:
        font_path: Path to a font file or directory containing fonts

    Returns:
        Dict with 'light', 'regular', 'bold' keys mapping to font file paths,
        or None if loading fails
    """
    from pathlib import Path

    path = Path(font_path).expanduser().resolve()
    if not path.exists():
        print(f"\u26a0 Font path not found: {path}")
        return None

    # Single file: use it for all weights
    if path.is_file():
        if path.suffix.lower() not in FONT_EXTENSIONS:
            print(f"\u26a0 Unsupported font extension: {path.suffix}")
            return None
        p = str(path)
        return {"bold": p, "regular": p, "light": p}

    # Directory: search for weight-specific files
    font_files = [
        f for f in path.iterdir()
        if f.is_file() and f.suffix.lower() in FONT_EXTENSIONS
    ]
    if not font_files:
        print(f"\u26a0 No font files found in directory: {path}")
        return None

    matches: dict[str, str] = {}
    for f in font_files:
        name_lower = f.name.lower()
        for weight, patterns in WEIGHT_PATTERNS.items():
            if any(pat in name_lower for pat in patterns):
                if weight not in matches:
                    matches[weight] = str(f)
                break

    # Fill in missing weights with any available font
    fallback = next(iter(matches.values()), str(font_files[0]))
    for weight in ("bold", "regular", "light"):
        if weight not in matches:
            matches[weight] = fallback
            print(f"  Using fallback for {weight} weight")

    return matches


def load_fonts(
    font_family: str | None = None,
    font_path: str | None = None,
) -> FontSet | None:
    """
    Load fonts in priority order: font_family > font_path > bundled Roboto.

    Args:
        font_family: Google Fonts family name (e.g., 'Noto Sans JP'). Takes
                     precedence over `font_path` if both are provided.
        font_path: Path to a local font file or directory.

    Returns:
        FontSet with paths to font files, or None if all loading methods fail
    """
    # Priority 1: Google Fonts
    if font_family and font_family.lower() != "roboto":
        print(f"Loading Google Font: {font_family}")
        fonts = download_google_font(font_family)
        if fonts:
            print(f"\u2713 Font '{font_family}' loaded successfully")
            return FontSet.from_dict(fonts)
        print(f"\u26a0 Failed to load '{font_family}', trying next font option")

    # Priority 2: Local font path
    if font_path:
        print(f"Loading local font from: {font_path}")
        fonts = load_local_font(font_path)
        if fonts:
            print("\u2713 Local font loaded successfully")
            return FontSet.from_dict(fonts)
        print("\u26a0 Failed to load local font, falling back to Roboto")

    # Priority 3: Bundled Roboto
    fonts_dir = constants.FONTS_DIR
    font_paths = {
        "bold": os.path.join(fonts_dir, "Roboto-Bold.ttf"),
        "regular": os.path.join(fonts_dir, "Roboto-Regular.ttf"),
        "light": os.path.join(fonts_dir, "Roboto-Light.ttf"),
    }

    for _weight, path in font_paths.items():
        if not os.path.exists(path):
            print(f"\u26a0 Font not found: {path}")
            return None

    return FontSet.from_dict(font_paths)
