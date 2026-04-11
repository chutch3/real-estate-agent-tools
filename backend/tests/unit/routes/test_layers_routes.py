from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routes.layers import router
from backend.services.layer import LayerService


class TestLayerRoutes:
    def test_get_layers_returns_groups(self, subject, mock_layer_service):
        mock_layer_service.get_layers.return_value = {
            "groups": [
                {
                    "id": "crime",
                    "label": "Crime",
                    "categories": [
                        {
                            "id": "crime-violent",
                            "label": "Violent Crime",
                            "date_from": "2025-04-01",
                            "date_to": "2026-04-01",
                            "record_count": 42,
                            "bbox": [-86.035, 37.997, -85.404, 38.375],
                        }
                    ],
                }
            ]
        }

        response = subject.get("/layers")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert len(body["groups"]) == 1
        assert body["groups"][0]["id"] == "crime"
        mock_layer_service.get_layers.assert_awaited_once_with(county_fips=None)

    def test_get_layers_passes_county_fips_to_service(self, subject, mock_layer_service):
        mock_layer_service.get_layers.return_value = {"groups": []}

        response = subject.get("/layers?county_fips=21111")

        assert response.status_code == HTTPStatus.OK
        mock_layer_service.get_layers.assert_awaited_once_with(county_fips="21111")

    def test_get_layer_tile_returns_png(self, subject, mock_layer_service):
        mock_layer_service.get_tile.return_value = b"\x89PNG fake"

        response = subject.get("/layers/crime-violent/tiles/0/0/0")

        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "image/png"
        assert response.content == b"\x89PNG fake"
        mock_layer_service.get_tile.assert_awaited_once_with(layer_id="crime-violent", z=0, x=0, y=0)

    def test_get_layer_tile_returns_cache_control_header(self, subject, mock_layer_service):
        mock_layer_service.get_tile.return_value = b"\x89PNG fake"

        response = subject.get("/layers/crime-violent/tiles/0/0/0")

        assert response.headers["cache-control"] == "public, max-age=604800"

    @pytest.fixture
    def mock_layer_service(self):
        return AsyncMock(spec=LayerService)

    @pytest.fixture
    def subject(self, test_container, mock_layer_service):
        with test_container.override_providers(
            layer_service=mock_layer_service,
        ):
            app = FastAPI()
            app.include_router(router)
            yield TestClient(app)
