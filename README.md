# OpenCartograph

An open-source cartographic rendering tool. Generate high-quality map posters for any location worldwide using OpenStreetMap data. 27 themes, multiple layer types, rotation, custom fonts, and resolutions up to 18×20" at 600 DPI.

## Examples

|                                      City                                       |      Theme      |                Notes                |
| :-----------------------------------------------------------------------------: | :-------------: | :---------------------------------: |
|    <img src="examples/dubai_midnight_blue_20260118_140807.png" width="220">     |  Midnight Blue  |        Dubai — Palm Jumeirah        |
|  <img src="examples/hong_kong_neon_cyberpunk_20260409_195640.png" width="220">  | Neon Cyberpunk  |              Hong Kong              |
|      <img src="examples/reykjavik_arctic_20260413_133857.png" width="220">      |     Arctic      |              Reykjavík              |
|      <img src="examples/miami_vaporwave_20260413_134319.png" width="220">       |    Vaporwave    |         Miami (rotated 20°)         |
|       <img src="examples/vienna_crimson_20260413_135313.png" width="220">       |     Crimson     |               Vienna                |
|      <img src="examples/seattle_espresso_20260413_135732.png" width="220">      |    Espresso     |               Seattle               |
|        <img src="examples/delhi_butter_20260414_004320.png" width="220">        |     Butter      |       Delhi — Lutyens layout        |
|     <img src="examples/singapore_oxblood_20260414_003835.png" width="220">      |     Oxblood     |              Singapore              |
|        <img src="examples/london_noir_20260409_200022.png" width="220">         |      Noir       |               London                |
|    <img src="examples/marrakech_terracotta_20260409_200730.png" width="220">    |   Terracotta    |              Marrakech              |
|    <img src="examples/tokyo_contrast_zones_20260409_194415.png" width="220">    | Contrast Zones  |                Tokyo                |
|     <img src="examples/kyoto_japanese_ink_20260409_195134.png" width="220">     |  Japanese Ink   |                Kyoto                |
|       <img src="examples/seattle_forest_20260409_194918.png" width="220">       |     Forest      |               Seattle               |
|      <img src="examples/portland_emerald_20260409_194846.png" width="220">      |     Emerald     |              Portland               |
|      <img src="examples/barcelona_ocean_20260409_200256.png" width="220">       |      Ocean      |              Barcelona              |
|     <img src="examples/los_angeles_sunset_20260409_200558.png" width="220">     |     Sunset      |     Los Angeles (with airports)     |
|       <img src="examples/boston_autumn_20260409_193834.png" width="220">        |     Autumn      |               Boston                |
|     <img src="examples/new_york_blueprint_20260409_193935.png" width="220">     |    Blueprint    |              New York               |
|  <img src="examples/washington_copper_patina_20260409_194634.png" width="220">  |  Copper Patina  | Washington DC (with national parks) |
| <img src="examples/copenhagen_monochrome_blue_20260409_195451.png" width="220"> | Monochrome Blue |             Copenhagen              |
|   <img src="examples/chicago_gradient_roads_20260409_195041.png" width="220">   | Gradient Roads  |               Chicago               |
|   <img src="examples/amsterdam_pastel_dream_20260409_200443.png" width="220">   |  Pastel Dream   |              Amsterdam              |
|      <img src="examples/rome_warm_beige_20260409_200810.png" width="220">       |   Warm Beige    |                Rome                 |
|  <img src="examples/ann_arbor_midnight_blue_20260410_011524.png" width="220">   |  Midnight Blue  |     Ann Arbor (with buildings)      |
|   <img src="examples/detroit_midnight_blue_20260414_011335.png" width="220">    |  Midnight Blue  |   Detroit (with buildings, 30km)    |

## Installation

### With uv (recommended)

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
pip install .
```

## Quick Start

```bash
# Activate the venv first
source .venv/bin/activate

# Generate a poster
python -m opencartograph --city "Paris" --country "France"

