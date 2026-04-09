"""
Poster rendering pipeline orchestrator.

Coordinates data fetching, figure setup, layer rendering, and file output.
"""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt
import osmnx as ox
from geopandas import GeoDataFrame
from networkx import MultiDiGraph
from tqdm import tqdm

from ..models import FontSet, PosterConfig
from ..osm import fetch_features, fetch_graph
from ..output import save_poster
from .layers import (
    apply_viewport,
    render_airports,
    render_buildings,
    render_gradients,
    render_national_parks,
    render_parks,
    render_roads,
    render_runways,
    render_stadiums,
    render_typography,
    render_water,
)
from .compass import draw_north_badge
from .ocean import build_ocean_polygons, render_ocean
from .rotation import get_projected_center, rotate_features, rotate_graph
from .viewport import get_crop_limits, setup_figure


@dataclass
class MapData:
    """All fetched OSM data needed for rendering."""

    graph: MultiDiGraph
    water: GeoDataFrame | None
    parks: GeoDataFrame | None
    national_parks: GeoDataFrame | None
    airports: GeoDataFrame | None
    runways: GeoDataFrame | None
    buildings: GeoDataFrame | None
    stadiums: GeoDataFrame | None
    coastline: GeoDataFrame | None


def fetch_map_data(config: PosterConfig, compensated_dist: int) -> MapData:
    """
    Fetch all OSM data (street network, water, parks) with progress bar.

    Args:
        config: Poster configuration
        compensated_dist: Distance compensated for aspect ratio

    Returns:
        MapData with all fetched data

    Raises:
        RuntimeError: If street network data cannot be retrieved
    """
    # Total steps depend on which optional layers are requested
    total_steps = 4  # street, water, parks, coastline
    if config.show_national_parks:
        total_steps += 1
    if config.show_airports:
        total_steps += 1
    if config.show_buildings:
        total_steps += 1
    if config.show_stadiums:
        total_steps += 1

    national_parks: GeoDataFrame | None = None
    airports: GeoDataFrame | None = None
    runways: GeoDataFrame | None = None
    buildings: GeoDataFrame | None = None
    stadiums: GeoDataFrame | None = None

    with tqdm(
        total=total_steps,
        desc="Fetching map data",
        unit="step",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
    ) as pbar:
        # 1. Fetch Street Network
        pbar.set_description("Downloading street network")
        g = fetch_graph(config.center, compensated_dist)
        if g is None:
            raise RuntimeError("Failed to retrieve street network data.")
        pbar.update(1)

        # 2. Fetch Water Features
        pbar.set_description("Downloading water features")
        water = fetch_features(
            config.center,
            compensated_dist,
            tags={"natural": ["water", "bay", "strait"], "waterway": "riverbank"},
            name="water",
        )
        pbar.update(1)

        # 3. Fetch Parks
        pbar.set_description("Downloading parks/green spaces")
        parks = fetch_features(
            config.center,
            compensated_dist,
            tags={"leisure": "park", "landuse": ["grass", "cemetery"], "natural": "wood"},
            name="parks",
        )
        pbar.update(1)

        # Track which explicitly-requested optional layers failed to fetch
        failed_layers: list[str] = []

        # 4. Fetch National Parks (optional)
        if config.show_national_parks:
            pbar.set_description("Downloading national parks")
            national_parks = fetch_features(
                config.center,
                compensated_dist,
                tags={"boundary": ["national_park", "protected_area"], "leisure": "nature_reserve"},
                name="national_parks",
            )
            if national_parks is None:
                failed_layers.append("national parks")
            pbar.update(1)

        # 5. Fetch Airports (optional; combined polygons + lines)
        if config.show_airports:
            pbar.set_description("Downloading airports")
            aero = fetch_features(
                config.center,
                compensated_dist,
                tags={"aeroway": ["aerodrome", "apron", "helipad", "runway", "taxiway"]},
                name="aeroway",
            )
            if aero is None:
                failed_layers.append("airports")
            elif not aero.empty:
                aero_type = aero.geometry.type
                airports = aero[aero_type.isin(["Polygon", "MultiPolygon"])]
                runways = aero[aero_type.isin(["LineString", "MultiLineString"])]
                if airports.empty:
                    airports = None
                if runways.empty:
                    runways = None
            pbar.update(1)

        # Fetch Buildings (optional; heavy for dense cities)
        if config.show_buildings:
            pbar.set_description("Downloading buildings")
            buildings = fetch_features(
                config.center,
                compensated_dist,
                tags={"building": True},
                name="buildings",
            )
            if buildings is None:
                failed_layers.append("buildings")
            pbar.update(1)

        # Fetch Stadiums (optional)
        if config.show_stadiums:
            pbar.set_description("Downloading stadiums")
            stadiums = fetch_features(
                config.center,
                compensated_dist,
                tags={"leisure": ["stadium", "sports_centre"]},
                name="stadiums",
            )
            if stadiums is None:
                failed_layers.append("stadiums")
            pbar.update(1)

        # Fetch Coastline
        pbar.set_description("Downloading coastline")
        coastline = fetch_features(
            config.center,
            compensated_dist,
            tags={"natural": "coastline"},
            name="coastline",
        )
        pbar.update(1)

    if failed_layers:
        print(
            f"\u26a0 Warning: requested layer(s) failed to fetch and will be "
            f"missing from the poster: {', '.join(failed_layers)}"
        )
    else:
        print("\u2713 All data retrieved successfully!")
    return MapData(
        graph=g, water=water, parks=parks,
        national_parks=national_parks, airports=airports, runways=runways,
        buildings=buildings, stadiums=stadiums,
        coastline=coastline,
    )


