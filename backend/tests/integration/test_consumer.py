from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from backend.container import Container
from backend.models import Brokerage, Document, Property, Representation, User


class TestConsumer:
    def test_get_property_returns_details(self, subject: TestClient):
        response = subject.get("/api/consumer/property")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["address_line1"] == "123 Main St"
        assert body["role"] == "listing_agent"
        assert "agent_name" in body
        assert "agent_email" in body

    def test_get_property_requires_consumer_session(self, subject: TestClient):
        subject.cookies.clear()

        response = subject.get("/api/consumer/property")

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_get_net_sheet_allowed_for_listing_agent(self, subject: TestClient):
        response = subject.get("/api/consumer/net-sheet")

        assert response.status_code == HTTPStatus.OK

    def test_get_net_sheet_forbidden_for_buyers_agent(self, lightweight_client: TestClient, test_container: Container):
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

        token = lightweight_client.post(f"/api/representations/{buyers_rep_id}/magic-links").json()["token"]
        lightweight_client.post(f"/api/magic/{token}/session")

        response = lightweight_client.get("/api/consumer/net-sheet")

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get_documents_returns_only_visible(self, subject: TestClient, property_id: str, test_container: Container):
        with test_container.db().session() as session:
            session.add(Document(property_id=property_id, filename="visible.pdf", consumer_visible=True))
            session.add(Document(property_id=property_id, filename="hidden.pdf", consumer_visible=False))
            session.commit()

        response = subject.get("/api/consumer/documents")

        assert response.status_code == HTTPStatus.OK
        filenames = [d["filename"] for d in response.json()["documents"]]
        assert "visible.pdf" in filenames
        assert "hidden.pdf" not in filenames

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
    def subject(self, lightweight_client: TestClient, representation_id: str) -> TestClient:
        token = lightweight_client.post(f"/api/representations/{representation_id}/magic-links").json()["token"]
        lightweight_client.post(f"/api/magic/{token}/session")
        return lightweight_client