# Or with uv
uv run python -m opencartograph --city "Paris" --country "France"
```

## Usage

### Required

| Option      | Short | Description  |
| ----------- | ----- | ------------ |
| `--city`    | `-c`  | City name    |
| `--country` | `-C`  | Country name |

You can substitute `--latitude` / `--longitude` for the city/country if you want to center the map on exact coordinates.

### Core options

| Option         | Short | Description                                         | Default      |
| -------------- | ----- | --------------------------------------------------- | ------------ |
| `--theme`      | `-t`  | Visual theme name                                   | `terracotta` |
| `--distance`   | `-d`  | Map radius in meters                                | `18000`      |
| `--quality`    | `-q`  | Quality preset (`low`, `standard`, `high`, `ultra`) | `standard`   |
| `--width`      | `-W`  | Image width in inches (overrides quality preset)    | `12`         |
| `--height`     | `-H`  | Image height in inches (overrides quality preset)   | `16`         |
| `--format`     | `-f`  | Output format (`png`, `svg`, `pdf`)                 | `png`        |
| `--output-dir` | `-o`  | Output directory                                    | `output/`    |

### Quality presets

| Preset     | Dimensions | DPI | Use case                            |
| ---------- | ---------- | --- | ----------------------------------- |
| `low`      | 6 × 8"     | 150 | Quick previews and iteration        |
| `standard` | 12 × 16"   | 300 | Default — high-quality print        |
| `high`     | 16 × 20"   | 400 | Large prints                        |
| `ultra`    | 18 × 20"   | 600 | Wall-sized prints, very large files |

### Optional layers

These extra layers are off by default. Each adds an extra OpenStreetMap fetch.

| Option         | Description                                  |
| -------------- | -------------------------------------------- |
| `--airports`   | Airport grounds, runways, and taxiways       |
| `--natl-parks` | National parks and protected areas           |
| `--stadiums`   | Stadiums                                     |
| `--buildings`  | Building footprints (heavy for dense cities) |

### Map controls

| Option                          | Short   | Description                                         |
| ------------------------------- | ------- | --------------------------------------------------- |
| `--latitude`                    | `-lat`  | Override center latitude                            |
| `--longitude`                   | `-long` | Override center longitude                           |
| `--orientation-offset`          | `-O`    | Rotate the map clockwise by N degrees (-180 to 180) |
| `--show-north` / `--hide-north` |         | Compass badge (auto-enabled when rotated)           |
| `--line-scale`                  |         | Scale road line widths (default `1.0`)              |

### Text and typography

| Option               | Short | Description                                       |
| -------------------- | ----- | ------------------------------------------------- |
| `--no-text`          |       | Map only, no text overlay                         |
| `--show-date`        |       | Display the current date below coordinates        |
| `--show-attribution` |       | Show "© OpenStreetMap contributors" in the corner |
| `--display-city`     | `-dc` | Override the displayed city name                  |
| `--display-country`  | `-dC` | Override the displayed country name               |
| `--country-label`    |       | Override the country line on the poster           |
| `--font-family`      |       | Google Fonts family name                          |
| `--font-path`        |       | Path to a local font file or directory            |

Font priority: `--font-family` (Google Fonts) > `--font-path` (local) > bundled Roboto. Google Fonts are downloaded on first use and cached in `fonts/cache/`.

### Theme management

| Option             | Description                                             |
| ------------------ | ------------------------------------------------------- |
| `--list-themes`    | Print all available themes                              |
| `--theme-swatches` | Generate a side-by-side color swatch PNG of every theme |
| `--all-themes`     | Generate a poster for every theme at once               |

## Examples

```bash
# Map only, no text
python -m opencartograph -c "Frisco" -C "USA" -t noir -d 6000 --no-text

# Iconic grid patterns
python -m opencartograph -c "New York" -C "USA" -t blueprint -d 12000
python -m opencartograph -c "Barcelona" -C "Spain" -t warm_beige -d 8000

# Waterfront cities
python -m opencartograph -c "Venice" -C "Italy" -t blueprint -d 4000
python -m opencartograph -c "Amsterdam" -C "Netherlands" -t ocean -d 6000

# Large wall print, all extra layers, custom title
python -m opencartograph -c "Detroit" -C "USA" -t midnight_blue -d 30000 \
    -q ultra --buildings --airports --natl-parks --stadiums

# Rotated 45° with the compass badge
python -m opencartograph -c "Granada" -C "Spain" -t copper_patina -O 45

# Override coordinates and label
python -m opencartograph -c "Huntsville" -C "United States" \
    --display-city "UAH" --country-label "Huntsville" \
    -lat 34.7245 -long -86.6398 -d 5000 -t blueprint --buildings

# Local font for non-Latin scripts
python -m opencartograph -c "Tokyo" -C "Japan" \
    -dc "東京" -dC "日本" \
    --font-path /usr/share/fonts/noto-cjk/

# Google Fonts (auto-downloaded)
python -m opencartograph -c "Seoul" -C "South Korea" \
    -dc "서울" -dC "대한민국" \
    --font-family "Noto Sans KR" -t midnight_blue

# SVG output for editing
python -m opencartograph -c "London" -C "UK" -t noir -d 15000 -f svg

