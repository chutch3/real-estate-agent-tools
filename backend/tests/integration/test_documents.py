import os
from http import HTTPStatus
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pymilvus import MilvusClient
from pytest_httpserver import HTTPServer

from backend.container import Container
from backend.main import create_app
from backend.schema import drop_document_embeddings_schema
from tests.integration.conftest import make_jwt, seed_brokerage_and_user

MILVUS_URI = "http://localhost:19530"
_MOTO_URL = "http://localhost:5005"
_S3_BUCKET = "test-documents"


class TestDocuments:
    def test_upload_and_retrieve_pdf(self, subject, httpserver: HTTPServer):
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
        upload_response = subject.post(
            "/api/documents",
            files={"file": ("mls_sheet.pdf", original_bytes, "application/pdf")},
        )
        assert upload_response.status_code == HTTPStatus.CREATED
        doc_id = upload_response.json()["id"]
        retrieve_response = subject.get(f"/api/documents/{doc_id}")
        assert retrieve_response.status_code == HTTPStatus.OK
        assert retrieve_response.headers["content-type"] == "application/pdf"
        assert retrieve_response.content == original_bytes

    def test_retrieve_pdf_returns_404_for_unknown_id(self, subject):
        response = subject.get("/api/documents/nonexistent-id")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_upload_pdf_stores_embeddings(
        self, subject, httpserver: HTTPServer, milvus_client, test_container: Container
    ):
        httpserver.expect_request("/v1/embeddings").respond_with_json(
            {
                "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
                "model": "text-embedding-ada-002",
                "object": "list",
                "usage": {"prompt_tokens": 5, "total_tokens": 5},
            }
        )
        response = subject.post(
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

    @pytest.fixture
    def milvus_client(self, subject, test_container: Container) -> MilvusClient:
        yield test_container.milvus_client()

    @pytest.fixture
    def subject(self, test_container: Container, tmp_path, httpserver: HTTPServer, integration_services):
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
