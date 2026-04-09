"""
Individual render layers for the poster.

Each layer function renders one visual element onto the matplotlib axes.
Layers are called in order by the pipeline orchestrator.
"""

from __future__ import annotations

import matplotlib.colors as mcolors
import numpy as np
import osmnx as ox
from geopandas import GeoDataFrame
from matplotlib.axes import Axes
from networkx import MultiDiGraph

from .. import constants
from ..models import FontSet, PosterConfig
from ..road_styles import compute_edge_styles
from ..text import compute_city_font_size, format_city_display, make_font


def _render_polygon_layer(
    gdf: GeoDataFrame | None,
    ax: Axes,
    facecolor: str,
    zorder: float,
    min_area_m2: float = constants.MIN_POLYGON_AREA_M2,
) -> None:
    """
    Filter to polygons and plot a GeoDataFrame.

    Expects already-projected data (metric CRS).

    Args:
        gdf: GeoDataFrame of features (may be None or empty)
        ax: Matplotlib axes to plot on
        facecolor: Fill color for polygons
        zorder: Z-order for layer stacking
        min_area_m2: Minimum polygon area in square meters (default filters
            out tiny features like fountains; pass 0 to disable filtering)
    """
    if gdf is None or gdf.empty:
        return
    polys = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])]
    if polys.empty:
        return
    polys = polys[polys.geometry.is_valid & (polys.geometry.area >= min_area_m2)]
    if polys.empty:
        return
    polys.plot(ax=ax, facecolor=facecolor, edgecolor="none", zorder=zorder)


def render_water(
    ax: Axes,
    water: GeoDataFrame | None,
    config: PosterConfig,
) -> None:
    """Render water polygons layer."""
    _render_polygon_layer(
        water, ax,
        config.theme.water, constants.ZORDER_WATER,
    )


def render_parks(
    ax: Axes,
    parks: GeoDataFrame | None,
    config: PosterConfig,
) -> None:
    """Render parks/green space polygons layer."""
    _render_polygon_layer(
        parks, ax,
        config.theme.parks, constants.ZORDER_PARKS,
    )


def render_national_parks(
    ax: Axes,
    national_parks: GeoDataFrame | None,
    config: PosterConfig,
) -> None:
    """Render national park/protected area polygons layer."""
    _render_polygon_layer(
        national_parks, ax,
        config.theme.national_parks, constants.ZORDER_NATIONAL_PARKS,
    )


def render_airports(
    ax: Axes,
    airports: GeoDataFrame | None,
    config: PosterConfig,
) -> None:
    """Render airport ground polygons layer."""
    _render_polygon_layer(
        airports, ax,
        config.theme.airports, constants.ZORDER_AIRPORTS,
    )


def render_runways(
    ax: Axes,
    runways: GeoDataFrame | None,
    config: PosterConfig,
) -> None:
    """Render airport runways/taxiways as lines."""
    if runways is None or runways.empty:
        return
    lines = runways[runways.geometry.type.isin(["LineString", "MultiLineString"])]
    if lines.empty:
        return
    lines.plot(
        ax=ax, color=config.theme.runways,
        linewidth=1.5, zorder=constants.ZORDER_RUNWAYS,
    )


def render_buildings(
    ax: Axes,
    buildings: GeoDataFrame | None,
    config: PosterConfig,
) -> None:
    """Render building footprint polygons layer."""
    _render_polygon_layer(
        buildings, ax,
        config.theme.buildings, constants.ZORDER_BUILDINGS,
        min_area_m2=0,
    )


def render_stadiums(
    ax: Axes,
    stadiums: GeoDataFrame | None,
    config: PosterConfig,
) -> None:
    """Render stadium and sports venue polygons layer."""
    _render_polygon_layer(
        stadiums, ax,
        config.theme.stadiums, constants.ZORDER_STADIUMS,
    )


def render_roads(
    ax: Axes,
    g_proj: MultiDiGraph,
    config: PosterConfig,
) -> None:
    """Render the road network with themed hierarchy colors and widths."""
    print("Applying road hierarchy colors...")
    styles = compute_edge_styles(g_proj, config.theme.roads, config.line_scale)
    ox.plot_graph(
        g_proj,
        ax=ax,
        bgcolor=config.theme.bg,
        node_size=0,
        edge_color=styles.colors,
        edge_linewidth=styles.widths,
        show=False,
        close=False,
    )


def apply_viewport(
    ax: Axes,
    crop_xlim: tuple[float, float],
    crop_ylim: tuple[float, float],
) -> None:
    """Set aspect ratio and crop limits on the axes."""
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(crop_xlim)
    ax.set_ylim(crop_ylim)


