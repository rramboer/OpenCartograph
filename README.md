# OpenCartograph

An open-source cartographic rendering tool. Generate high-quality map visualizations for any location worldwide using OpenStreetMap data. Supports multiple visual themes, export formats, and fully customizable output.

<img src="posters/singapore_neon_cyberpunk_20260118_153328.png" width="250">
<img src="posters/dubai_midnight_blue_20260118_140807.png" width="250">

## Examples

| Country      | City           | Theme           | Poster |
|:------------:|:--------------:|:---------------:|:------:|
| USA          | San Francisco  | sunset          | <img src="posters/san_francisco_sunset_20260118_144726.png" width="250"> |
| Spain        | Barcelona      | warm_beige      | <img src="posters/barcelona_warm_beige_20260118_140048.png" width="250"> |
| Italy        | Venice         | blueprint       | <img src="posters/venice_blueprint_20260118_140505.png" width="250"> |
| Japan        | Tokyo          | japanese_ink    | <img src="posters/tokyo_japanese_ink_20260118_142446.png" width="250"> |
| India        | Mumbai         | contrast_zones  | <img src="posters/mumbai_contrast_zones_20260118_145843.png" width="250"> |
| Morocco      | Marrakech      | terracotta      | <img src="posters/marrakech_terracotta_20260118_143253.png" width="250"> |
| Singapore    | Singapore      | neon_cyberpunk  | <img src="posters/singapore_neon_cyberpunk_20260118_153328.png" width="250"> |
| Australia    | Melbourne      | forest          | <img src="posters/melbourne_forest_20260118_153446.png" width="250"> |
| UAE          | Dubai          | midnight_blue   | <img src="posters/dubai_midnight_blue_20260118_140807.png" width="250"> |
| USA          | Seattle        | emerald         | <img src="posters/seattle_emerald_20260124_162244.png" width="250"> |

## Installation

### With uv (Recommended)

