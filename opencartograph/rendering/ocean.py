"""
Sea/ocean polygon construction from OSM coastline data.

Converts coastline linestrings into renderable water polygons using the
OSM convention: walking along a coastline, land is on the left and water
is on the right.
"""

from __future__ import annotations

from typing import Any

import geopandas as gpd
import osmnx as ox
from matplotlib.axes import Axes
from shapely.geometry import box as shapely_box
from shapely.ops import linemerge, polygonize, unary_union

from .. import constants


def build_ocean_polygons(
    coastline_gdf: gpd.GeoDataFrame | None,
    crs: Any,
    crop_xlim: tuple[float, float],
    crop_ylim: tuple[float, float],
) -> gpd.GeoDataFrame | None:
    """
    Build ocean polygons from OSM coastline linestrings.

    Clips coastline data to the viewport, merges with the viewport boundary,
    polygonizes into faces, then classifies each face as land or water using
    the coastline direction convention.

    Args:
        coastline_gdf: GeoDataFrame of coastline geometries (may be None)
        crs: Target CRS from the projected street graph
        crop_xlim: Viewport x-limits in projected coordinates
        crop_ylim: Viewport y-limits in projected coordinates

    Returns:
        GeoDataFrame of ocean polygons in projected CRS, or None
    """
    if coastline_gdf is None or coastline_gdf.empty:
        return None

    # Filter to line geometries only
    line_mask = coastline_gdf.geometry.type.isin(["LineString", "MultiLineString"])
    coast_lines = coastline_gdf[line_mask]
    if coast_lines.empty:
        return None

    # Project coastlines to the graph's metric CRS
    try:
        coast_proj = ox.projection.project_gdf(coast_lines, to_crs=crs)
    except (ValueError, RuntimeError):
        try:
            coast_proj = coast_lines.to_crs(crs)
        except Exception:
            return None

    # Build viewport rectangle
    viewport = shapely_box(crop_xlim[0], crop_ylim[0], crop_xlim[1], crop_ylim[1])

    # Merge coastline fragments and clip to viewport
    merged = linemerge(list(coast_proj.geometry))
    clipped = merged.intersection(viewport)
    if clipped.is_empty:
        return None

    # Combine clipped coastline with viewport boundary to form closed regions
    combined = unary_union([clipped, viewport.boundary])

    # Polygonize into candidate faces
    polygons = list(polygonize(combined))
    if not polygons:
        return None

    # Classify each polygon as water or land
    water_polys = [p for p in polygons if _is_water(p, clipped)]
    if not water_polys:
        return None

    return gpd.GeoDataFrame(geometry=water_polys, crs=crs)


def _is_water(polygon, coastline_geom) -> bool:
    """
    Determine if a polygon is on the water side of a coastline.

    Uses the OSM convention: walking along the coastline direction,
    land is to the left (positive cross product) and water is to the
    right (negative cross product).
    """
    test_point = polygon.representative_point()

    # Find the nearest coastline segment
    if coastline_geom.geom_type == "MultiLineString":
        nearest_line = min(
            coastline_geom.geoms, key=lambda line: line.distance(test_point)
        )
    elif coastline_geom.geom_type == "LineString":
        nearest_line = coastline_geom
    else:
        return False

    # Get coastline direction at the nearest point
    param = nearest_line.project(test_point)
    epsilon = 1.0  # 1 meter in projected CRS
    p1 = nearest_line.interpolate(max(0, param - epsilon))
    p2 = nearest_line.interpolate(min(nearest_line.length, param + epsilon))

    # Direction vector of coastline
    dx = p2.x - p1.x
    dy = p2.y - p1.y

    # Vector from coastline to test point
    nearest_pt = nearest_line.interpolate(param)
    cx = test_point.x - nearest_pt.x
    cy = test_point.y - nearest_pt.y

    # Cross product: positive = left = land, negative = right = water
    cross = dx * cy - dy * cx
    return cross < 0


def render_ocean(
    ax: Axes,
    ocean_polys: gpd.GeoDataFrame | None,
    color: str,
) -> None:
    """
    Render ocean polygons onto the axes.

    Args:
        ax: Matplotlib axes
        ocean_polys: GeoDataFrame of ocean polygons (may be None)
        color: Fill color for the ocean
    """
    if ocean_polys is None or ocean_polys.empty:
        return
    ocean_polys.plot(
        ax=ax, facecolor=color, edgecolor="none", zorder=constants.ZORDER_OCEAN,
    )
