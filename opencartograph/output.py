"""
Output file handling for generated posters.

Handles filename generation and saving matplotlib figures to disk.
"""

from __future__ import annotations

import os
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from . import constants
from .models import PosterConfig


def generate_output_filename(
    city: str, theme_name: str, output_format: str,
    output_dir: str | None = None,
) -> str:
    """
    Generate unique output filename with city, theme, and datetime.

    Args:
        city: City name
        theme_name: Theme name
        output_format: File format extension (png, svg, pdf)
        output_dir: Override output directory (defaults to constants.OUTPUT_DIR)

    Returns:
        Full path to output file
    """
    out_dir = output_dir or str(constants.OUTPUT_DIR)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    city_slug = city.lower().replace(" ", "_")
    ext = output_format.lower()
    filename = f"{city_slug}_{theme_name}_{timestamp}.{ext}"
    return os.path.join(out_dir, filename)


def save_poster(fig: Figure, config: PosterConfig) -> None:
    """
    Save a matplotlib figure to disk in the configured format.

    Args:
        fig: Matplotlib figure to save
        config: Poster configuration with output path and format
    """
    print(f"Saving to {config.output_file}...")

    fmt = config.output_format.lower()
    save_kwargs: dict = dict(
        facecolor=config.theme.bg,
        bbox_inches="tight",
        pad_inches=0,
    )

    # DPI matters for raster formats and rasterized elements in PDF
    if fmt in ("png", "pdf"):
        save_kwargs["dpi"] = config.dpi

    try:
        plt.savefig(config.output_file, format=fmt, **save_kwargs)
    except OSError as e:
        raise RuntimeError(
            f"Failed to save poster to '{config.output_file}': {e}. "
            f"Check that the directory exists and you have write permissions."
        ) from e
    print(f"\u2713 Done! Poster saved as {config.output_file}")
