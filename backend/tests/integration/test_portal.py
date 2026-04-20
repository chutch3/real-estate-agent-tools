from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from backend.container import Container
from backend.models import Brokerage, Property, Representation, User


class TestPortal:
    def test_generate_access_code_returns_code_and_portal_url(self, subject, representation_id):
        response = subject.post(f"/api/representations/{representation_id}/access-code")

        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert "code" in body
        assert "portal_url" in body
        assert len(body["code"]) == 8

    def test_generate_access_code_requires_authentication(self, subject, representation_id):
        subject.cookies.clear()

        response = subject.post(f"/api/representations/{representation_id}/access-code")

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_get_portal_info_returns_url_and_code_status(self, subject, representation_id):
        response = subject.get(f"/api/representations/{representation_id}/portal")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert "portal_url" in body
        assert "has_active_code" in body
        assert body["has_active_code"] is False

    def test_get_portal_info_reflects_active_code(self, subject, representation_id):
        subject.post(f"/api/representations/{representation_id}/access-code")

        response = subject.get(f"/api/representations/{representation_id}/portal")

        assert response.json()["has_active_code"] is True

    def test_consumer_session_created_with_valid_portal_token_and_code(
        self, subject, representation_id, consumer_client
    ):
        code = subject.post(f"/api/representations/{representation_id}/access-code").json()["code"]
        portal_token = (
            subject.get(f"/api/representations/{representation_id}/portal").json()["portal_url"].split("/")[-1]
        )

        response = consumer_client.post(f"/api/portal/{portal_token}/session", json={"code": code})

        assert response.status_code == HTTPStatus.OK
        assert "consumer_token" in response.cookies
        body = response.json()
        assert body["representation_id"] == representation_id
        assert body["role"] == "listing_agent"
        assert "property_address" in body

    def test_consumer_session_rejected_with_wrong_code(self, subject, representation_id, consumer_client):
        subject.post(f"/api/representations/{representation_id}/access-code")
        portal_token = (
            subject.get(f"/api/representations/{representation_id}/portal").json()["portal_url"].split("/")[-1]
        )

        response = consumer_client.post(f"/api/portal/{portal_token}/session", json={"code": "wrongcode"})

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_consumer_session_rejected_with_invalid_portal_token(self, consumer_client):
        response = consumer_client.post("/api/portal/not-a-real-token/session", json={"code": "123456"})

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_consumer_session_rejected_with_no_active_code(self, subject, representation_id, consumer_client):
        portal_token = (
            subject.get(f"/api/representations/{representation_id}/portal").json()["portal_url"].split("/")[-1]
        )

        response = consumer_client.post(f"/api/portal/{portal_token}/session", json={"code": "anycode"})

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_rotating_code_invalidates_previous(self, subject, representation_id, consumer_client):
        old_code = subject.post(f"/api/representations/{representation_id}/access-code").json()["code"]
        portal_token = (
            subject.get(f"/api/representations/{representation_id}/portal").json()["portal_url"].split("/")[-1]
        )
        subject.post(f"/api/representations/{representation_id}/access-code")

        response = consumer_client.post(f"/api/portal/{portal_token}/session", json={"code": old_code})

        assert response.status_code == HTTPStatus.UNAUTHORIZED

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

    @pytest.fixture
    def consumer_client(self, lightweight_client: TestClient) -> TestClient:
        """A separate client instance without agent auth cookies."""
        return TestClient(lightweight_client.app)
