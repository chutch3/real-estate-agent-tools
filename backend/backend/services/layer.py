import asyncio
import functools
import io
import logging
from typing import Optional

from PIL import Image

from backend.exceptions import LayerNotFoundError
from backend.repositories.layer import LayerRepository


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


@functools.cache
def _render_empty_tile() -> bytes:
    buf = io.BytesIO()
    Image.new("RGBA", (256, 256), (0, 0, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


class LayerService:
    def __init__(self, repository: LayerRepository) -> None:
        self._repository = repository
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
                tile_zoom = None

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

                    if tile_zoom is None:
                        tile_zoom = meta.get("tile_zoom")

                categories.append(
                    {
                        "id": layer_id,
                        "label": category_config["label"],
                        "date_from": date_from,
                        "date_to": date_to,
                        "record_count": total_count,
                        "bbox": union_bbox,
                        "tile_zoom": tile_zoom,
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
        try:
            return await asyncio.to_thread(self._repository.get_png_tile, layer_id, z, x, y)
        except LayerNotFoundError:
            return _render_empty_tile()
