from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import JWTError

from backend.models import Brokerage, User
from backend.repositories.brokerage import BrokerageRepository
from backend.repositories.user import UserRepository
from backend.routes.identity import router
from backend.services.security import SecurityService


class TestIdentityRoutes:
    def test_create_brokerage_returns_201(self, subject, mock_brokerage_repository):
        mock_brokerage_repository.create.return_value = Brokerage(
            id="brk-1", name="Acme Realty", contact_info="info@acme.com"
        )

        response = subject.post("/brokerages", json={"name": "Acme Realty", "contact_info": "info@acme.com"})

        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert body["id"] == "brk-1"
        assert body["name"] == "Acme Realty"
        mock_brokerage_repository.create.assert_called_once()

    def test_create_user_returns_201(self, subject, mock_user_repository, mock_security_service):
        mock_security_service.hash_password.return_value = "hashed-pw"
        mock_user_repository.create.return_value = User(
            id="usr-1", email="agent@example.com", role="agent", brokerage_id="brk-1"
        )

        response = subject.post(
            "/users",
            json={"email": "agent@example.com", "password": "secret", "role": "agent", "brokerage_id": "brk-1"},
        )

        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert body["id"] == "usr-1"
        assert body["email"] == "agent@example.com"
        mock_security_service.hash_password.assert_called_once_with("secret")

    def test_login_sets_access_token_cookie(self, subject, mock_user_repository, mock_security_service):
        mock_user_repository.get_by_email.return_value = User(
            id="usr-1", email="agent@example.com", hashed_password="hashed-pw", role="agent", brokerage_id="brk-1"
        )
        mock_security_service.verify_password.return_value = True
        mock_security_service.create_access_token.return_value = "jwt-token"

        response = subject.post("/auth/token", data={"username": "agent@example.com", "password": "secret"})

        assert response.status_code == HTTPStatus.OK
        assert "access_token" in response.cookies
        mock_security_service.create_access_token.assert_called_once_with(
            user_id="usr-1", brokerage_id="brk-1", role="agent"
        )

    def test_login_returns_401_for_unknown_email(self, subject, mock_user_repository):
        mock_user_repository.get_by_email.return_value = None

        response = subject.post("/auth/token", data={"username": "nobody@example.com", "password": "secret"})

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_login_returns_401_for_wrong_password(self, subject, mock_user_repository, mock_security_service):
        mock_user_repository.get_by_email.return_value = User(
            id="usr-1", email="agent@example.com", hashed_password="hashed-pw", role="agent", brokerage_id="brk-1"
        )
        mock_security_service.verify_password.return_value = False

        response = subject.post("/auth/token", data={"username": "agent@example.com", "password": "wrong"})

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_logout_clears_access_token_cookie(self, subject):
        subject.cookies.set("access_token", "some-token")

        response = subject.post("/auth/logout")

        assert response.status_code == HTTPStatus.OK
        assert response.cookies.get("access_token") is None

    def test_get_me_returns_user_and_brokerage(
        self, subject, mock_user_repository, mock_brokerage_repository, mock_security_service
    ):
        mock_security_service.decode_token.return_value = {"sub": "usr-1"}
        mock_user_repository.get_by_id.return_value = User(
            id="usr-1", email="agent@example.com", role="agent", brokerage_id="brk-1"
        )
        mock_brokerage_repository.get_by_id.return_value = Brokerage(id="brk-1", name="Acme Realty")
        subject.cookies.set("access_token", "valid-token")

        response = subject.get("/users/me")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["id"] == "usr-1"
        assert body["email"] == "agent@example.com"
        assert body["brokerage"]["id"] == "brk-1"
        mock_security_service.decode_token.assert_called_once_with("valid-token")

    def test_get_me_includes_user_name(
        self, subject, mock_user_repository, mock_brokerage_repository, mock_security_service
    ):
        mock_security_service.decode_token.return_value = {"sub": "usr-1"}
        mock_user_repository.get_by_id.return_value = User(
            id="usr-1", email="agent@example.com", role="agent", brokerage_id="brk-1", name="Jane Smith"
        )
        mock_brokerage_repository.get_by_id.return_value = Brokerage(id="brk-1", name="Acme Realty")
        subject.cookies.set("access_token", "valid-token")

        response = subject.get("/users/me")

        assert response.status_code == HTTPStatus.OK
        assert response.json()["name"] == "Jane Smith"

    def test_get_me_returns_401_when_no_cookie(self, subject):
        response = subject.get("/users/me")

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_get_me_returns_401_for_invalid_token(self, subject, mock_security_service):
        mock_security_service.decode_token.side_effect = JWTError("bad token")
        subject.cookies.set("access_token", "bad-token")

        response = subject.get("/users/me")

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_get_me_returns_401_when_user_not_found(self, subject, mock_security_service, mock_user_repository):
        mock_security_service.decode_token.return_value = {"sub": "missing-user"}
        mock_user_repository.get_by_id.return_value = None
        subject.cookies.set("access_token", "valid-token")

        response = subject.get("/users/me")

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @pytest.fixture
    def mock_brokerage_repository(self):
        return MagicMock(spec=BrokerageRepository)

    @pytest.fixture
    def mock_user_repository(self):
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def mock_security_service(self):
        return MagicMock(spec=SecurityService)

    @pytest.fixture
    def subject(self, test_container, mock_brokerage_repository, mock_user_repository, mock_security_service):
        with test_container.override_providers(
            brokerage_repository=mock_brokerage_repository,
            user_repository=mock_user_repository,
            security_service=mock_security_service,
        ):
            app = FastAPI()
            app.include_router(router)
            yield TestClient(app)
