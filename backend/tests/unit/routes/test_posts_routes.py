from http import HTTPStatus
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth import get_current_user
from backend.exceptions import PropertyNotFoundError
from backend.models import AgentInfo, PostGenerationRequest, User
from backend.post_coordinator import PostCoordinator
from backend.routes.posts import router


class TestPostRoutes:
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
                    custom_template="This is a custom template",
                ),
                {"post": "this is another test post"},
            ),
        ],
    )
    def test_generate_post(self, subject, mock_coordinator, actual_request, expected_response):
        mock_coordinator.generate_post.return_value = expected_response["post"]
        response = subject.post("/posts", json=actual_request.model_dump())
        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == expected_response

        mock_coordinator.generate_post.assert_called_once_with(
            address=actual_request.address,
            agent_info=actual_request.agent_info,
            custom_template=actual_request.custom_template,
        )

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
        response = subject.post("/posts", json=request.model_dump())
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {"detail": "Property not found"}

    @pytest.fixture
    def mock_coordinator(self):
        yield AsyncMock(spec=PostCoordinator)

    @pytest.fixture
    def mock_current_user(self):
        return User(id="user-123", email="test@test.com", role="AGENT", brokerage_id="brokerage-123")

    @pytest.fixture
    def subject(self, test_container, mock_coordinator, mock_current_user):
        with test_container.override_providers(
            post_coordinator=mock_coordinator,
        ):
            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[get_current_user] = lambda: mock_current_user
            yield TestClient(app)
            app.dependency_overrides.clear()
