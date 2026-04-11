import os
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pymilvus.exceptions import MilvusException
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Response as WerkzeugResponse

from backend.container import Container
from backend.main import create_app
from backend.models import DocumentInfo, PropertyInfo
from backend.schema import drop_document_embeddings_schema
from tests.integration.conftest import make_jwt, seed_brokerage_and_user

MILVUS_URI = "http://localhost:19530"


class TestChat:
    def test_chat_with_property(self, subject, httpserver: HTTPServer):
        httpserver.expect_request("/v1/embeddings").respond_with_json(
            {
                "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
                "model": "text-embedding-ada-002",
                "object": "list",
                "usage": {"prompt_tokens": 5, "total_tokens": 5},
            }
        )
        sse_body = (
            'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"This property is located in Mountain View"},"finish_reason":null}]}\n\n'
            "data: [DONE]\n\n"
        )
        httpserver.expect_request("/v1/chat/completions").respond_with_data(sse_body, content_type="text/event-stream")

        property_data = PropertyInfo(
            latitude=37.4225103,
            longitude=-122.0847089,
        )
        create_response = subject.post("/api/properties", json=property_data.model_dump())
        assert create_response.status_code == HTTPStatus.CREATED
        property_id = create_response.json()["id"]

        chat_response = subject.post(
            f"/api/properties/{property_id}/chat",
            json={"message": "Tell me about this property"},
        )
        assert chat_response.status_code == HTTPStatus.OK
        assert "Mountain View" in chat_response.text

        history_response = subject.get(f"/api/properties/{property_id}/chat")
        assert history_response.status_code == HTTPStatus.OK
        messages = history_response.json()
        assert len(messages) == 2
        user_msg = next(m for m in messages if m["role"] == "user")
        assistant_msg = next(m for m in messages if m["role"] == "assistant")
        assert user_msg["content"] == "Tell me about this property"
        assert "Mountain View" in assistant_msg["content"]

    def test_chat_with_document_context(self, subject, httpserver: HTTPServer):
        httpserver.expect_request("/v1/embeddings").respond_with_json(
            {
                "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
                "model": "text-embedding-ada-002",
                "object": "list",
                "usage": {"prompt_tokens": 5, "total_tokens": 5},
            }
        )

        upload_response = subject.post(
            "/api/documents",
            files={"file": open("tests/integration/fixtures/mls_sheet.pdf", "rb")},
        )
        doc_id = upload_response.json()["id"]

        property_data = PropertyInfo(
            latitude=37.4225103,
            longitude=-122.0847089,
            documents=[DocumentInfo(id=doc_id, filename="mls_sheet.pdf")],
        )
        create_response = subject.post("/api/properties", json=property_data.model_dump())
        property_id = create_response.json()["id"]

        captured = {}
        sse_body = (
            'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"I see the MLS sheet"},"finish_reason":null}]}\n\n'
            "data: [DONE]\n\n"
        )

        def capture_and_respond(request):
            captured["body"] = request.get_json()
            return WerkzeugResponse(sse_body, content_type="text/event-stream")

        httpserver.expect_request("/v1/chat/completions").respond_with_handler(capture_and_respond)

        chat_response = subject.post(
            f"/api/properties/{property_id}/chat",
            json={"message": "What does the MLS sheet say?"},
        )

        assert chat_response.status_code == HTTPStatus.OK
        messages = captured["body"]["messages"]
        system_message = next(m for m in messages if m["role"] == "system")
        assert "Buyers Brokers Only, LLC" in system_message["content"]

    def test_chat_returns_503_when_milvus_unavailable(self, subject, httpserver: HTTPServer, test_container: Container):
        httpserver.expect_request("/v1/embeddings").respond_with_json(
            {
                "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
                "model": "text-embedding-ada-002",
                "object": "list",
                "usage": {"prompt_tokens": 5, "total_tokens": 5},
            }
        )

        property_data = PropertyInfo(latitude=37.4225103, longitude=-122.0847089)
        create_response = subject.post("/api/properties", json=property_data.model_dump())
        property_id = create_response.json()["id"]

        with patch.object(
            test_container.document_embedding_repository(),
            "query_embeddings",
            new=AsyncMock(side_effect=MilvusException("unavailable")),
        ):
            response = subject.post(
                f"/api/properties/{property_id}/chat",
                json={"message": "Tell me about this property"},
            )

        assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE

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
