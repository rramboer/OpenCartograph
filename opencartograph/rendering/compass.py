"""
North compass badge for rotated maps.

Draws a simple compass arrow indicating north when the map is rotated.
"""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes
from matplotlib.patches import FancyArrowPatch

from .. import constants


def draw_north_badge(
    ax: Axes,
    orientation_offset: float,
    text_color: str,
) -> None:
    """
    Draw a north-pointing arrow badge on the map.

    The arrow rotates opposite to the map rotation so it always
    points toward geographic north. Positioned in axes-fraction
    coordinates so it stays consistent regardless of map extent.

    Args:
        ax: Matplotlib axes
        orientation_offset: Map rotation in degrees (clockwise positive)
        text_color: Theme text color for the badge
    """
    # Convert axes-fraction position to data coordinates
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_range = xlim[1] - xlim[0]
    y_range = ylim[1] - ylim[0]

    cx = xlim[0] + x_range * constants.COMPASS_X_FRAC
    cy = ylim[0] + y_range * constants.COMPASS_Y_FRAC

    arrow_len = min(x_range, y_range) * constants.COMPASS_SIZE_FRAC

    # Arrow points toward geographic north
    angle_rad = np.deg2rad(orientation_offset)
    dx = arrow_len * np.sin(angle_rad)
    dy = arrow_len * np.cos(angle_rad)

    arrow = FancyArrowPatch(
        (cx - dx * 0.4, cy - dy * 0.4),
        (cx + dx * 0.6, cy + dy * 0.6),
        arrowstyle="->,head_length=6,head_width=3",
        color=text_color,
        linewidth=1,
        zorder=constants.ZORDER_COMPASS,
    )
    ax.add_patch(arrow)

    # "N" label at the tip
    label_x = cx + dx * 0.75
    label_y = cy + dy * 0.75
    ax.text(
        label_x, label_y, "N",
        color=text_color,
        fontsize=10,
        fontweight="bold",
        ha="center", va="center",
        zorder=constants.ZORDER_COMPASS,
    )
