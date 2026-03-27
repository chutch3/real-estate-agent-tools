import os
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import pytest
from backend.container import Container
from backend.main import create_app
from backend.models import (
    AgentInfo,
    DocumentInfo,
    GeocodeLocation,
    GeocodeRequest,
    GeocodeResponse,
    PostGenerationRequest,
    PropertyInfo,
    TemplateResponse,
)
from backend.schema import create_document_embeddings_schema, drop_document_embeddings_schema
from backend.template_loader import TEMPLATE_DIR
from fastapi.testclient import TestClient
from pymilvus import MilvusClient
from pymilvus.exceptions import MilvusException
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Response as WerkzeugResponse

MILVUS_URI = "http://localhost:19530"


class TestApp:
    def test_health_check(self, subject):
        response = subject.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_generate_post(self, subject, httpserver: HTTPServer):
        httpserver.expect_request("/properties").respond_with_json([
            {
                "id": "prop-1",
                "formattedAddress": "1600 Amphitheatre Pkwy, Mountain View, CA 94043",
                "addressLine1": "1600 Amphitheatre Pkwy",
                "city": "Mountain View",
                "state": "CA",
                "zipCode": "94043",
                "latitude": 37.4225103,
                "longitude": -122.0847089,
            }
        ])
        httpserver.expect_request("/v1/embeddings").respond_with_json({
            "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
            "model": "text-embedding-ada-002",
            "object": "list",
            "usage": {"prompt_tokens": 5, "total_tokens": 5},
        })
        httpserver.expect_request("/v1/chat/completions").respond_with_json({
            "choices": [{"message": {"content": "John Doe from John Doe Real Estate — Mountain View, CA. Contact: john.doe@example.com", "role": "assistant"}}],
            "model": "gpt-4",
            "object": "chat.completion",
        })

        response = subject.post(
            "/api/posts",
            json=PostGenerationRequest(
                address="1600 Amphitheatre Parkway Mountain View, CA 94043, USA",
                agent_info=AgentInfo(
                    agent_name="John Doe",
                    agent_company="John Doe Real Estate",
                    agent_contact="john.doe@example.com",
                ),
            ).model_dump(),
        )
        assert response.status_code == HTTPStatus.CREATED
        response_json = response.json()
        assert "post" in response_json
        assert "John Doe" in response_json["post"]
        assert "John Doe Real Estate" in response_json["post"]
        assert "john.doe@example.com" in response_json["post"]
        assert "Mountain View, CA" in response_json["post"]

    def test_geocode(self, subject, httpserver: HTTPServer):
        httpserver.expect_request("/maps/api/geocode/json").respond_with_json({
            "results": [
                {"geometry": {"location": {"lat": 37.4225103, "lng": -122.0847089}}}
            ]
        })

        response = subject.post(
            "/api/geocode",
            json=GeocodeRequest(
                address="1600 Amphitheatre Parkway Mountain View, CA 94043, USA"
            ).model_dump(),
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == GeocodeResponse(
            location=GeocodeLocation(lat=37.4225103, lng=-122.0847089)
        ).model_dump()

    def test_get_default_template(self, subject):
        response = subject.get("/api/templates/default")
        assert response.status_code == HTTPStatus.OK
        with open(f"{TEMPLATE_DIR}/post_prompt.txt", "r") as file:
            assert response.json() == TemplateResponse(template=file.read()).model_dump()

    @pytest.mark.parametrize(
        "origin,expected_allow_origin,expected_status_code,expected_response",
        [
            ("http://localhost:3001", "http://localhost:3001", 200, "OK"),
            ("http://localhost", "http://localhost", 200, "OK"),
            ("http://localhost.tiangolo.com", None, 400, "Disallowed CORS origin"),
        ],
    )
    def test_cors(
        self,
        subject,
        origin,
        expected_allow_origin,
        expected_status_code,
        expected_response,
    ):
        response = subject.options(
            "/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code == expected_status_code
        assert (
            response.headers.get("Access-Control-Allow-Origin") == expected_allow_origin
        )
        assert all(
            method in response.headers["Access-Control-Allow-Methods"]
            for method in ["DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"]
        )
        assert response.text == expected_response

    def test_list_properties_returns_empty_when_no_properties(self, subject):
        response = subject.get("/api/properties/list")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == []

    def test_create_and_list_properties(self, subject, httpserver: HTTPServer):
        httpserver.expect_request("/v1/embeddings").respond_with_json({
            "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
            "model": "text-embedding-ada-002",
            "object": "list",
            "usage": {"prompt_tokens": 5, "total_tokens": 5},
        })

        upload_response = subject.post(
            "/api/documents",
            files={"file": open("tests/integration/fixtures/mls_sheet.pdf", "rb")},
        )
        assert upload_response.status_code == HTTPStatus.CREATED
        doc_id = upload_response.json().get("id")

        property_data = PropertyInfo(
            rentcast_id="some-rentcast-id",
            latitude=37.4225103,
            longitude=-122.0847089,
            documents_ids=[doc_id],
        )
        create_response = subject.post(
            "/api/properties",
            json=property_data.model_dump(),
        )
        assert create_response.status_code == HTTPStatus.CREATED
        created_id = create_response.json().get("id")
        assert created_id is not None

        list_response = subject.get("/api/properties/list")
        assert list_response.status_code == HTTPStatus.OK
        properties = list_response.json()
        assert len(properties) == 1
        assert properties[0]["id"] == created_id

    def test_upload_and_retrieve_pdf(self, subject, httpserver: HTTPServer):
        httpserver.expect_request("/v1/embeddings").respond_with_json({
            "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
            "model": "text-embedding-ada-002",
            "object": "list",
            "usage": {"prompt_tokens": 5, "total_tokens": 5},
        })

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

    def test_delete_document_from_property(self, subject, httpserver: HTTPServer):
        httpserver.expect_request("/v1/embeddings").respond_with_json({
            "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
            "model": "text-embedding-ada-002",
            "object": "list",
            "usage": {"prompt_tokens": 5, "total_tokens": 5},
        })

        upload_response = subject.post(
            "/api/documents",
            files={"file": open("tests/integration/fixtures/mls_sheet.pdf", "rb")},
        )
        assert upload_response.status_code == HTTPStatus.CREATED
        doc_id = upload_response.json()["id"]

        property_data = PropertyInfo(
            latitude=37.4225103,
            longitude=-122.0847089,
            documents=[DocumentInfo(id=doc_id, filename="mls_sheet.pdf")],
        )
        create_response = subject.post("/api/properties", json=property_data.model_dump())
        assert create_response.status_code == HTTPStatus.CREATED
        property_id = create_response.json()["id"]

        delete_response = subject.delete(f"/api/properties/{property_id}/documents/{doc_id}")
        assert delete_response.status_code == HTTPStatus.OK
        assert delete_response.json()["documents"] == []

        retrieve_after_delete = subject.get(f"/api/documents/{doc_id}")
        assert retrieve_after_delete.status_code == HTTPStatus.NOT_FOUND

    def test_delete_document_returns_404_when_doc_not_in_property(self, subject):
        property_data = PropertyInfo(latitude=37.4225103, longitude=-122.0847089)
        create_response = subject.post("/api/properties", json=property_data.model_dump())
        assert create_response.status_code == HTTPStatus.CREATED
        property_id = create_response.json()["id"]

        response = subject.delete(f"/api/properties/{property_id}/documents/nonexistent-doc")
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_upload_pdf(self, subject, httpserver: HTTPServer, milvus_client, test_container: Container):
        httpserver.expect_request("/v1/embeddings").respond_with_json({
            "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
            "model": "text-embedding-ada-002",
            "object": "list",
            "usage": {"prompt_tokens": 5, "total_tokens": 5},
        })

        response = subject.post(
            "/api/documents",
            files={"file": open("tests/integration/fixtures/mls_sheet.pdf", "rb")},
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json().get("id") is not None
        collection_name = test_container.embeddings_collection_name()
        assert milvus_client.has_collection(collection_name)
        actual = milvus_client.query(
            collection_name=collection_name, filter=f'doc_id == "{response.json().get("id")}"'
        )
        assert len(actual) == 12
        assert any(
            "Buyers Brokers Only, LLC \n| \nExclusive Buyer Agents - MA & NH \n| Tel: 617.501.0233"
            in chunk.get("text") for chunk in actual
        )
        assert actual[0].get("embedding") is not None

    def test_chat_with_property(self, subject, httpserver: HTTPServer):
        httpserver.expect_request("/v1/embeddings").respond_with_json({
            "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
            "model": "text-embedding-ada-002",
            "object": "list",
            "usage": {"prompt_tokens": 5, "total_tokens": 5},
        })
        sse_body = (
            'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"This property is located in Mountain View"},"finish_reason":null}]}\n\n'
            "data: [DONE]\n\n"
        )
        httpserver.expect_request("/v1/chat/completions").respond_with_data(
            sse_body, content_type="text/event-stream"
        )

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
        httpserver.expect_request("/v1/embeddings").respond_with_json({
            "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
            "model": "text-embedding-ada-002",
            "object": "list",
            "usage": {"prompt_tokens": 5, "total_tokens": 5},
        })

        upload_response = subject.post(
            "/api/documents",
            files={"file": open("tests/integration/fixtures/mls_sheet.pdf", "rb")},
        )
        doc_id = upload_response.json()["id"]

        property_data = PropertyInfo(
            latitude=37.4225103,
            longitude=-122.0847089,
            documents=[DocumentInfo(id=doc_id, filename="mls_sheet.pdf")]
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
        httpserver.expect_request("/v1/embeddings").respond_with_json({
            "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
            "model": "text-embedding-ada-002",
            "object": "list",
            "usage": {"prompt_tokens": 5, "total_tokens": 5},
        })

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
        }
        with patch.dict(os.environ, env_overrides):
            with TestClient(create_app(test_container)) as client:
                yield client
        drop_document_embeddings_schema()
