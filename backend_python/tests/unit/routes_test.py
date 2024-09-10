from http import HTTPStatus
from typing import Container
from unittest.mock import AsyncMock, Mock

from backend.models import PostGenerationRequest, AgentInfo
import pytest
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

    @pytest.fixture
    def mock_coordinator(self):
        yield AsyncMock(spec=PostCoordinator)

    @pytest.fixture
    def subject(self, test_container: Container, mock_coordinator):
        with test_container.post_coordinator.override(mock_coordinator):
            app = FastAPI()
            app.include_router(router)
            yield TestClient(app)
