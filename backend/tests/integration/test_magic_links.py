from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from backend.container import Container
from backend.models import Brokerage, Document, Property, Representation, User


class TestMagicLinkTokens:
    def test_create_magic_link_returns_token(self, subject, representation_id):
        response = subject.post(f"/api/representations/{representation_id}/magic-links")

        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert "token" in body
        assert "id" in body
        assert "expires_at" in body
        assert body["last_accessed_at"] is None

    def test_list_magic_links_returns_active_tokens(self, subject, representation_id):
        subject.post(f"/api/representations/{representation_id}/magic-links")
        subject.post(f"/api/representations/{representation_id}/magic-links")

        response = subject.get(f"/api/representations/{representation_id}/magic-links")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert len(body["tokens"]) == 2

    def test_revoke_magic_link_removes_it_from_list(self, subject, representation_id):
        create_response = subject.post(f"/api/representations/{representation_id}/magic-links")
        token_id = create_response.json()["id"]

        revoke_response = subject.delete(f"/api/representations/{representation_id}/magic-links/{token_id}")
        assert revoke_response.status_code == HTTPStatus.NO_CONTENT

        list_response = subject.get(f"/api/representations/{representation_id}/magic-links")
        assert list_response.status_code == HTTPStatus.OK
        assert list_response.json()["tokens"] == []

    def test_create_magic_link_requires_authentication(self, subject, representation_id):
        subject.cookies.clear()

        response = subject.post(f"/api/representations/{representation_id}/magic-links")

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @pytest.fixture
    def subject(self, lightweight_client: TestClient) -> TestClient:
        return lightweight_client

    @pytest.fixture
    def representation_id(self, lightweight_client: TestClient, test_container: Container) -> str:
        with test_container.db().session() as session:
            brokerage = session.exec(select(Brokerage)).first()
            prop = Property(address_line1="123 Main St", city="Louisville", state="KY", zip_code="40202")
            session.add(prop)
            session.commit()
            session.refresh(prop)
            rep = Representation(
                property_id=prop.id,
                brokerage_id=brokerage.id,
                role="listing_agent",
                status="active",
            )
            session.add(rep)
            session.commit()
            session.refresh(rep)
            return rep.id


class TestConsumerSession:
    def test_post_session_sets_consumer_cookie(self, subject, magic_token):
        response = subject.post(f"/api/magic/{magic_token}/session")

        assert response.status_code == HTTPStatus.OK
        assert "consumer_token" in response.cookies

    def test_post_session_returns_representation_info(self, subject, magic_token, representation_id):
        response = subject.post(f"/api/magic/{magic_token}/session")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["representation_id"] == representation_id
        assert body["role"] == "listing_agent"
        assert "property_address" in body

    def test_post_session_with_invalid_token_returns_401(self, subject):
        response = subject.post("/api/magic/not-a-real-token/session")

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_get_consumer_property_requires_consumer_session(self, subject):
        response = subject.get("/api/consumer/property")

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_get_consumer_property_returns_property_details(self, subject, magic_token):
        subject.post(f"/api/magic/{magic_token}/session")

        response = subject.get("/api/consumer/property")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert "address_line1" in body
        assert "role" in body
        assert "agent_name" in body
        assert "agent_email" in body

    def test_get_consumer_net_sheet_allowed_for_listing_agent(self, subject, magic_token):
        subject.post(f"/api/magic/{magic_token}/session")

        response = subject.get("/api/consumer/net-sheet")

        assert response.status_code == HTTPStatus.OK

    def test_get_consumer_net_sheet_forbidden_for_buyers_agent(self, subject, buyers_magic_token):
        subject.post(f"/api/magic/{buyers_magic_token}/session")

        response = subject.get("/api/consumer/net-sheet")

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get_consumer_documents_returns_only_visible_documents(
        self, subject, magic_token, property_id, test_container: Container
    ):
        with test_container.db().session() as session:
            doc_visible = Document(property_id=property_id, filename="visible.pdf", consumer_visible=True)
            doc_hidden = Document(property_id=property_id, filename="hidden.pdf", consumer_visible=False)
            session.add(doc_visible)
            session.add(doc_hidden)
            session.commit()

        subject.post(f"/api/magic/{magic_token}/session")

        response = subject.get("/api/consumer/documents")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        filenames = [d["filename"] for d in body["documents"]]
        assert "visible.pdf" in filenames
        assert "hidden.pdf" not in filenames

    @pytest.fixture
    def buyers_magic_token(self, subject: TestClient, test_container: Container) -> str:
        with test_container.db().session() as session:
            brokerage = session.exec(select(Brokerage)).first()
            user = session.exec(select(User)).first()
            prop = Property(address_line1="456 Buyer St")
            session.add(prop)
            session.commit()
            session.refresh(prop)
            rep = Representation(
                property_id=prop.id,
                brokerage_id=brokerage.id,
                user_id=user.id,
                role="buyers_agent",
                status="active",
            )
            session.add(rep)
            session.commit()
            session.refresh(rep)
            buyers_rep_id = rep.id

        create_response = subject.post(f"/api/representations/{buyers_rep_id}/magic-links")
        return create_response.json()["token"]

    @pytest.fixture
    def magic_token(self, subject: TestClient, representation_id: str) -> str:
        response = subject.post(f"/api/representations/{representation_id}/magic-links")
        return response.json()["token"]

    @pytest.fixture
    def property_id(self, test_container: Container, representation_id: str) -> str:
        with test_container.db().session() as session:
            rep = session.get(Representation, representation_id)
            return rep.property_id

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


class TestDocumentVisibility:
    def test_patch_visibility_sets_consumer_visible_true(self, subject, property_id, document_id):
        response = subject.patch(
            f"/api/properties/{property_id}/documents/{document_id}/visibility",
            json={"consumer_visible": True},
        )

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["consumer_visible"] is True

    def test_patch_visibility_sets_consumer_visible_false(self, subject, property_id, document_id):
        response = subject.patch(
            f"/api/properties/{property_id}/documents/{document_id}/visibility",
            json={"consumer_visible": False},
        )

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["consumer_visible"] is False

    def test_patch_visibility_requires_authentication(self, subject, property_id, document_id):
        subject.cookies.clear()

        response = subject.patch(
            f"/api/properties/{property_id}/documents/{document_id}/visibility",
            json={"consumer_visible": True},
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @pytest.fixture
    def document_id(self, test_container: Container, property_id: str) -> str:
        with test_container.db().session() as session:
            doc = Document(property_id=property_id, filename="test.pdf")
            session.add(doc)
            session.commit()
            session.refresh(doc)
            return doc.id

    @pytest.fixture
    def property_id(self, test_container: Container, lightweight_client: TestClient) -> str:
        with test_container.db().session() as session:
            brokerage = session.exec(select(Brokerage)).first()
            prop = Property(address_line1="789 Test Ave")
            session.add(prop)
            session.commit()
            session.refresh(prop)
            rep = Representation(
                property_id=prop.id,
                brokerage_id=brokerage.id,
                role="listing_agent",
                status="active",
            )
            session.add(rep)
            session.commit()
            return prop.id

    @pytest.fixture
    def subject(self, lightweight_client: TestClient) -> TestClient:
        return lightweight_client
