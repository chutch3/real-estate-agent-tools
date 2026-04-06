import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from prefect import flow, task
from prefect.cache_policies import NO_CACHE
from prefect.concurrency.sync import concurrency

from pipeline.cache import make_cache_key
from pipeline.tiles.colormaps import LAYER_COLORMAPS
from pipeline.tiles.rendering import BASE_ZOOM, render_png_tile, tiles_for_polygon
from rasterio.crs import CRS
from rasterio.features import geometry_mask
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, calculate_default_transform, reproject
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from scipy.stats import gaussian_kde
from shapely.geometry import Point, Polygon, mapping

from pipeline.clients.backend import BackendClient
from pipeline.geocoding.base import AddressRecord, Geocoder
from pipeline.geocoding.census import CensusGeocoder
from pipeline.regions.loader import Region, load_region_by_fips
from pipeline.sources.base import Source
from pipeline.storage.base import TileStorage
from pipeline.storage.s3 import S3TileStorage

_logger = logging.getLogger(__name__)

_RESOLUTION_M = 200
_DATA_TILE_VERSION = "v1"


@dataclass
class KdeGrid:
    values: np.ndarray
    bounds: tuple[float, float, float, float]
    width: int
    height: int


def _compute_kde_grid(records: gpd.GeoDataFrame, polygon: Polygon) -> KdeGrid:
    minx, miny, maxx, maxy = polygon.bounds
    resolution_deg = _RESOLUTION_M / 111_320  # ~200m in degrees at mid-latitude
    width = max(int((maxx - minx) / resolution_deg), 10)
    height = max(int((maxy - miny) / resolution_deg), 10)

    grid = np.zeros((height, width), dtype=np.float32)

    if len(records) >= 2:
        lons = records["lon"].values.astype(np.float64)
        lats = records["lat"].values.astype(np.float64)
        try:
            kde = gaussian_kde(np.vstack([lons, lats]))
            xs = np.linspace(minx, maxx, width)
            ys = np.linspace(maxy, miny, height)
            xx, yy = np.meshgrid(xs, ys)
            positions = np.vstack([xx.ravel(), yy.ravel()])
            density = kde(positions).reshape(height, width).astype(np.float32)
            max_val = density.max()
            if max_val > 0:
                grid = density / max_val
        except np.linalg.LinAlgError:
            _logger.warning(
                "KDE estimation failed for %d records (data may be collinear); returning zero grid",
                len(records),
            )
    elif len(records) == 1:
        grid[height // 2, width // 2] = 1.0

    outside = geometry_mask(
        [mapping(polygon)],
        out_shape=(height, width),
        transform=from_bounds(minx, miny, maxx, maxy, width, height),
    )
    grid[outside] = 0.0

    return KdeGrid(
        values=grid,
        bounds=(minx, miny, maxx, maxy),
        width=width,
        height=height,
    )


@task(cache_key_fn=make_cache_key("fetch_raw"), persist_result=True)
def fetch_raw(source: Source, polygon: Polygon, date_from: date, date_to: date) -> gpd.GeoDataFrame:
    return source.fetch(polygon, date_from, date_to)


@task
def combine_and_clip(frames: list[gpd.GeoDataFrame], polygon: Polygon) -> gpd.GeoDataFrame:
    if not frames:
        return gpd.GeoDataFrame(
            columns=["lat", "lon", "category", "date", "source", "geometry"],
            geometry="geometry",
            crs="EPSG:4326",
        )
    combined = gpd.GeoDataFrame(
        pd.concat(frames, ignore_index=True),
        geometry="geometry",
        crs="EPSG:4326",
    )
    clipped = combined[combined.geometry.notna() & combined.geometry.within(polygon)].copy()
    return clipped


_GEOCODE_BATCH_SIZE = 1_000
_CENSUS_CONCURRENCY_LIMIT = "census-geocoder"


@task(cache_key_fn=make_cache_key("geocode_batch"), persist_result=True, retries=3, retry_delay_seconds=60)
def geocode_batch(addresses: list[AddressRecord], geocoder: Geocoder) -> dict[int, tuple[float, float]]:
    with concurrency(_CENSUS_CONCURRENCY_LIMIT, occupy=1):
        return geocoder.geocode(addresses)


@task(cache_key_fn=make_cache_key("geocode_records"), persist_result=True)
def geocode_records(frame: gpd.GeoDataFrame, geocoder: Geocoder) -> gpd.GeoDataFrame:
    if frame.empty:
        return frame

    needs_geocoding = frame.geometry.isna()
    if not needs_geocoding.any():
        return frame

    to_geocode = frame[needs_geocoding]

    addresses = [
        (idx, row.get("address"), row.get("city"), row.get("state"), row.get("zip_code"))
        for idx, row in to_geocode.iterrows()
    ]
    batches = [
        addresses[i : i + _GEOCODE_BATCH_SIZE]
        for i in range(0, len(addresses), _GEOCODE_BATCH_SIZE)
    ]
    futures = [geocode_batch.submit(batch, geocoder) for batch in batches]
    coords: dict[int, tuple[float, float]] = {}
    for future in futures:
        coords.update(future.result())

    matched = len(coords)
    total = len(to_geocode)
    _logger.info("Census geocoder matched %d of %d addresses", matched, total)
    if matched < total:
        _logger.warning("Census geocoder could not match %d address(es)", total - matched)

    already_geocoded = frame[~needs_geocoding].copy()

    new_rows = []
    for idx, row in to_geocode.iterrows():
        if idx in coords:
            lat, lon = coords[idx]
            new_rows.append({
                **{k: v for k, v in row.items() if k != "geometry"},
                "lat": lat,
                "lon": lon,
                "geometry": Point(lon, lat),
            })

    if not new_rows:
        return gpd.GeoDataFrame(already_geocoded, geometry="geometry", crs="EPSG:4326")

    newly_geocoded = gpd.GeoDataFrame(new_rows, geometry="geometry", crs="EPSG:4326")
    combined = gpd.GeoDataFrame(
        pd.concat([already_geocoded, newly_geocoded], ignore_index=True),
        geometry="geometry",
        crs="EPSG:4326",
    )
    return combined


@task(cache_key_fn=make_cache_key("compute_kde_grid"), persist_result=True)
def compute_kde_grid(records: gpd.GeoDataFrame, polygon: Polygon) -> KdeGrid:
    return _compute_kde_grid(records, polygon)


@task(cache_key_fn=make_cache_key("write_cog"), persist_result=True)
def write_cog(kde_grid: KdeGrid) -> bytes:
    minx, miny, maxx, maxy = kde_grid.bounds
    transform = from_bounds(minx, miny, maxx, maxy, kde_grid.width, kde_grid.height)

    src_fd, src_path = tempfile.mkstemp(suffix=".tif")
    os.close(src_fd)
    reproj_fd, reproj_path = tempfile.mkstemp(suffix=".tif")
    os.close(reproj_fd)
    cog_fd, cog_path = tempfile.mkstemp(suffix=".tif")
    os.close(cog_fd)

    try:
        with rasterio.open(
            src_path,
            "w",
            driver="GTiff",
            height=kde_grid.height,
            width=kde_grid.width,
            count=1,
            dtype="float32",
            crs=CRS.from_epsg(4326),
            transform=transform,
        ) as dst:
            dst.write(kde_grid.values, 1)

        with rasterio.open(src_path) as src:
            t, w, h = calculate_default_transform(
                src.crs, CRS.from_epsg(3857), src.width, src.height, *src.bounds
            )
            with rasterio.open(
                reproj_path,
                "w",
                driver="GTiff",
                height=h,
                width=w,
                count=1,
                dtype="float32",
                crs=CRS.from_epsg(3857),
                transform=t,
            ) as dst:
                reproject(
                    source=rasterio.band(src, 1),
                    destination=rasterio.band(dst, 1),
                    src_crs=src.crs,
                    dst_crs=CRS.from_epsg(3857),
                    resampling=Resampling.bilinear,
                )

        cog_translate(
            reproj_path,
            cog_path,
            cog_profiles.get("deflate"),
            overview_level=6,
            overview_resampling="average",
            quiet=True,
        )

        with open(cog_path, "rb") as f:
            return f.read()
    finally:
        for path in [src_path, reproj_path, cog_path]:
            if os.path.exists(path):
                os.unlink(path)


_CATEGORY_LAYER_IDS: dict[str, str] = {
    "violent": "crime-violent",
    "property": "crime-property",
}


@task(cache_policy=NO_CACHE)
def store_data_tile(
    storage: TileStorage,
    cog_bytes: bytes,
    crime_category: str,
    fips: str,
    date_from: date,
    date_to: date,
) -> None:
    storage.store_data_tile(
        crime_category=crime_category,
        resolution_m=_RESOLUTION_M,
        date_from=date_from,
        date_to=date_to,
        version=_DATA_TILE_VERSION,
        fips=fips,
        cog_bytes=cog_bytes,
    )


@task(cache_policy=NO_CACHE)
def render_and_store_png_tiles(
    storage: TileStorage,
    cog_bytes: bytes,
    layer_id: str,
    region: Region,
) -> None:
    colormap = LAYER_COLORMAPS[layer_id]()
    polygon = region.polygon
    for tile in tiles_for_polygon(polygon):
        png_bytes = render_png_tile(
            tile=tile,
            cog_bytes=cog_bytes,
            county_polygon=polygon,
            colormap=colormap,
        )
        storage.store_png_tile(
            layer_id=layer_id,
            z=tile.z,
            x=tile.x,
            y=tile.y,
            png_bytes=png_bytes,
        )


@task(cache_policy=NO_CACHE)
def store_meta(
    storage: TileStorage,
    layer_id: str,
    fips: str,
    records: gpd.GeoDataFrame,
    region: Region,
    date_from: date,
    date_to: date,
) -> None:
    meta = {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "record_count": len(records),
        "bbox": list(region.polygon.bounds),
        "tile_zoom": BASE_ZOOM,
    }
    storage.store_meta(
        layer_id=layer_id,
        fips=fips,
        meta_bytes=json.dumps(meta).encode(),
    )


def execute_heatmap(
    region: Region,
    date_from: date,
    date_to: date,
    storage: TileStorage,
    geocoder: Geocoder | None = None,
) -> None:
    if geocoder is None:
        geocoder = CensusGeocoder()

    frames = [
        fetch_raw(source, region.polygon, date_from, date_to)
        for source in region.sources
    ]
    geocoded_frames = [geocode_records(frame, geocoder) for frame in frames]
    records = combine_and_clip(geocoded_frames, region.polygon)

    fips = region.slug

    for crime_category, layer_id in _CATEGORY_LAYER_IDS.items():
        category_records = (
            records[records["category"] == crime_category] if not records.empty else records
        )
        kde_grid = compute_kde_grid(category_records, region.polygon)
        cog_bytes = write_cog(kde_grid)
        store_data_tile(storage, cog_bytes, crime_category, fips, date_from, date_to)
        render_and_store_png_tiles(storage, cog_bytes, layer_id, region)
        store_meta(storage, layer_id, fips, category_records, region, date_from, date_to)


@flow(name="crime-heatmap-pipeline")
def crime_heatmap_pipeline(
    date_from: str | None = None,
    date_to: str | None = None,
) -> None:
    today = date.today()
    resolved_date_to = date.fromisoformat(date_to) if date_to else today
    resolved_date_from = date.fromisoformat(date_from) if date_from else today - timedelta(days=365)

    backend_url = os.environ["BACKEND_URL"]
    tiger_base_url = os.environ.get("TIGER_BASE_URL", "https://tigerweb.geo.census.gov")
    sources_config_path = os.environ.get("SOURCES_CONFIG_PATH")

    client = BackendClient(base_url=backend_url)
    county_fips_list = client.list_county_fips()

    bucket = os.environ["CRIME_DATA_S3_BUCKET"]
    storage = S3TileStorage(bucket=bucket)

    for fips in county_fips_list:
        region = load_region_by_fips(
            fips,
            tiger_base_url=tiger_base_url,
            sources_config_path=Path(sources_config_path) if sources_config_path else None,
        )
        if region is None:
            _logger.warning("No county boundary found for FIPS %s, skipping", fips)
            continue
        execute_heatmap(region, resolved_date_from, resolved_date_to, storage)
