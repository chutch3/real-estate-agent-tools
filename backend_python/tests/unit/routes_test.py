from http import HTTPStatus
from typing import Container
from unittest.mock import AsyncMock, Mock

from backend.clients.google_maps import GoogleMapsClient
import pytest
from backend.exceptions import AddressNotFoundError, PropertyNotFoundError
from backend.models import (
    AgentInfo,
    GeocodeLocation,
    GeocodeRequest,
    GeocodeResponse,
    PostGenerationRequest,
)
from backend.post_coordinator import PostCoordinator
from backend.routes import router
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestRoutes:
    @pytest.mark.parametrize(
        "actual_request, expected_response",
        [
            (
                PostGenerationRequest(
                    address="123 Main St, Anytown, USA",
                    agent_info=AgentInfo(
                        agent_name="John Doe",
                        agent_company="John Doe Real Estate",
                        agent_contact="john.doe@example.com",
                    ),
                ),
                {"post": "This is a test post"},
            ),
            (
                PostGenerationRequest(
                    address="456 Main St, Anytown, USA",
                    agent_info=AgentInfo(
                        agent_name="Jane Doe",
                        agent_company="Jane Doe Real Estate",
                        agent_contact="jane.doe@example.com",
                    ),
                ),
                {"post": "this is another test post"},
            ),
        ],
    )
    def test_generate_post(
        self, subject, mock_coordinator, actual_request, expected_response
    ):
        mock_coordinator.generate_post.return_value = expected_response["post"]
        response = subject.post("/generate-post", json=actual_request.model_dump())
        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == expected_response

    def test_generate_post_with_invalid_address(self, subject, mock_coordinator):
        request = PostGenerationRequest(
            address="Invalid Address",
            agent_info=AgentInfo(
                agent_name="John Doe",
                agent_company="John Doe Real Estate",
                agent_contact="john.doe@example.com",
            ),
        )

        mock_coordinator.generate_post.side_effect = PropertyNotFoundError()
        response = subject.post("/generate-post", json=request.model_dump())
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "Property not found"}

    def test_geocode(self, subject, mock_google_maps_client):
        expected = GeocodeLocation(latitude=40.7128, longitude=-74.006)
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
    def mock_coordinator(self):
        yield AsyncMock(spec=PostCoordinator)

    @pytest.fixture
    def mock_google_maps_client(self):
        yield AsyncMock(spec=GoogleMapsClient)

    @pytest.fixture
    def subject(
        self,
        test_container: Container,
        mock_coordinator: AsyncMock,
        mock_google_maps_client: AsyncMock,
    ):
        with test_container.override_providers(
            post_coordinator=mock_coordinator,
            google_maps_client=mock_google_maps_client,
        ):
            app = FastAPI()
            app.include_router(router)
            yield TestClient(app)
