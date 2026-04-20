from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.auth import get_current_user
from backend.exceptions import InvalidAccessError
from backend.models import Property, Representation, User
from backend.repositories.properties import PropertyRepository
from backend.routes.portal import router
from backend.services.access_code import AccessCodeService
from backend.services.rate_limiter import RateLimiter


class TestPortalRoutes:
    @pytest.fixture
    def mock_access_code_service(self):
        return MagicMock(spec=AccessCodeService)

    @pytest.fixture
    def mock_property_repository(self):
        return MagicMock(spec=PropertyRepository)

    @pytest.fixture
    def mock_rate_limiter(self):
        mock = MagicMock(spec=RateLimiter)
        mock.is_allowed.return_value = True
        return mock

    @pytest.fixture
    def current_user(self):
        return User(id="user-1", email="agent@test.com", brokerage_id="brk-1", role="AGENT", hashed_password="x")

    @pytest.fixture
    def subject(
        self,
        test_container,
        mock_access_code_service,
        mock_property_repository,
        mock_rate_limiter,
        current_user,
    ):
        with test_container.override_providers(
            access_code_service=mock_access_code_service,
            property_repository=mock_property_repository,
            rate_limiter=mock_rate_limiter,
        ):
            app = FastAPI()
            app.include_router(router)
            app.dependency_overrides[get_current_user] = lambda: current_user
            yield TestClient(app)
            app.dependency_overrides.clear()

    def test_generate_access_code_returns_code_and_portal_url(self, subject, mock_access_code_service):
        mock_access_code_service.generate.return_value = ("ABCD1234", "http://localhost:3001/portal/tok-abc")

        response = subject.post("/representations/rep-1/access-code")

        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert body["code"] == "ABCD1234"
        assert body["portal_url"] == "http://localhost:3001/portal/tok-abc"
        mock_access_code_service.generate.assert_called_once_with("rep-1", "brk-1")

    def test_generate_access_code_returns_404_when_representation_not_found(self, subject, mock_access_code_service):
        mock_access_code_service.generate.side_effect = InvalidAccessError("not found")

        response = subject.post("/representations/rep-missing/access-code")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_generate_access_code_returns_401_when_unauthenticated(self, subject):
        subject.app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(Exception("not auth"))

    def test_get_portal_info_returns_url_and_code_status(self, subject, mock_access_code_service):
        mock_access_code_service.has_active_code.return_value = (False, "http://localhost:3001/portal/tok-abc")

        response = subject.get("/representations/rep-1/portal")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["portal_url"] == "http://localhost:3001/portal/tok-abc"
        assert body["has_active_code"] is False
        mock_access_code_service.has_active_code.assert_called_once_with("rep-1", "brk-1")

    def test_get_portal_info_reflects_active_code(self, subject, mock_access_code_service):
        mock_access_code_service.has_active_code.return_value = (True, "http://localhost:3001/portal/tok-abc")

        response = subject.get("/representations/rep-1/portal")

        assert response.json()["has_active_code"] is True

    def test_get_portal_info_returns_404_when_representation_not_found(self, subject, mock_access_code_service):
        mock_access_code_service.has_active_code.side_effect = InvalidAccessError("not found")

        response = subject.get("/representations/rep-missing/portal")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_create_consumer_session_returns_session_and_sets_cookie(
        self, subject, mock_access_code_service, mock_property_repository
    ):
        rep = Representation(
            id="rep-1",
            property_id="prop-1",
            brokerage_id="brk-1",
            role="listing_agent",
            portal_token="tok-abc",
        )
        mock_access_code_service.validate.return_value = rep
        mock_property_repository.get.return_value = Property(
            id="prop-1", address_line1="123 Main St", city="Louisville", state="KY", zip_code="40202"
        )

        response = subject.post("/portal/tok-abc/session", json={"code": "ABCD1234"})

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["representation_id"] == "rep-1"
        assert body["role"] == "listing_agent"
        assert body["property_address"] == "123 Main St, Louisville, KY, 40202"
        assert "consumer_token" in response.cookies
        mock_access_code_service.validate.assert_called_once_with("tok-abc", "ABCD1234")

    def test_create_consumer_session_returns_401_when_invalid_code(self, subject, mock_access_code_service):
        mock_access_code_service.validate.side_effect = InvalidAccessError("invalid")

        response = subject.post("/portal/bad-token/session", json={"code": "WRONG"})

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_create_consumer_session_returns_429_when_rate_limited(self, subject, mock_rate_limiter):
        mock_rate_limiter.is_allowed.return_value = False

        response = subject.post("/portal/tok-abc/session", json={"code": "ABCD1234"})

        assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS
