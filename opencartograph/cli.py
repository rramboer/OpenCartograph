"""
Command-line interface for OpenCartograph.
"""

from __future__ import annotations

import argparse
import sys
import traceback
from datetime import date

from lat_lon_parser import parse

from . import constants
from .fonts import load_fonts
from .geocoding import get_coordinates
from .models import Coordinates, PosterConfig
from .output import generate_output_filename
from .rendering import compose_poster
from .theme import get_available_themes, list_themes, load_theme


def print_examples() -> None:
    """Print usage examples."""
    print("""
OpenCartograph
==============

Usage:
  opencartograph --city <city> --country <country> [options]

Examples:
  opencartograph -c "New York" -C "USA" -t noir -d 12000           # Manhattan grid
  opencartograph -c "Barcelona" -C "Spain" -t warm_beige -d 8000   # Eixample district grid
  opencartograph -c "Venice" -C "Italy" -t blueprint -d 4000       # Canal network
  opencartograph -c "Paris" -C "France" -t pastel_dream -d 10000   # Haussmann boulevards
  opencartograph -c "Tokyo" -C "Japan" -t japanese_ink -d 15000    # Dense organic streets
  opencartograph -c "London" -C "UK" -t noir -d 15000              # Thames curves
  opencartograph -c "Frisco" -C "USA" -t noir -d 6000 --no-text   # Map only, no text

Options:
  --city, -c        City name (required)
  --country, -C     Country name (required)
  --country-label   Override country text displayed on poster
  --theme, -t       Theme name (default: terracotta)
  --all-themes      Generate posters for all themes
  --distance, -d    Map radius in meters (default: 18000)
  --no-text         Generate poster without any text overlay
  --list-themes     List all available themes

Distance guide:
  4000-6000m   Small/dense cities (Venice, Amsterdam old center)
  8000-12000m  Medium cities, focused downtown (Paris, Barcelona)
  15000-20000m Large metros, full city view (Tokyo, Mumbai)

Available themes can be found in the 'themes/' directory.
Generated posters are saved to 'posters/' directory.
""")


