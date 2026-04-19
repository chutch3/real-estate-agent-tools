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
    def test_generate_post_returns_created(self, subject, mock_coordinator):
        mock_coordinator.generate_post.return_value = "This is a test post"
        response = subject.post(
            "/posts",
            json=PostGenerationRequest(
                property_id="prop-1",
                agent_info=AgentInfo(agent_name="John Doe", agent_company="Acme", agent_contact="john@example.com"),
            ).model_dump(),
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == {"post": "This is a test post"}

    def test_generate_post_passes_property_id_and_brokerage_id(self, subject, mock_coordinator):
        mock_coordinator.generate_post.return_value = "post"
        agent_info = AgentInfo(agent_name="John Doe", agent_company="Acme", agent_contact="john@example.com")
        subject.post(
            "/posts",
            json=PostGenerationRequest(property_id="prop-1", agent_info=agent_info).model_dump(),
        )
        mock_coordinator.generate_post.assert_called_once_with(
            property_id="prop-1",
            brokerage_id="brokerage-123",
            agent_info=agent_info,
            custom_template=None,
        )

    def test_generate_post_returns_404_for_unknown_property(self, subject, mock_coordinator):
        mock_coordinator.generate_post.side_effect = PropertyNotFoundError()
        response = subject.post(
            "/posts",
            json=PostGenerationRequest(
                property_id="missing",
                agent_info=AgentInfo(agent_name="John Doe", agent_company="Acme", agent_contact="j@example.com"),
            ).model_dump(),
        )
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
