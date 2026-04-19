from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from backend.container import Container
from backend.models import Brokerage, Property, Representation, User


class TestMagicLinks:
    def test_create_returns_token(self, subject, representation_id):
        response = subject.post(f"/api/representations/{representation_id}/magic-links")

        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert "token" in body
        assert "id" in body
        assert "expires_at" in body
        assert body["last_accessed_at"] is None

    def test_create_requires_authentication(self, subject, representation_id):
        subject.cookies.clear()

        response = subject.post(f"/api/representations/{representation_id}/magic-links")

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_list_returns_active_tokens(self, subject, representation_id):
        subject.post(f"/api/representations/{representation_id}/magic-links")
        subject.post(f"/api/representations/{representation_id}/magic-links")

        response = subject.get(f"/api/representations/{representation_id}/magic-links")

        assert response.status_code == HTTPStatus.OK
        assert len(response.json()["tokens"]) == 2

    def test_list_excludes_revoked_tokens(self, subject, representation_id):
        token_id = subject.post(f"/api/representations/{representation_id}/magic-links").json()["id"]
        subject.delete(f"/api/representations/{representation_id}/magic-links/{token_id}")

        response = subject.get(f"/api/representations/{representation_id}/magic-links")

        assert response.status_code == HTTPStatus.OK
        assert response.json()["tokens"] == []

    def test_revoke_returns_no_content(self, subject, representation_id):
        token_id = subject.post(f"/api/representations/{representation_id}/magic-links").json()["id"]

        response = subject.delete(f"/api/representations/{representation_id}/magic-links/{token_id}")

        assert response.status_code == HTTPStatus.NO_CONTENT

    def test_session_sets_consumer_cookie(self, subject, magic_token):
        response = subject.post(f"/api/magic/{magic_token}/session")

        assert response.status_code == HTTPStatus.OK
        assert "consumer_token" in response.cookies

    def test_session_returns_representation_info(self, subject, magic_token, representation_id):
        response = subject.post(f"/api/magic/{magic_token}/session")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["representation_id"] == representation_id
        assert body["role"] == "listing_agent"
        assert "property_address" in body

    def test_session_rejects_invalid_token(self, subject):
        response = subject.post("/api/magic/not-a-real-token/session")

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @pytest.fixture
    def magic_token(self, subject: TestClient, representation_id: str) -> str:
        return subject.post(f"/api/representations/{representation_id}/magic-links").json()["token"]

    @pytest.fixture
    def representation_id(self, lightweight_client: TestClient, test_container: Container) -> str:
        with test_container.db().session() as session:
            brokerage = session.exec(select(Brokerage)).first()
            user = session.exec(select(User)).first()
            prop = Property(address_line1="123 Main St", city="Louisville", state="KY", zip_code="40202")
            session.add(prop)
            session.commit()
            session.refresh(prop)
            rep = Representation(
                property_id=prop.id,
                brokerage_id=brokerage.id,
                user_id=user.id,
                role="listing_agent",
                status="active",
            )
            session.add(rep)
            session.commit()
            session.refresh(rep)
            return rep.id

    @pytest.fixture
    def subject(self, lightweight_client: TestClient) -> TestClient:
        return lightweight_client