def _project_features(gdf: GeoDataFrame | None, crs: str) -> GeoDataFrame | None:
    """Project a GeoDataFrame to the target CRS, returning None if empty."""
    if gdf is None or gdf.empty:
        return gdf
    try:
        return ox.projection.project_gdf(gdf)
    except (ValueError, RuntimeError):
        return gdf.to_crs(crs)


def compose_poster(
    config: PosterConfig, default_fonts: FontSet | None = None
) -> str:
    """
    Orchestrate the full poster rendering pipeline.

    Args:
        config: Complete poster configuration
        default_fonts: Default FontSet (Roboto) for attribution text

    Returns:
        Path to the saved output file
    """
    print(f"\nGenerating map for {config.city}, {config.country}...")

    # Compute compensated distance for viewport crop
    compensated_dist = int(
        config.dist
        * (max(config.height, config.width) / min(config.height, config.width))
        / 4
    )

    # Fetch all map data
    map_data = fetch_map_data(config, compensated_dist)

    # Setup figure
    print("Rendering map...")
    fig, ax = setup_figure(config)

    # Project graph to metric CRS
    g_proj = ox.project_graph(map_data.graph)
    crs = g_proj.graph["crs"]

    # Project feature layers to the same metric CRS
    proj_water = _project_features(map_data.water, crs)
    proj_parks = _project_features(map_data.parks, crs)
    proj_national_parks = _project_features(map_data.national_parks, crs)
    proj_airports = _project_features(map_data.airports, crs)
    proj_runways = _project_features(map_data.runways, crs)
    proj_buildings = _project_features(map_data.buildings, crs)
    proj_stadiums = _project_features(map_data.stadiums, crs)
    proj_coastline = _project_features(map_data.coastline, crs)

    # Apply rotation if requested (in metric space, before crop limits)
    if config.orientation_offset != 0:
        cx, cy = get_projected_center(config.center, crs)
        rotate_graph(g_proj, cx, cy, config.orientation_offset)
        proj_water = rotate_features(proj_water, cx, cy, config.orientation_offset)
        proj_parks = rotate_features(proj_parks, cx, cy, config.orientation_offset)
        proj_national_parks = rotate_features(
            proj_national_parks, cx, cy, config.orientation_offset,
        )
        proj_airports = rotate_features(proj_airports, cx, cy, config.orientation_offset)
        proj_runways = rotate_features(proj_runways, cx, cy, config.orientation_offset)
        proj_buildings = rotate_features(proj_buildings, cx, cy, config.orientation_offset)
        proj_stadiums = rotate_features(proj_stadiums, cx, cy, config.orientation_offset)
        proj_coastline = rotate_features(
            proj_coastline, cx, cy, config.orientation_offset,
        )

    # Compute viewport crop limits early (ocean polygons need them)
    crop_xlim, crop_ylim = get_crop_limits(
        g_proj, config.center, fig, compensated_dist
    )

    # Build and render ocean from coastline data
    ocean_polys = build_ocean_polygons(
        proj_coastline, crs, crop_xlim, crop_ylim,
    )
    render_ocean(ax, ocean_polys, config.theme.water)

    # Render layers in order (already projected)
    render_national_parks(ax, proj_national_parks, config)
    render_airports(ax, proj_airports, config)
    render_parks(ax, proj_parks, config)
    render_stadiums(ax, proj_stadiums, config)
    render_runways(ax, proj_runways, config)
    render_water(ax, proj_water, config)
    render_buildings(ax, proj_buildings, config)
    render_roads(ax, g_proj, config)

    # Apply viewport crop
    apply_viewport(ax, crop_xlim, crop_ylim)

    # Render overlays
    render_gradients(ax, config)
    if not config.no_text:
        render_typography(ax, config, default_fonts)

    if config.show_north:
        draw_north_badge(ax, config.orientation_offset, config.theme.text)

    # Save and cleanup
    save_poster(fig, config)
    plt.close(fig)

    return config.output_file
