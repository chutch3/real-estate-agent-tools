from http import HTTPStatus
from typing import Container
from unittest.mock import AsyncMock, Mock

from backend.clients.google_maps import GoogleMapsClient
from backend.template_loader import TemplateLoader
import pytest
from backend.exceptions import AddressNotFoundError, PropertyNotFoundError
from backend.models import (
    AgentInfo,
    GeocodeLocation,
    GeocodeRequest,
    GeocodeResponse,
    PostGenerationRequest,
    TemplateResponse,
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

    def test_get_default_template(self, subject, mock_template_loader):
        mock_template_loader.read_user_prompt.return_value = "This is a test template"
        response = subject.get("/default-template")
        assert response.status_code == HTTPStatus.OK
        assert (
            response.json()
            == TemplateResponse(template="This is a test template").model_dump()
        )

    @pytest.fixture
    def mock_coordinator(self):
        yield AsyncMock(spec=PostCoordinator)

    @pytest.fixture
    def mock_google_maps_client(self):
        yield AsyncMock(spec=GoogleMapsClient)

    @pytest.fixture
    def mock_template_loader(self):
        yield Mock(spec=TemplateLoader)

    @pytest.fixture
    def subject(
        self,
        test_container: Container,
        mock_coordinator: AsyncMock,
        mock_google_maps_client: AsyncMock,
        mock_template_loader: Mock,
    ):
        with test_container.override_providers(
            post_coordinator=mock_coordinator,
            google_maps_client=mock_google_maps_client,
            template_loader=mock_template_loader,
        ):
            app = FastAPI()
            app.include_router(router)
            yield TestClient(app)