def create_gradient_fade(
    ax: Axes, color: str, location: str = "bottom", zorder: float = 10
) -> None:
    """
    Create a smooth fade effect at the top or bottom of the map.

    Uses a float32 RGBA image with bilinear interpolation instead of a
    ListedColormap to eliminate visible colour banding on dark themes.

    Args:
        ax: Matplotlib axes
        color: Background/gradient color (hex string)
        location: 'bottom' or 'top'
        zorder: Z-order for stacking
    """
    n_rows = 1024
    rgb = mcolors.to_rgb(color)

    # Build RGBA image: constant colour, varying alpha
    gradient_img = np.zeros((n_rows, 1, 4), dtype=np.float32)
    gradient_img[:, 0, 0] = rgb[0]
    gradient_img[:, 0, 1] = rgb[1]
    gradient_img[:, 0, 2] = rgb[2]

    if location == "bottom":
        gradient_img[:, 0, 3] = np.linspace(1, 0, n_rows, dtype=np.float32)
        extent_y_start = 0.0
        extent_y_end = constants.GRADIENT_BOTTOM_END
    else:
        gradient_img[:, 0, 3] = np.linspace(0, 1, n_rows, dtype=np.float32)
        extent_y_start = constants.GRADIENT_TOP_START
        extent_y_end = 1.0

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    y_range = ylim[1] - ylim[0]

    y_bottom = ylim[0] + y_range * extent_y_start
    y_top = ylim[0] + y_range * extent_y_end

    ax.imshow(
        gradient_img,
        extent=(xlim[0], xlim[1], y_bottom, y_top),
        aspect="auto",
        interpolation="bilinear",
        zorder=zorder,
        origin="lower",
    )


def render_gradients(ax: Axes, config: PosterConfig) -> None:
    """Render top and bottom gradient fade overlays."""
    create_gradient_fade(
        ax, config.theme.gradient_color,
        location="bottom", zorder=constants.ZORDER_GRADIENT,
    )
    create_gradient_fade(
        ax, config.theme.gradient_color,
        location="top", zorder=constants.ZORDER_GRADIENT,
    )


def render_typography(
    ax: Axes,
    config: PosterConfig,
    default_fonts: FontSet | None,
) -> None:
    """
    Render city name, country, coordinates, optional date, divider line, and attribution.

    Args:
        ax: Matplotlib axes
        config: Poster configuration
        default_fonts: Default FontSet (Roboto), used for attribution fallback
    """
    scale_factor = min(config.height, config.width) / constants.FONT_REFERENCE_DIMENSION
    active_fonts = config.fonts

    # Create font properties for sub-elements
    font_sub = make_font(active_fonts, "light", constants.BASE_FONT_SUB * scale_factor)
    font_coords = make_font(active_fonts, "regular", constants.BASE_FONT_COORDS * scale_factor)

    # Format and size city name
    spaced_city = format_city_display(config.display_city)
    adjusted_font_size = compute_city_font_size(
        config.display_city, constants.BASE_FONT_MAIN, scale_factor
    )
    font_main = make_font(active_fonts, "bold", adjusted_font_size)

    text_color = config.theme.text
    zorder = constants.ZORDER_TEXT

    # City name
    ax.text(
        0.5, constants.TEXT_Y_CITY, spaced_city,
        transform=ax.transAxes, color=text_color,
        ha="center", fontproperties=font_main, zorder=zorder,
    )

    # Country name
    ax.text(
        0.5, constants.TEXT_Y_COUNTRY, config.display_country.upper(),
        transform=ax.transAxes, color=text_color,
        ha="center", fontproperties=font_sub, zorder=zorder,
    )

    # Coordinates
    coords_text = config.center.format_display()
    ax.text(
        0.5, constants.TEXT_Y_COORDS, coords_text,
        transform=ax.transAxes, color=text_color,
        alpha=constants.COORDS_ALPHA, ha="center",
        fontproperties=font_coords, zorder=zorder,
    )

    # Date
    if config.date_text is not None:
        ax.text(
            0.5, constants.TEXT_Y_DATE, config.date_text,
            transform=ax.transAxes, color=text_color,
            alpha=constants.COORDS_ALPHA, ha="center",
            fontproperties=font_coords, zorder=zorder,
        )

    # Divider line
    ax.plot(
        [constants.DIVIDER_X_START, constants.DIVIDER_X_END],
        [constants.TEXT_Y_DIVIDER, constants.TEXT_Y_DIVIDER],
        transform=ax.transAxes, color=text_color,
        linewidth=1 * scale_factor, zorder=zorder,
    )

    # Attribution (bottom right) — always uses default fonts if available
    if config.show_attribution:
        attr_fonts = default_fonts or active_fonts
        font_attr = make_font(attr_fonts, "light", constants.BASE_FONT_ATTR)
        ax.text(
            constants.TEXT_X_ATTR, constants.TEXT_Y_ATTR,
            constants.ATTRIBUTION_TEXT,
            transform=ax.transAxes, color=text_color,
            alpha=constants.ATTRIBUTION_ALPHA, ha="right", va="bottom",
            fontproperties=font_attr, zorder=zorder,
        )
