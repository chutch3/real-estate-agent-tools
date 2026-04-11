from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.clients.google_maps import GoogleMapsClient
from backend.exceptions import AddressNotFoundError
from backend.models import GeocodeLocation, GeocodeRequest, GeocodeResponse
from backend.routes.geocode import router


class TestGeocodeRoutes:
    def test_geocode(self, subject, mock_google_maps_client):
        expected = GeocodeLocation(lat=40.7128, lng=-74.006)
        mock_google_maps_client.geocode.return_value = expected
        response = subject.post(
            "/geocode",
            json=GeocodeRequest(address="123 Main St, Anytown, USA").model_dump(),
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == GeocodeResponse(location=expected).model_dump()

    def test_geocode_with_invalid_address(self, subject, mock_google_maps_client):
        mock_google_maps_client.geocode.side_effect = AddressNotFoundError()
        response = subject.post(
            "/geocode",
            json=GeocodeRequest(address="Invalid Address").model_dump(),
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "Address not found"}

    def test_geocode_all_other_exceptions(self, subject, mock_google_maps_client):
        mock_google_maps_client.geocode.side_effect = Exception()
        response = subject.post(
            "/geocode",
            json=GeocodeRequest(address="123 Main St, Anytown, USA").model_dump(),
        )
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "Unable to geocode address"}

    @pytest.fixture
    def mock_google_maps_client(self):
        yield AsyncMock(spec=GoogleMapsClient)

    @pytest.fixture
    def subject(self, test_container, mock_google_maps_client):
        with test_container.override_providers(
            google_maps_client=mock_google_maps_client,
        ):
            app = FastAPI()
            app.include_router(router)
            yield TestClient(app)
