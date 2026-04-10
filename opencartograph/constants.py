"""
Constants and default values used throughout the opencartograph package.
"""

from __future__ import annotations

import os
from pathlib import Path

# Project root is the parent of the opencartograph package directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory paths (with env-var override for cache)
CACHE_DIR = Path(os.environ.get("CACHE_DIR", str(PROJECT_ROOT / "cache")))
THEMES_DIR = PROJECT_ROOT / "themes"
FONTS_DIR = PROJECT_ROOT / "fonts"
FONTS_CACHE_DIR = FONTS_DIR / "cache"
OUTPUT_DIR = PROJECT_ROOT / "output"

FILE_ENCODING = "utf-8"

# Typography base sizes (reference dimension: 12 inches)
BASE_FONT_MAIN = 60
BASE_FONT_SUB = 22
BASE_FONT_COORDS = 14
BASE_FONT_ATTR = 8
FONT_REFERENCE_DIMENSION = 12.0

# City name length threshold for font size reduction
CITY_NAME_LENGTH_THRESHOLD = 10
CITY_NAME_MIN_SCALE_FACTOR = 10

# Road widths by tier
ROAD_WIDTH_MOTORWAY = 1.2
ROAD_WIDTH_PRIMARY = 1.0
ROAD_WIDTH_SECONDARY = 0.8
ROAD_WIDTH_TERTIARY = 0.6
ROAD_WIDTH_DEFAULT = 0.4

# Gradient fade extent fractions (of axes height)
GRADIENT_BOTTOM_END = 0.25
GRADIENT_TOP_START = 0.75

# Latin script detection
LATIN_SCRIPT_THRESHOLD = 0.8
LATIN_UPPER_CODEPOINT = 0x250

# Maximum poster dimension (inches)
MAX_DIMENSION_INCHES = 20.0

# Poster DPI for raster formats
RASTER_DPI = 300

# Quality presets: (width_inches, height_inches, dpi)
QUALITY_PRESETS: dict[str, tuple[float, float, int]] = {
    "low": (6.0, 8.0, 150),
    "standard": (12.0, 16.0, 300),
    "high": (16.0, 20.0, 400),
    "ultra": (18.0, 20.0, 600),
}

# Text vertical positions (fraction of axes height)
TEXT_Y_CITY = 0.14
TEXT_Y_DIVIDER = 0.125
TEXT_Y_COUNTRY = 0.10
TEXT_Y_COORDS = 0.07
TEXT_Y_DATE = 0.045
TEXT_Y_ATTR = 0.02
TEXT_X_ATTR = 0.98

# Divider line x-range
DIVIDER_X_START = 0.4
DIVIDER_X_END = 0.6

# Rate limiting delays (seconds)
GEOCODING_DELAY = 1
GRAPH_FETCH_DELAY = 0.5
FEATURE_FETCH_DELAY = 0.3

# Default theme name
DEFAULT_THEME = "terracotta"

# Default poster dimensions (inches)
DEFAULT_WIDTH = 12.0
DEFAULT_HEIGHT = 16.0

# Default map distance (meters)
DEFAULT_DISTANCE = 18000

# City name letter spacing for Latin scripts
LATIN_LETTER_SPACING = "  "

# Coordinates display precision
COORD_DECIMAL_PLACES = 4

# Attribution text
ATTRIBUTION_TEXT = "\u00a9 OpenStreetMap contributors"
ATTRIBUTION_ALPHA = 0.5
COORDS_ALPHA = 0.7

# Minimum area (in projected m²) for polygon features to be rendered.
# Filters out tiny water bodies (fountains, pools) that appear as dots.
MIN_POLYGON_AREA_M2 = 5000

# Z-order values for rendering layers
ZORDER_OCEAN = 0.3
ZORDER_PARKS = 0.5
ZORDER_AIRPORTS = 0.6
ZORDER_STADIUMS = 0.7
ZORDER_NATIONAL_PARKS = 0.8
ZORDER_WATER = 0.9
ZORDER_BUILDINGS = 0.95
ZORDER_RUNWAYS = 0.97
ZORDER_GRADIENT = 10
ZORDER_TEXT = 11
ZORDER_COMPASS = 13

# Compass badge positioning (fraction of map extent)
COMPASS_X_FRAC = 0.06
COMPASS_Y_FRAC = 0.06
COMPASS_SIZE_FRAC = 0.05