# Generate every theme at once
python -m opencartograph -c "Tokyo" -C "Japan" --all-themes
```

## Distance guide

| Distance     | Best for                                                          |
| ------------ | ----------------------------------------------------------------- |
| 4000-6000m   | Small/dense areas (Venice, Amsterdam center, single neighborhood) |
| 8000-12000m  | Medium cities, downtown focus (Paris, Barcelona)                  |
| 15000-20000m | Large metros, full city view (Tokyo, Mumbai)                      |
| 25000-40000m | Entire metro areas with suburbs                                   |

## Themes (27 total)

Run `python -m opencartograph --list-themes` to see all themes, or `python -m opencartograph --theme-swatches` to generate a visual swatch.

| Theme             | Style                                                                         |
| ----------------- | ----------------------------------------------------------------------------- |
| `amethyst`        | Deep aubergine purple with lavender and rose-gold accents                     |
| `arctic`          | Icy whites and pale blues — winter aesthetic                                  |
| `autumn`          | Burnt oranges, deep reds, golden yellows                                      |
| `blueprint`       | Architectural blueprint aesthetic                                             |
| `butter`          | Saturated butter yellow with caramel roads                                    |
| `contrast_zones`  | High contrast, urban density gradient                                         |
| `copper_patina`   | Oxidized copper teal-green with copper accents                                |
| `crimson`         | Deep wine and burgundy with rose-gold accents                                 |
| `emerald`         | Lush dark green with mint accents                                             |
| `espresso`        | Rich dark chocolate browns with cream and caramel                             |
| `forest`          | Deep greens and sage tones                                                    |
| `gradient_roads`  | Smooth gradient from dark center to light edges                               |
| `japanese_ink`    | Minimalist ink wash with subtle red accent                                    |
| `midnight_blue`   | Navy background with gold/copper roads                                        |
| `monochrome_blue` | Single blue color family                                                      |
| `neon_cyberpunk`  | Dark with electric pink/cyan                                                  |
| `night_drive`     | Black background with white "headlight" roads and red "brake light" motorways |
| `noir`            | Pure black background, white roads — modern gallery aesthetic                 |
| `ocean`           | Various blues and teals — coastal cities                                      |
| `oxblood`         | Deep blood red with cream accents                                             |
| `pastel_dream`    | Soft muted pastels                                                            |
| `prussian`        | Old-world naval atlas — Prussian blue with cream parchment and gold           |
| `sakura`          | Soft pink cherry blossom tones                                                |
| `sunset`          | Warm oranges and pinks — golden hour aesthetic                                |
| `terracotta`      | Mediterranean warmth (default)                                                |
| `vaporwave`       | Retro synthwave — purple with hot pink and cyan neon                          |
| `warm_beige`      | Earthy warm neutrals with sepia tones                                         |

### Custom themes

Drop a JSON file in `themes/`. All keys are required:

```json
{
  "name": "My Theme",
  "description": "Description of the theme",
  "bg": "#FFFFFF",
  "text": "#000000",
  "gradient_color": "#FFFFFF",
  "water": "#C0D8E0",
  "parks": "#E8F0E8",
  "national_parks": "#D8E0D0",
  "airports": "#F0F0F0",
  "runways": "#888888",
  "buildings": "#CCCCCC",
  "stadiums": "#E0E8E0",
  "road_motorway": "#0A0A0A",
  "road_primary": "#1A1A1A",
  "road_secondary": "#2A2A2A",
  "road_tertiary": "#3A3A3A",
  "road_residential": "#4A4A4A",
  "road_default": "#3A3A3A"
}
```

## Output

Posters are saved to `output/` by default. Filename format:

```
{city}_{theme}_{YYYYMMDD_HHMMSS}.{format}
```

## Project structure

```
OpenCartograph/
├── opencartograph/
│   ├── cli.py                  # Argument parsing and entry point
│   ├── constants.py            # Constants and z-orders
│   ├── models.py               # Frozen dataclasses
│   ├── fonts.py                # Font loading (Roboto, Google Fonts, local)
│   ├── geocoding.py            # City → coordinates via Nominatim
│   ├── osm.py                  # OpenStreetMap data fetching via OSMnx
│   ├── output.py               # File saving and filename generation
│   ├── road_styles.py          # Highway classification and styling
│   ├── text.py                 # Script detection and typography
│   ├── theme.py                # Theme loading and management
│   ├── swatches.py             # Theme swatch generator
│   └── rendering/
│       ├── pipeline.py         # Rendering orchestrator
│       ├── layers.py           # Individual render layers
│       ├── viewport.py         # Figure setup and crop calculations
│       ├── ocean.py            # Coastline → ocean polygons
│       ├── rotation.py         # Map rotation
│       └── compass.py          # North compass badge
├── tests/                      # Unit tests
├── themes/                     # Theme JSON files
├── fonts/                      # Bundled Roboto + Google Fonts cache
├── examples/                   # Example poster images
└── output/                     # Generated output (gitignored)
```
