from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routes.internal import router
from backend.services.property import PropertyService


class TestInternalRoutes:
    def test_get_internal_counties(self, subject, mock_property_service):
        mock_property_service.list_county_fips.return_value = ["21111"]

        response = subject.get("/internal/counties")

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"county_fips": ["21111"]}
        mock_property_service.list_county_fips.assert_awaited_once()

    @pytest.fixture
    def mock_property_service(self):
        yield AsyncMock(spec=PropertyService)

    @pytest.fixture
    def subject(self, test_container, mock_property_service):
        with test_container.override_providers(
            property_service=mock_property_service,
        ):
            app = FastAPI()
            app.include_router(router)
            yield TestClient(app)
