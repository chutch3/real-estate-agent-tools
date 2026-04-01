import json
from dataclasses import dataclass
from pathlib import Path

import yaml
from shapely.geometry import Polygon, shape

from pipeline.sources.arcgis import ArcGISFeatureSource
from pipeline.sources.base import Source
from pipeline.sources.socrata import SocrataSource

_REGIONS_DIR = Path(__file__).parent.parent.parent / "regions"


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
        return SocrataSource(
            name=spec["name"],
            dataset_id=spec["dataset_id"],
            date_field=spec["date_field"],
            lat_field=spec["lat_field"],
            lon_field=spec["lon_field"],
            category_field=spec["category_field"],
            base_url=f"https://{spec['domain']}",
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
