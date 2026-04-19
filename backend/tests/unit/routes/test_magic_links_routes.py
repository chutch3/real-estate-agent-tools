from datetime import UTC, datetime
from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth import get_current_user
from backend.exceptions import InvalidMagicLinkError
from backend.models import MagicLinkToken, Property, Representation, User
from backend.repositories.properties import PropertyRepository
from backend.repositories.representation import RepresentationRepository
from backend.routes.magic_links import router
from backend.services.magic_link import MagicLinkService
from backend.services.rate_limiter import RateLimiter


class TestMagicLinksRoutes:
    def test_create_magic_link_returns_201(self, subject, mock_magic_link_service):
        token = MagicLinkToken(
            id="tok-1",
            representation_id="rep-1",
            token="abc-uuid",
            expires_at=datetime.now(UTC),
        )
        mock_magic_link_service.create_magic_link.return_value = token

        response = subject.post("/representations/rep-1/magic-links")

        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert body["token"] == "abc-uuid"
        assert body["id"] == "tok-1"
        mock_magic_link_service.create_magic_link.assert_called_once_with("rep-1", "brokerage-123")

    def test_create_magic_link_returns_404_when_representation_not_found(self, subject, mock_magic_link_service):
        mock_magic_link_service.create_magic_link.side_effect = InvalidMagicLinkError("not found")

        response = subject.post("/representations/missing/magic-links")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_list_magic_links_returns_200(self, subject, mock_magic_link_service):
        mock_magic_link_service.list_tokens.return_value = []

        response = subject.get("/representations/rep-1/magic-links")

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"tokens": []}

    def test_revoke_magic_link_returns_204(self, subject, mock_magic_link_service):
        response = subject.delete("/representations/rep-1/magic-links/tok-1")

        assert response.status_code == HTTPStatus.NO_CONTENT
        mock_magic_link_service.revoke_token.assert_called_once_with("tok-1", "brokerage-123")

    def test_create_session_uses_x_forwarded_for_for_rate_limiting(
        self,
        subject,
        mock_magic_link_service,
        mock_representation_repository,
        mock_property_repository,
        mock_rate_limiter,
    ):
        token = MagicLinkToken(
            id="tok-1",
            representation_id="rep-1",
            token="abc-uuid",
            expires_at=datetime.now(UTC),
        )
        mock_magic_link_service.validate_token.return_value = token
        mock_representation_repository.get.return_value = Representation(
            id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent"
        )
        mock_property_repository.get.return_value = Property(id="prop-1", address_line1="123 Main St")
        mock_rate_limiter.is_allowed.return_value = True

        subject.post(
            "/magic/abc-uuid/session",
            headers={"X-Forwarded-For": "203.0.113.42"},
        )

        mock_rate_limiter.is_allowed.assert_called_once_with("magic_session:203.0.113.42")

    def test_create_session_falls_back_to_client_host_when_no_forwarded_for(
        self,
        subject,
        mock_magic_link_service,
        mock_representation_repository,
        mock_property_repository,
        mock_rate_limiter,
    ):
        token = MagicLinkToken(
            id="tok-1",
            representation_id="rep-1",
            token="abc-uuid",
            expires_at=datetime.now(UTC),
        )
        mock_magic_link_service.validate_token.return_value = token
        mock_representation_repository.get.return_value = Representation(
            id="rep-1", property_id="prop-1", brokerage_id="brk-1", role="listing_agent"
        )
        mock_property_repository.get.return_value = Property(id="prop-1", address_line1="123 Main St")
        mock_rate_limiter.is_allowed.return_value = True

        subject.post("/magic/abc-uuid/session")

        call_args = mock_rate_limiter.is_allowed.call_args[0][0]
        assert call_args.startswith("magic_session:")
        assert call_args != "magic_session:203.0.113.42"

    def test_create_session_returns_429_when_rate_limited(self, subject, mock_rate_limiter):
        mock_rate_limiter.is_allowed.return_value = False

        response = subject.post("/magic/any-token/session")

        assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS

    def test_create_session_returns_401_for_invalid_token(self, subject, mock_magic_link_service, mock_rate_limiter):
        mock_rate_limiter.is_allowed.return_value = True
        mock_magic_link_service.validate_token.side_effect = InvalidMagicLinkError("invalid")

        response = subject.post("/magic/bad-token/session")

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @pytest.fixture
    def mock_current_user(self):
        return User(id="user-123", email="test@test.com", role="agent", brokerage_id="brokerage-123")

    @pytest.fixture
    def mock_magic_link_service(self):
        return MagicMock(spec=MagicLinkService)

    @pytest.fixture
    def mock_representation_repository(self):
        return MagicMock(spec=RepresentationRepository)

    @pytest.fixture
    def mock_property_repository(self):
        return MagicMock(spec=PropertyRepository)

    @pytest.fixture
    def mock_rate_limiter(self):
        return MagicMock(spec=RateLimiter)

    @pytest.fixture
    def subject(
        self,
        test_container,
        mock_current_user,
        mock_magic_link_service,
        mock_representation_repository,
        mock_property_repository,
        mock_rate_limiter,
    ):
        with test_container.override_providers(
            magic_link_service=mock_magic_link_service,
            representation_repository=mock_representation_repository,
            property_repository=mock_property_repository,
            rate_limiter=mock_rate_limiter,
        ):
            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[get_current_user] = lambda: mock_current_user
            yield TestClient(app)
            app.dependency_overrides.clear()
