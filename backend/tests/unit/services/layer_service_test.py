from unittest.mock import MagicMock

import pytest

from backend.exceptions import LayerNotFoundError
from backend.repositories.layer import LayerRepository
from backend.services.layer import LayerService, _render_empty_tile


class TestLayerService:
    @pytest.fixture
    def repository(self):
        return MagicMock(spec=LayerRepository)

    @pytest.fixture
    def subject(self, repository) -> LayerService:
        return LayerService(repository=repository)

    @pytest.mark.asyncio
    async def test_get_layers_returns_empty_when_no_data(self, subject, repository):
        repository.list_region_slugs.return_value = []

        result = await subject.get_layers()

        assert result == {"groups": []}

    @pytest.mark.asyncio
    async def test_get_layers_returns_group_with_categories_when_data_exists(self, subject, repository):
        repository.list_region_slugs.side_effect = lambda layer_id: (
            ["louisville-metro"] if layer_id in ("crime-violent", "crime-property") else []
        )
        repository.get_meta.return_value = {
            "date_from": "2025-04-01",
            "date_to": "2026-04-01",
            "record_count": 42,
            "bbox": [-86.035, 37.997, -85.404, 38.375],
        }

        result = await subject.get_layers()

        assert len(result["groups"]) == 1
        group = result["groups"][0]
        assert group["id"] == "crime"
        assert group["label"] == "Crime"
        assert len(group["categories"]) == 2
        ids = {c["id"] for c in group["categories"]}
        assert ids == {"crime-violent", "crime-property"}

    @pytest.mark.asyncio
    async def test_get_layers_category_includes_aggregated_meta(self, subject, repository):
        repository.list_region_slugs.side_effect = lambda layer_id: (
            ["louisville-metro"] if layer_id == "crime-violent" else []
        )
        repository.get_meta.return_value = {
            "date_from": "2025-04-01",
            "date_to": "2026-04-01",
            "record_count": 42,
            "bbox": [-86.035, 37.997, -85.404, 38.375],
            "tile_zoom": 12,
        }

        result = await subject.get_layers()

        group = result["groups"][0]
        violent = next(c for c in group["categories"] if c["id"] == "crime-violent")
        assert violent["label"] == "Violent Crime"
        assert violent["date_from"] == "2025-04-01"
        assert violent["date_to"] == "2026-04-01"
        assert violent["record_count"] == 42
        assert violent["bbox"] == [-86.035, 37.997, -85.404, 38.375]
        assert violent["tile_zoom"] == 12

    @pytest.mark.asyncio
    async def test_get_layers_aggregates_record_count_across_regions(self, subject, repository):
        repository.list_region_slugs.side_effect = lambda layer_id: (
            ["region-a", "region-b"] if layer_id == "crime-violent" else []
        )
        repository.get_meta.side_effect = [
            {
                "date_from": "2025-04-01",
                "date_to": "2026-04-01",
                "record_count": 30,
                "bbox": [-86.0, 38.0, -85.5, 38.4],
            },
            {
                "date_from": "2025-04-01",
                "date_to": "2026-04-01",
                "record_count": 20,
                "bbox": [-85.5, 38.0, -85.0, 38.4],
            },
        ]

        result = await subject.get_layers()

        violent = result["groups"][0]["categories"][0]
        assert violent["record_count"] == 50

    @pytest.mark.asyncio
    async def test_get_layers_skips_category_if_no_regions_have_data(self, subject, repository):
        repository.list_region_slugs.side_effect = lambda layer_id: (
            ["louisville-metro"] if layer_id == "crime-violent" else []
        )
        repository.get_meta.return_value = {
            "date_from": "2025-04-01",
            "date_to": "2026-04-01",
            "record_count": 42,
            "bbox": [-86.035, 37.997, -85.404, 38.375],
        }

        result = await subject.get_layers()

        group = result["groups"][0]
        ids = {c["id"] for c in group["categories"]}
        assert "crime-property" not in ids

    @pytest.mark.asyncio
    async def test_get_layers_with_county_fips_returns_matching_layers(self, subject, repository):
        repository.has_region.side_effect = lambda layer_id, fips: layer_id == "crime-violent"
        repository.get_meta.return_value = {
            "date_from": "2025-04-01",
            "date_to": "2026-04-01",
            "record_count": 42,
            "bbox": [-86.035, 37.997, -85.404, 38.375],
        }

        result = await subject.get_layers(county_fips="21111")

        assert len(result["groups"]) == 1
        ids = {c["id"] for c in result["groups"][0]["categories"]}
        assert ids == {"crime-violent"}
        repository.has_region.assert_any_call("crime-violent", "21111")
        repository.has_region.assert_any_call("crime-property", "21111")

    @pytest.mark.asyncio
    async def test_get_layers_with_county_fips_returns_empty_when_no_data(self, subject, repository):
        repository.has_region.return_value = False

        result = await subject.get_layers(county_fips="18019")

        assert result == {"groups": []}

    @pytest.mark.asyncio
    async def test_get_layers_with_county_fips_does_not_call_list_region_slugs(self, subject, repository):
        repository.has_region.return_value = False

        await subject.get_layers(county_fips="21111")

        repository.list_region_slugs.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_tile_returns_bytes_when_tile_exists(self, subject, repository):
        png_bytes = b"\x89PNG-fake"
        repository.get_png_tile.return_value = png_bytes

        result = await subject.get_tile("crime-violent", z=12, x=1234, y=3456)

        assert result == png_bytes
        repository.get_png_tile.assert_called_once_with("crime-violent", 12, 1234, 3456)

    @pytest.mark.asyncio
    async def test_get_tile_returns_empty_png_when_tile_not_found(self, subject, repository):
        repository.get_png_tile.side_effect = LayerNotFoundError("tile not found")

        result = await subject.get_tile("crime-violent", z=12, x=0, y=0)

        assert result == _render_empty_tile()
        repository.get_png_tile.assert_called_once_with("crime-violent", 12, 0, 0)
