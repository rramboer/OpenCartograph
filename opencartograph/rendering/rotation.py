"""
Map rotation utilities.

Rotates the projected graph and feature GeoDataFrames around the map center
so all layers stay aligned.
"""

from __future__ import annotations

import numpy as np
import osmnx as ox
from geopandas import GeoDataFrame
from networkx import MultiDiGraph
from shapely.affinity import rotate as shapely_rotate
from shapely.geometry import Point

from ..models import Coordinates


def get_projected_center(
    center: Coordinates, crs: str,
) -> tuple[float, float]:
    """Project lat/lon center into the graph's metric CRS."""
    pt = ox.projection.project_geometry(
        Point(center.longitude, center.latitude),
        crs="EPSG:4326",
        to_crs=crs,
    )[0]
    return pt.x, pt.y


def rotate_graph(
    g_proj: MultiDiGraph,
    center_x: float,
    center_y: float,
    angle: float,
) -> None:
    """
    Rotate graph nodes and edge geometries in-place.

    Args:
        g_proj: Projected graph (metric CRS)
        center_x: Rotation center X (projected)
        center_y: Rotation center Y (projected)
        angle: Clockwise rotation in degrees
    """
    # Shapely uses counter-clockwise positive
    angle_ccw = -angle
    cos_t = np.cos(np.deg2rad(angle_ccw))
    sin_t = np.sin(np.deg2rad(angle_ccw))

    # Rotate nodes
    for _, data in g_proj.nodes(data=True):
        dx = data["x"] - center_x
        dy = data["y"] - center_y
        data["x"] = center_x + (dx * cos_t - dy * sin_t)
        data["y"] = center_y + (dx * sin_t + dy * cos_t)

    # Rotate edge geometries
    for _, _, data in g_proj.edges(data=True):
        if "geometry" in data:
            data["geometry"] = shapely_rotate(
                data["geometry"], angle_ccw, origin=(center_x, center_y),
            )


def rotate_features(
    gdf: GeoDataFrame | None,
    center_x: float,
    center_y: float,
    angle: float,
) -> GeoDataFrame | None:
    """
    Rotate a GeoDataFrame's geometries around the map center.

    Returns a copy with rotated geometries, or None if input is None/empty.
    """
    if gdf is None or gdf.empty:
        return gdf
    angle_ccw = -angle
    rotated = gdf.copy()
    rotated["geometry"] = rotated["geometry"].apply(
        lambda geom: shapely_rotate(geom, angle_ccw, origin=(center_x, center_y))
    )
    return rotated
