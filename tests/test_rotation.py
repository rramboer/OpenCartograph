"""Tests for opencartograph.rendering.rotation."""

from __future__ import annotations

import numpy as np
import pytest
from geopandas import GeoDataFrame
from networkx import MultiDiGraph
from shapely.geometry import LineString, Point, Polygon

from opencartograph.rendering.rotation import (
    rotate_features,
    rotate_graph,
)


def _make_graph(nodes: dict[int, tuple[float, float]], edges=None) -> MultiDiGraph:
    """Build a simple projected graph with given node positions."""
    g = MultiDiGraph(crs="EPSG:32633")
    for nid, (x, y) in nodes.items():
        g.add_node(nid, x=x, y=y)
    if edges:
        for u, v, data in edges:
            g.add_edge(u, v, **data)
    return g


class TestRotateGraph:
    def test_90_degrees_single_node(self):
        g = _make_graph({1: (1.0, 0.0)})
        rotate_graph(g, center_x=0.0, center_y=0.0, angle=90)
        x = g.nodes[1]["x"]
        y = g.nodes[1]["y"]
        assert x == pytest.approx(0.0, abs=1e-10)
        assert y == pytest.approx(-1.0, abs=1e-10)

    def test_180_degrees(self):
        g = _make_graph({1: (1.0, 0.0)})
        rotate_graph(g, center_x=0.0, center_y=0.0, angle=180)
        assert g.nodes[1]["x"] == pytest.approx(-1.0, abs=1e-10)
        assert g.nodes[1]["y"] == pytest.approx(0.0, abs=1e-10)

    def test_360_degrees_is_identity(self):
        g = _make_graph({1: (3.0, 4.0), 2: (-1.0, 2.0)})
        rotate_graph(g, center_x=0.0, center_y=0.0, angle=360)
        assert g.nodes[1]["x"] == pytest.approx(3.0, abs=1e-10)
        assert g.nodes[1]["y"] == pytest.approx(4.0, abs=1e-10)
        assert g.nodes[2]["x"] == pytest.approx(-1.0, abs=1e-10)
        assert g.nodes[2]["y"] == pytest.approx(2.0, abs=1e-10)

    def test_rotation_around_nonzero_center(self):
        # Rotate (2, 0) around (1, 0) by 90 degrees CW -> (1, -1)
        g = _make_graph({1: (2.0, 0.0)})
        rotate_graph(g, center_x=1.0, center_y=0.0, angle=90)
        assert g.nodes[1]["x"] == pytest.approx(1.0, abs=1e-10)
        assert g.nodes[1]["y"] == pytest.approx(-1.0, abs=1e-10)

    def test_edge_geometry_rotated(self):
        line = LineString([(0, 0), (1, 0)])
        g = _make_graph(
            {1: (0.0, 0.0), 2: (1.0, 0.0)},
            edges=[(1, 2, {"geometry": line})],
        )
        rotate_graph(g, center_x=0.0, center_y=0.0, angle=90)
        rotated_line = g.edges[1, 2, 0]["geometry"]
        coords = list(rotated_line.coords)
        assert coords[0][0] == pytest.approx(0.0, abs=1e-10)
        assert coords[1][0] == pytest.approx(0.0, abs=1e-10)
        assert coords[1][1] == pytest.approx(-1.0, abs=1e-10)

    def test_zero_rotation_is_identity(self):
        g = _make_graph({1: (5.0, 7.0)})
        rotate_graph(g, center_x=0.0, center_y=0.0, angle=0)
        assert g.nodes[1]["x"] == pytest.approx(5.0)
        assert g.nodes[1]["y"] == pytest.approx(7.0)


class TestRotateFeatures:
    def test_none_returns_none(self):
        assert rotate_features(None, 0, 0, 45) is None

    def test_empty_returns_empty(self):
        gdf = GeoDataFrame(geometry=[], crs="EPSG:32633")
        result = rotate_features(gdf, 0, 0, 45)
        assert result.empty

    def test_polygon_rotated_90(self):
        # Square at (1,0)-(2,0)-(2,1)-(1,1), rotate 90 CW around origin
        square = Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])
        gdf = GeoDataFrame(geometry=[square], crs="EPSG:32633")
        result = rotate_features(gdf, center_x=0, center_y=0, angle=90)
        centroid = result.geometry.iloc[0].centroid
        # Original centroid (1.5, 0.5) -> 90 CW -> (0.5, -1.5)
        assert centroid.x == pytest.approx(0.5, abs=1e-10)
        assert centroid.y == pytest.approx(-1.5, abs=1e-10)

    def test_does_not_mutate_original(self):
        point = Point(1, 0)
        gdf = GeoDataFrame(geometry=[point], crs="EPSG:32633")
        rotate_features(gdf, center_x=0, center_y=0, angle=90)
        # Original should be unchanged
        assert gdf.geometry.iloc[0].x == 1.0
        assert gdf.geometry.iloc[0].y == 0.0

    def test_rotation_around_nonzero_center(self):
        point = Point(3, 1)
        gdf = GeoDataFrame(geometry=[point], crs="EPSG:32633")
        result = rotate_features(gdf, center_x=2, center_y=1, angle=90)
        p = result.geometry.iloc[0]
        # (3,1) around (2,1) by 90 CW -> (2, 0)
        assert p.x == pytest.approx(2.0, abs=1e-10)
        assert p.y == pytest.approx(0.0, abs=1e-10)
