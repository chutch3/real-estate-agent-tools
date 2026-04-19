import os
from http import HTTPStatus
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pymilvus import MilvusClient
from pytest_httpserver import HTTPServer
from sqlmodel import select

from backend.container import Container
from backend.main import create_app
from backend.models import Brokerage, Document, Property, Representation
from backend.schema import drop_document_embeddings_schema
from tests.integration.conftest import make_jwt, seed_brokerage_and_user

MILVUS_URI = "http://localhost:19530"
_MOTO_URL = "http://localhost:5005"
_S3_BUCKET = "test-documents"


class TestDocuments:
    def test_upload_and_retrieve_pdf(self, docker_subject, httpserver: HTTPServer):
        httpserver.expect_request("/v1/embeddings").respond_with_json(
            {
                "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
                "model": "text-embedding-ada-002",
                "object": "list",
                "usage": {"prompt_tokens": 5, "total_tokens": 5},
            }
        )
        with open("tests/integration/fixtures/mls_sheet.pdf", "rb") as f:
            original_bytes = f.read()
        upload_response = docker_subject.post(
            "/api/documents",
            files={"file": ("mls_sheet.pdf", original_bytes, "application/pdf")},
        )
        assert upload_response.status_code == HTTPStatus.CREATED
        doc_id = upload_response.json()["id"]
        retrieve_response = docker_subject.get(f"/api/documents/{doc_id}")
        assert retrieve_response.status_code == HTTPStatus.OK
        assert retrieve_response.headers["content-type"] == "application/pdf"
        assert retrieve_response.content == original_bytes

    def test_retrieve_pdf_returns_404_for_unknown_id(self, docker_subject):
        response = docker_subject.get("/api/documents/nonexistent-id")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_upload_pdf_stores_embeddings(
        self, docker_subject, httpserver: HTTPServer, milvus_client, test_container: Container
    ):
        httpserver.expect_request("/v1/embeddings").respond_with_json(
            {
                "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
                "model": "text-embedding-ada-002",
                "object": "list",
                "usage": {"prompt_tokens": 5, "total_tokens": 5},
            }
        )
        response = docker_subject.post(
            "/api/documents",
            files={"file": open("tests/integration/fixtures/mls_sheet.pdf", "rb")},
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json().get("id") is not None
        collection_name = test_container.embeddings_collection_name()
        assert milvus_client.has_collection(collection_name)
        actual = milvus_client.query(collection_name=collection_name, filter=f'doc_id == "{response.json().get("id")}"')
        assert len(actual) == 12
        assert any("Buyers Brokers Only, LLC" in chunk.get("text") for chunk in actual)
        assert actual[0].get("embedding") is not None

    def test_patch_visibility_sets_consumer_visible_true(self, subject, property_id, document_id):
        response = subject.patch(
            f"/api/properties/{property_id}/documents/{document_id}/visibility",
            json={"consumer_visible": True},
        )

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["id"] == document_id
        assert body["consumer_visible"] is True

    def test_patch_visibility_sets_consumer_visible_false(self, subject, property_id, document_id):
        response = subject.patch(
            f"/api/properties/{property_id}/documents/{document_id}/visibility",
            json={"consumer_visible": False},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json()["consumer_visible"] is False

    def test_patch_visibility_requires_authentication(self, subject, property_id, document_id):
        subject.cookies.clear()

        response = subject.patch(
            f"/api/properties/{property_id}/documents/{document_id}/visibility",
            json={"consumer_visible": True},
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_patch_visibility_rejected_for_document_from_different_property(
        self, subject: TestClient, property_id: str, test_container: Container
    ):
        with test_container.db().session() as session:
            brokerage = session.exec(select(Brokerage)).first()
            other_prop = Property(address_line1="999 Other St")
            session.add(other_prop)
            session.commit()
            session.refresh(other_prop)
            session.add(
                Representation(
                    property_id=other_prop.id,
                    brokerage_id=brokerage.id,
                    role="listing_agent",
                    status="active",
                )
            )
            other_doc = Document(property_id=other_prop.id, filename="other.pdf")
            session.add(other_doc)
            session.commit()
            session.refresh(other_doc)
            other_doc_id = other_doc.id

        response = subject.patch(
            f"/api/properties/{property_id}/documents/{other_doc_id}/visibility",
            json={"consumer_visible": True},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_property_list_includes_consumer_visible_on_documents(
        self, subject: TestClient, property_id: str, test_container: Container
    ):
        with test_container.db().session() as session:
            doc = Document(property_id=property_id, filename="report.pdf", consumer_visible=True)
            session.add(doc)
            session.commit()

        response = subject.get("/api/properties/list")

        assert response.status_code == HTTPStatus.OK
        matched = next((p for p in response.json() if p["id"] == property_id), None)
        assert matched is not None
        assert matched["documents"][0]["consumer_visible"] is True

    @pytest.fixture
    def milvus_client(self, docker_subject, test_container: Container) -> MilvusClient:
        yield test_container.milvus_client()

    @pytest.fixture
    def subject(self, lightweight_client: TestClient) -> TestClient:
        return lightweight_client

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
    def docker_subject(self, test_container: Container, tmp_path, httpserver: HTTPServer, integration_services):
        base_url = httpserver.url_for("").rstrip("/")
        env_overrides = {
            "DB_URI": f"sqlite:///{tmp_path}/test.db",
            "MILVUS_URI": MILVUS_URI,
            "OPENAI_API_KEY": "fake-key",
            "OPENAI_BASE_URL": f"{base_url}/v1",
            "OPENAI_MODEL": "gpt-4",
            "OPENAI_EMBEDDINGS_MODEL": "text-embedding-ada-002",
            "OPENAI_EMBEDDINGS_DIMENSION": "1536",
            "RENTCAST_API_KEY": "fake-key",
            "RENTCAST_BASE_URL": base_url,
            "GOOGLE_MAPS_API_KEY": "fake-key",
            "GOOGLE_MAPS_BASE_URL": base_url,
            "RAG_TOP_K": "5",
            "S3_BUCKET": "test-documents",
            "S3_ACCESS_KEY": "test",
            "S3_SECRET_KEY": "test",
            "S3_ENDPOINT_URL": "http://localhost:5005",
            "CENSUS_GEOCODER_BASE_URL": base_url,
            "TIGER_BASE_URL": base_url,
            "ARCGIS_PARCELS_BASE_URL": base_url,
            "ARCGIS_PARCELS_SUPPORTED_STATES": "IN",
            "JWT_SECRET_KEY": "test-secret",
        }
        with patch.dict(os.environ, env_overrides):
            with TestClient(create_app(test_container)) as client:
                brokerage_id, user_id = seed_brokerage_and_user(test_container.db())
                token = make_jwt(user_id, brokerage_id)
                client.cookies.set("access_token", token)
                yield client
        drop_document_embeddings_schema()
