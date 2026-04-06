import json
import logging
from dataclasses import dataclass
from pathlib import Path

import httpx
import yaml
from shapely.geometry import Polygon, shape

from pipeline.sources.arcgis import ArcGISFeatureSource
from pipeline.sources.base import Source
from pipeline.sources.socrata import SocrataSource

_REGIONS_DIR = Path(__file__).parent.parent.parent / "regions"
_DEFAULT_SOURCES_CONFIG_PATH = _REGIONS_DIR / "sources_config.yml"
_TIGER_COUNTIES_PATH = "/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query"

_logger = logging.getLogger(__name__)


@dataclass
class Region:
    slug: str
    polygon: Polygon
    sources: list[Source]


def _build_source(spec: dict) -> Source | None:
    if spec.get("status") != "active":
        return None
    source_type = spec["type"]
    if source_type == "socrata":
        base_url = spec.get("base_url") or f"https://{spec['domain']}"
        return SocrataSource(
            name=spec["name"],
            dataset_id=spec["dataset_id"],
            date_field=spec["date_field"],
            lat_field=spec["lat_field"],
            lon_field=spec["lon_field"],
            category_field=spec["category_field"],
            base_url=base_url,
        )
    if source_type == "arcgis":
        return ArcGISFeatureSource(
            name=spec["name"],
            service_url=spec["service_url"],
            date_field=spec["date_field"],
            category_field=spec["category_field"],
            address_field=spec["address_field"],
            city_field=spec["city_field"],
            zip_field=spec["zip_field"],
            state_code=spec.get("state_code", "KY"),
        )
    raise ValueError(f"Unknown source type: {source_type}")


def load_region(slug: str, regions_dir: Path | None = None) -> Region:
    base_dir = regions_dir or _REGIONS_DIR
    region_dir = base_dir / slug
    if not region_dir.exists():
        raise ValueError(f"Region not found: {slug}")

    with open(region_dir / "region.geojson") as f:
        geojson = json.load(f)
    polygon = shape(geojson["geometry"])

    with open(region_dir / "sources.yml") as f:
        sources_config = yaml.safe_load(f)

    sources = []
    for spec in sources_config.get("sources", []):
        source = _build_source(spec)
        if source is not None:
            sources.append(source)

    return Region(slug=slug, polygon=polygon, sources=sources)


def load_region_by_fips(
    fips: str,
    tiger_base_url: str = "https://tigerweb.geo.census.gov",
    sources_config_path: Path | None = None,
) -> Region | None:
    response = httpx.get(
        f"{tiger_base_url}{_TIGER_COUNTIES_PATH}",
        params={
            "f": "json",
            "where": f"GEOID LIKE '{fips}%'",
            "returnGeometry": "true",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "orderByFields": "BASENAME",
            "resultRecordCount": 1,
            "outSR": 4326,
        },
    )
    response.raise_for_status()
    features = response.json().get("features", [])
    if not features:
        _logger.warning("No county boundary found in TIGERweb for FIPS %s", fips)
        return None

    rings = features[0]["geometry"]["rings"]
    polygon = Polygon(rings[0], rings[1:])

    config_path = sources_config_path or _DEFAULT_SOURCES_CONFIG_PATH
    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    sources = []
    for spec in config.get(fips, []):
        source = _build_source(spec)
        if source is not None:
            sources.append(source)

    return Region(slug=fips, polygon=polygon, sources=sources)