Make sure [uv](https://docs.astral.sh/uv/) is installed.

```bash
git clone https://github.com/rramboer/OpenCartograph.git
cd OpenCartograph
uv sync
```

### With pip + venv

```bash
git clone https://github.com/rramboer/OpenCartograph.git
cd OpenCartograph
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Quick Start

```bash
# Generate a poster
opencartograph --city "Paris" --country "France"

# Or run as a module
python -m opencartograph --city "Paris" --country "France"

# With uv (if not installed as a CLI)
uv run python -m opencartograph --city "Paris" --country "France"
```

## Usage

### Required Options

| Option | Short | Description |
|--------|-------|-------------|
| `--city` | `-c` | City name |
| `--country` | `-C` | Country name |

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--theme` | `-t` | Visual theme | `terracotta` |
| `--distance` | `-d` | Map radius in meters | `18000` |
| `--width` | `-W` | Poster width in inches | `12` |
| `--height` | `-H` | Poster height in inches | `16` |
| `--format` | `-f` | Output format (`png`, `svg`, `pdf`) | `png` |
| `--no-text` | | Generate poster without any text overlay | |
| `--latitude` | `-lat` | Override center latitude | |
| `--longitude` | `-long` | Override center longitude | |
| `--country-label` | | Override country text on poster | |
| `--all-themes` | | Generate posters for all themes | |
| `--list-themes` | | List available themes | |

### Multilingual Support

Display city and country names in any language with Google Fonts:

| Option | Short | Description |
|--------|-------|-------------|
| `--display-city` | `-dc` | Custom display name for city |
| `--display-country` | `-dC` | Custom display name for country |
| `--font-family` | | Google Fonts family name |

```bash
# Japanese
opencartograph -c "Tokyo" -C "Japan" -dc "東京" -dC "日本" --font-family "Noto Sans JP" -t japanese_ink

# Korean
opencartograph -c "Seoul" -C "South Korea" -dc "서울" -dC "대한민국" --font-family "Noto Sans KR" -t midnight_blue

# Arabic
opencartograph -c "Dubai" -C "UAE" -dc "دبي" -dC "الإمارات" --font-family "Cairo" -t terracotta
```

Fonts are automatically downloaded from Google Fonts and cached locally in `fonts/cache/`.

### Examples

```bash
# Map only, no text
opencartograph -c "Frisco" -C "USA" -t noir -d 6000 --no-text

# Iconic grid patterns
opencartograph -c "New York" -C "USA" -t noir -d 12000
opencartograph -c "Barcelona" -C "Spain" -t warm_beige -d 8000

# Waterfront cities
opencartograph -c "Venice" -C "Italy" -t blueprint -d 4000
opencartograph -c "Amsterdam" -C "Netherlands" -t ocean -d 6000

# Custom coordinates
opencartograph -c "Davisburg" -C "USA" -lat 42.755243 -long -83.556055 -t noir -d 3000 --no-text

# SVG output for editing
opencartograph -c "London" -C "UK" -t noir -d 15000 -f svg

# Generate all themes at once
opencartograph -c "Tokyo" -C "Japan" --all-themes
```

### Distance Guide

| Distance | Best for |
|----------|----------|
| 4000-6000m | Small/dense cities (Venice, Amsterdam center) |
| 8000-12000m | Medium cities, downtown focus (Paris, Barcelona) |
| 15000-20000m | Large metros, full city view (Tokyo, Mumbai) |

### Resolution Guide (300 DPI)

| Target | Resolution | Inches (`-W` / `-H`) |
|--------|-----------|----------------------|
| Instagram Post | 1080 x 1080 | 3.6 x 3.6 |
| Mobile Wallpaper | 1080 x 1920 | 3.6 x 6.4 |
| HD Wallpaper | 1920 x 1080 | 6.4 x 3.6 |
| 4K Wallpaper | 3840 x 2160 | 12.8 x 7.2 |
| A4 Print | 2480 x 3508 | 8.3 x 11.7 |

## Themes

17 built-in themes in the `themes/` directory:

| Theme | Style |
|-------|-------|
| `terracotta` | Mediterranean warmth (default) |
| `noir` | Pure black background, white roads |
| `midnight_blue` | Navy background with gold roads |
| `blueprint` | Architectural blueprint aesthetic |
| `neon_cyberpunk` | Dark with electric pink/cyan |
| `warm_beige` | Vintage sepia tones |
| `pastel_dream` | Soft muted pastels |
| `japanese_ink` | Minimalist ink wash style |
| `emerald` | Lush dark green aesthetic |
| `forest` | Deep greens and sage |
| `ocean` | Blues and teals for coastal cities |
| `sunset` | Warm oranges and pinks |
| `autumn` | Seasonal burnt oranges and reds |
| `copper_patina` | Oxidized copper aesthetic |
| `monochrome_blue` | Single blue color family |
| `gradient_roads` | Smooth gradient shading |
| `contrast_zones` | High contrast urban density |

### Custom Themes

Create a JSON file in `themes/`:

```json
{
  "name": "My Theme",
  "description": "Description of the theme",
  "bg": "#FFFFFF",
  "text": "#000000",
  "gradient_color": "#FFFFFF",
  "water": "#C0C0C0",
  "parks": "#F0F0F0",
  "road_motorway": "#0A0A0A",
  "road_primary": "#1A1A1A",
  "road_secondary": "#2A2A2A",
  "road_tertiary": "#3A3A3A",
  "road_residential": "#4A4A4A",
  "road_default": "#3A3A3A"
}
```

## Output

Posters are saved to `posters/` with the filename format:

```
{city}_{theme}_{YYYYMMDD_HHMMSS}.{format}
```

## Project Structure

```
OpenCartograph/
├── opencartograph/
│   ├── __init__.py
│   ├── __main__.py          # python -m opencartograph
│   ├── cli.py               # Argument parsing and entry point
│   ├── constants.py          # All configurable constants
│   ├── models.py             # Frozen dataclasses (Theme, PosterConfig, etc.)
│   ├── fonts.py              # Font loading and Google Fonts integration
│   ├── geocoding.py          # City name to coordinates via Nominatim
│   ├── osm.py                # OpenStreetMap data fetching via OSMnx
│   ├── output.py             # File saving and filename generation
│   ├── road_styles.py        # Highway classification and styling
│   ├── text.py               # Script detection and typography
│   ├── theme.py              # Theme loading and management
│   └── rendering/
│       ├── __init__.py
│       ├── pipeline.py       # Rendering orchestrator
│       ├── layers.py         # Individual render layers (water, parks, roads, etc.)
│       └── viewport.py       # Figure setup and crop calculations
├── tests/                    # 85 unit tests
├── themes/                   # Theme JSON files
├── fonts/                    # Bundled Roboto fonts + Google Fonts cache
└── posters/                  # Generated output
```

## Contributing

See [the roadmap](https://github.com/rramboer/OpenCartograph/issues/1) for planned features.

Fork of [originalankur/maptoposter](https://github.com/originalankur/maptoposter). Licensed under MIT.
