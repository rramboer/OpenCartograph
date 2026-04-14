"""
Generate a theme color swatch image showing all themes side by side.

Each theme is rendered as a column of colored rectangles with labels.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from . import constants

COLOR_KEYS = [
    ("bg", "Background"),
    ("text", "Text"),
    ("gradient_color", "Gradient"),
    ("water", "Water"),
    ("parks", "Parks"),
    ("national_parks", "National Parks"),
    ("airports", "Airports"),
    ("runways", "Runways"),
    ("buildings", "Buildings"),
    ("stadiums", "Stadiums"),
    ("road_motorway", "Motorway"),
    ("road_primary", "Primary"),
    ("road_secondary", "Secondary"),
    ("road_tertiary", "Tertiary"),
    ("road_residential", "Residential"),
    ("road_default", "Default Road"),
]


def _load_themes() -> list[dict]:
    themes = []
    for path in sorted(constants.THEMES_DIR.glob("*.json")):
        with open(path) as f:
            themes.append(json.load(f))
    return themes


def _is_light(hex_color: str) -> bool:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return (r * 299 + g * 587 + b * 114) / 1000 > 128


def generate_swatches(output_dir: str | None = None) -> None:
    themes = _load_themes()
    if not themes:
        print("No themes found.")
        return

    n_themes = len(themes)
    n_colors = len(COLOR_KEYS)

    swatch_w = 1.2
    swatch_h = 0.6
    label_col_w = 1.5
    header_h = 1.0

    fig_w = label_col_w + n_themes * swatch_w + 0.5
    fig_h = header_h + n_colors * swatch_h + 0.5

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    for col, theme in enumerate(themes):
        x = label_col_w + col * swatch_w + swatch_w / 2
        y = fig_h - header_h / 2
        ax.text(
            x, y, theme["name"],
            ha="center", va="center",
            fontsize=6, fontweight="bold",
            rotation=45,
        )

    for row, (key, label) in enumerate(COLOR_KEYS):
        y_top = fig_h - header_h - row * swatch_h
        y_bottom = y_top - swatch_h

        ax.text(
            label_col_w - 0.15, (y_top + y_bottom) / 2, label,
            ha="right", va="center", fontsize=7,
        )

        for col, theme in enumerate(themes):
            color = theme.get(key, "#FFFFFF")
            x = label_col_w + col * swatch_w
            rect = mpatches.FancyBboxPatch(
                (x + 0.05, y_bottom + 0.03),
                swatch_w - 0.1, swatch_h - 0.06,
                boxstyle="round,pad=0.02",
                facecolor=color, edgecolor="#CCCCCC", linewidth=0.5,
            )
            ax.add_patch(rect)

            ax.text(
                x + swatch_w / 2, (y_top + y_bottom) / 2, color,
                ha="center", va="center", fontsize=4.5,
                color="#000000" if _is_light(color) else "#FFFFFF",
            )

    out_dir = output_dir or str(constants.OUTPUT_DIR)
    out_path = Path(out_dir) / "theme_swatches.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=200, bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)
    print(f"✓ Theme swatches saved to {out_path}")