def build_parser() -> argparse.ArgumentParser:
    """
    Build the argument parser with all CLI options.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="OpenCartograph - Generate high-quality map visualizations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  opencartograph --city "New York" --country "USA"
  opencartograph --city Tokyo --country Japan --theme midnight_blue
  opencartograph --city Paris --country France --theme noir --distance 15000
  opencartograph --city Frisco --country USA --theme noir --no-text -d 6000
  opencartograph --list-themes
        """,
    )

    parser.add_argument("--city", "-c", type=str, help="City name")
    parser.add_argument("--country", "-C", type=str, help="Country name")
    parser.add_argument(
        "--latitude", "-lat", dest="latitude", type=str,
        help="Override latitude center point",
    )
    parser.add_argument(
        "--longitude", "-long", dest="longitude", type=str,
        help="Override longitude center point",
    )
    parser.add_argument(
        "--country-label", dest="country_label", type=str,
        help="Override country text displayed on poster",
    )
    parser.add_argument(
        "--theme", "-t", type=str, default=constants.DEFAULT_THEME,
        help=f"Theme name (default: {constants.DEFAULT_THEME})",
    )
    parser.add_argument(
        "--all-themes", "--All-themes", dest="all_themes", action="store_true",
        help="Generate posters for all themes",
    )
    parser.add_argument(
        "--distance", "-d", type=int, default=constants.DEFAULT_DISTANCE,
        help=f"Map radius in meters (default: {constants.DEFAULT_DISTANCE})",
    )
    parser.add_argument(
        "--width", "-W", type=float, default=None,
        help=f"Image width in inches (default: {constants.DEFAULT_WIDTH}, max: {constants.MAX_DIMENSION_INCHES})",
    )
    parser.add_argument(
        "--height", "-H", type=float, default=None,
        help=f"Image height in inches (default: {constants.DEFAULT_HEIGHT}, max: {constants.MAX_DIMENSION_INCHES})",
    )
    parser.add_argument(
        "--list-themes", action="store_true",
        help="List all available themes",
    )
    parser.add_argument(
        "--display-city", "-dc", type=str,
        help="Custom display name for city (for i18n support)",
    )
    parser.add_argument(
        "--display-country", "-dC", type=str,
        help="Custom display name for country (for i18n support)",
    )
    parser.add_argument(
        "--font-family", type=str,
        help='Google Fonts family name (e.g., "Noto Sans JP", "Open Sans"). '
             "If not specified, uses local Roboto fonts.",
    )
    parser.add_argument(
        "--format", "-f", default="png", choices=["png", "svg", "pdf"],
        help="Output format for the poster (default: png)",
    )
    parser.add_argument(
        "--no-text", dest="no_text", action="store_true",
        help="Generate poster without any text (city name, country, coordinates, attribution)",
    )
    parser.add_argument(
        "--show-date", dest="show_date", action="store_true",
        help="Display the current date on the poster (below coordinates)",
    )
    parser.add_argument(
        "--line-scale", type=float, default=1.0,
        help="Scale factor for road line widths (default: 1.0). "
             "Use values >1 for thicker roads, <1 for thinner. Must be positive.",
    )
    parser.add_argument(
        "--output-dir", "-o", type=str, default=None,
        help="Output directory for generated posters (default: output/)",
    )
    parser.add_argument(
        "--quality", "-q",
        choices=list(constants.QUALITY_PRESETS.keys()),
        default=None,
        help="Quality preset: low (150 DPI), standard (300 DPI), "
             "high (400 DPI), ultra (600 DPI). "
             "Sets width, height, and DPI. Explicit --width/--height override.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    CLI entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # If no arguments provided, show examples
    if len(sys.argv) == 1 and argv is None:
        print_examples()
        return 0

    # List themes if requested
    if args.list_themes:
        list_themes()
        return 0

    # Validate required arguments
    if not args.city or not args.country:
        print("Error: --city and --country are required.\n")
        print_examples()
        return 1

    # Apply quality preset (explicit --width/--height override preset values)
    dpi = constants.RASTER_DPI
    if args.quality:
        preset_w, preset_h, preset_dpi = constants.QUALITY_PRESETS[args.quality]
        dpi = preset_dpi
        if args.width is None:
            args.width = preset_w
        if args.height is None:
            args.height = preset_h

    # Apply defaults for anything still unset
    if args.width is None:
        args.width = constants.DEFAULT_WIDTH
    if args.height is None:
        args.height = constants.DEFAULT_HEIGHT

    # Enforce maximum dimensions
    max_dim = constants.MAX_DIMENSION_INCHES
    if args.width > max_dim:
        print(
            f"\u26a0 Width {args.width} exceeds the maximum allowed limit of "
            f"{max_dim}. It's enforced as max limit {max_dim}."
        )
        args.width = max_dim
    if args.height > max_dim:
        print(
            f"\u26a0 Height {args.height} exceeds the maximum allowed limit of "
            f"{max_dim}. It's enforced as max limit {max_dim}."
        )
        args.height = max_dim

    if args.quality:
        print(f"\u2713 Quality preset: {args.quality} "
              f"({args.width}x{args.height} inches, {dpi} DPI)")
        if args.format == "svg":
            print("  Note: DPI setting has no effect on SVG output (vector format).")

    if args.line_scale <= 0:
        print("Error: --line-scale must be a positive number.")
        return 1

    available_themes = get_available_themes()
    if not available_themes:
        print("No themes found in 'themes/' directory.")
        return 1

    if args.all_themes:
        themes_to_generate = available_themes
    else:
        if args.theme not in available_themes:
            print(f"Error: Theme '{args.theme}' not found.")
            print(f"Available themes: {', '.join(available_themes)}")
            return 1
        themes_to_generate = [args.theme]

    print("=" * 50)
    print("OpenCartograph")
    print("=" * 50)

    # Load default fonts (Roboto)
    default_fonts = load_fonts()

    # Load custom fonts if specified
    custom_fonts = None
    if args.font_family:
        custom_fonts = load_fonts(args.font_family)
        if not custom_fonts:
            print(f"\u26a0 Failed to load '{args.font_family}', falling back to Roboto")

    final_fonts = custom_fonts or default_fonts
    if final_fonts is None and not args.no_text:
        print("\u2717 Error: No fonts available for text rendering. "
              "Ensure Roboto fonts exist in the fonts/ directory, "
              "or use --no-text to generate without text.")
        return 1

    # Get coordinates and generate poster
    try:
        if args.latitude and args.longitude:
            lat = parse(args.latitude)
            lon = parse(args.longitude)
            coords = Coordinates(latitude=lat, longitude=lon)
            print(f"\u2713 Coordinates: {lat}, {lon}")
        else:
            coords = get_coordinates(args.city, args.country)

        for theme_name in themes_to_generate:
            theme = load_theme(theme_name)
            output_file = generate_output_filename(
                args.city, theme_name, args.format,
                output_dir=args.output_dir,
            )

            # Resolve display names
            display_city = args.display_city or args.city
            display_country = args.display_country or args.country_label or args.country

            config = PosterConfig(
                city=args.city,
                country=args.country,
                center=coords,
                dist=args.distance,
                width=args.width,
                height=args.height,
                theme=theme,
                fonts=final_fonts,
                output_file=output_file,
                output_format=args.format,
                display_city=display_city,
                display_country=display_country,
                no_text=args.no_text,
                line_scale=args.line_scale,
                date_text=date.today().strftime("%B %d, %Y") if args.show_date else None,
                dpi=dpi,
            )

            compose_poster(config, default_fonts=default_fonts)

        print("\n" + "=" * 50)
        print("\u2713 Poster generation complete!")
        print("=" * 50)
        return 0

    except MemoryError:
        print("\nError: Not enough memory to render at the requested quality.")
        print("Try a lower quality preset (e.g., --quality high) or reduce dimensions.")
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n\u2717 Error: {e}")
        traceback.print_exc()
        return 1
