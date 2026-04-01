import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import boto3
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from prefect import flow, task
from prefect.cache_policies import NO_CACHE
from prefect.concurrency.sync import concurrency
from rasterio.crs import CRS
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, calculate_default_transform, reproject
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from scipy.stats import gaussian_kde
from shapely.geometry import Point, Polygon

from pipeline.geocoding.base import AddressRecord, Geocoder
from pipeline.geocoding.census import CensusGeocoder
from pipeline.regions.loader import Region, load_region
from pipeline.sources.base import Source
from pipeline.storage.base import LayerStorage
from pipeline.storage.s3 import S3LayerStorage

_logger = logging.getLogger(__name__)


@dataclass
class KdeGrid:
    values: np.ndarray
    bounds: tuple[float, float, float, float]
    width: int
    height: int


def _compute_kde_grid(records: gpd.GeoDataFrame, polygon: Polygon) -> KdeGrid:
    minx, miny, maxx, maxy = polygon.bounds
    resolution_deg = 200 / 111_320  # ~200m in degrees at mid-latitude
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

    return KdeGrid(
        values=grid,
        bounds=(minx, miny, maxx, maxy),
        width=width,
        height=height,
    )


@task
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


@task(cache_policy=NO_CACHE, retries=3, retry_delay_seconds=60)
def geocode_batch(addresses: list[AddressRecord], geocoder: Geocoder) -> dict[int, tuple[float, float]]:
    with concurrency(_CENSUS_CONCURRENCY_LIMIT, occupy=1):
        return geocoder.geocode(addresses)


@task(cache_policy=NO_CACHE)
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


@task
def compute_kde_grid(records: gpd.GeoDataFrame, polygon: Polygon) -> KdeGrid:
    return _compute_kde_grid(records, polygon)


@task(cache_policy=NO_CACHE)
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

        cog_translate(reproj_path, cog_path, cog_profiles.get("deflate"), quiet=True)

        with open(cog_path, "rb") as f:
            return f.read()
    finally:
        for path in [src_path, reproj_path, cog_path]:
            if os.path.exists(path):
                os.unlink(path)


@task(cache_policy=NO_CACHE)
def upload_layer(
    storage: LayerStorage,
    cog_bytes: bytes,
    region: Region,
    records: gpd.GeoDataFrame,
    generated_at: str,
) -> None:
    storage.store_cog(region.slug, cog_bytes)

    meta = {
        "region_slug": region.slug,
        "generated_at": generated_at,
        "record_count": len(records),
        "bbox": list(region.polygon.bounds),
    }
    storage.store_meta(region.slug, json.dumps(meta).encode())


def execute_heatmap(
    region: Region,
    date_from: date,
    date_to: date,
    storage: LayerStorage,
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
    kde_grid = compute_kde_grid(records, region.polygon)
    cog_bytes = write_cog(kde_grid)
    upload_layer(
        storage,
        cog_bytes,
        region,
        records,
        generated_at=date_to.isoformat(),
    )


@flow(name="crime-heatmap-pipeline")
def crime_heatmap_pipeline(
    region_slug: str,
    date_from: str | None = None,
    date_to: str | None = None,
) -> None:
    today = date.today()
    resolved_date_to = date.fromisoformat(date_to) if date_to else today
    resolved_date_from = date.fromisoformat(date_from) if date_from else today - timedelta(days=365)

    region = load_region(region_slug)
    bucket = os.environ["CRIME_DATA_S3_BUCKET"]
    storage = S3LayerStorage(
        bucket=bucket,
    )

    execute_heatmap(region, resolved_date_from, resolved_date_to, storage)
