import asyncio
import logging
from typing import Callable, Optional

from backend.repositories.layer import LayerRepository
from backend.services.crime_layer import (
    _crime_colormap,
    _render_empty_tile,
    _render_float_tile,
    _sync_get_tile,
    _violent_colormap,
)

_LAYER_COLORMAPS: dict[str, Callable[[], dict]] = {
    "crime-violent": _violent_colormap,
    "crime-property": _crime_colormap,
}


def _colormap_for_layer_id(layer_id: str) -> dict:
    if layer_id not in _LAYER_COLORMAPS:
        raise ValueError(f"unknown layer: {layer_id!r}")
    return _LAYER_COLORMAPS[layer_id]()


_LAYER_CONFIG: list[dict] = [
    {
        "id": "crime",
        "label": "Crime",
        "categories": [
            {"id": "crime-violent", "label": "Violent Crime"},
            {"id": "crime-property", "label": "Property Crime"},
        ],
    }
]


def _build_vsi_path(bucket_name: str, layer_id: str, region_slug: str) -> str:
    return f"/vsis3/{bucket_name}/layers/{layer_id}/{region_slug}/latest.tif"


class LayerService:
    def __init__(self, repository: LayerRepository, bucket_name: str) -> None:
        self._repository = repository
        self._bucket_name = bucket_name
        self._logger = logging.getLogger(self.__class__.__name__)
        self._region_slugs_cache: dict[str, list[str]] = {}

    def _get_region_slugs(self, layer_id: str) -> list[str]:
        if layer_id not in self._region_slugs_cache:
            self._region_slugs_cache[layer_id] = self._repository.list_region_slugs(layer_id)
        return self._region_slugs_cache[layer_id]

    async def get_layers(self, county_fips: Optional[str] = None) -> dict:
        groups = []
        for group_config in _LAYER_CONFIG:
            categories = []
            for category_config in group_config["categories"]:
                layer_id = category_config["id"]

                if county_fips is not None:
                    slugs = [county_fips] if self._repository.has_region(layer_id, county_fips) else []
                else:
                    slugs = self._get_region_slugs(layer_id)

                if not slugs:
                    continue

                total_count = 0
                date_from = None
                date_to = None
                union_bbox = None

                for slug in slugs:
                    meta = self._repository.get_meta(layer_id, slug)
                    total_count += meta.get("record_count", 0)

                    if date_from is None or meta.get("date_from", "") < date_from:
                        date_from = meta.get("date_from")
                    if date_to is None or meta.get("date_to", "") > date_to:
                        date_to = meta.get("date_to")

                    bbox = meta.get("bbox")
                    if bbox is not None:
                        if union_bbox is None:
                            union_bbox = list(bbox)
                        else:
                            union_bbox[0] = min(union_bbox[0], bbox[0])
                            union_bbox[1] = min(union_bbox[1], bbox[1])
                            union_bbox[2] = max(union_bbox[2], bbox[2])
                            union_bbox[3] = max(union_bbox[3], bbox[3])

                categories.append(
                    {
                        "id": layer_id,
                        "label": category_config["label"],
                        "date_from": date_from,
                        "date_to": date_to,
                        "record_count": total_count,
                        "bbox": union_bbox,
                    }
                )

            if categories:
                groups.append(
                    {
                        "id": group_config["id"],
                        "label": group_config["label"],
                        "categories": categories,
                    }
                )

        return {"groups": groups}

    async def get_tile(self, layer_id: str, z: int, x: int, y: int) -> bytes:
        slugs = self._get_region_slugs(layer_id)
        if not slugs:
            self._logger.info("No regions found for layer %s, returning empty tile", layer_id)
            return _render_empty_tile()

        vsi_paths = [_build_vsi_path(self._bucket_name, layer_id, slug) for slug in slugs]
        colormap = _colormap_for_layer_id(layer_id)
        return await asyncio.to_thread(_sync_get_tile, vsi_paths, z, x, y, colormap)
