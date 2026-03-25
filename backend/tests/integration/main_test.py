import os
from http import HTTPStatus
from unittest.mock import patch

import pytest
from backend.container import Container
from backend.main import create_app
from backend.models import (
    AgentInfo,
    GeocodeLocation,
    GeocodeRequest,
    GeocodeResponse,
    PostGenerationRequest,
    PropertyInfo,
    TemplateResponse,
)
from backend.schema import drop_document_embeddings_schema
from backend.template_loader import TEMPLATE_DIR
from fastapi.testclient import TestClient
from pymilvus import MilvusClient
from pytest_httpserver import HTTPServer

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
        httpserver.expect_request("/embeddings").respond_with_json({
            "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
            "model": "text-embedding-ada-002",
            "object": "list",
            "usage": {"prompt_tokens": 5, "total_tokens": 5},
        })
        httpserver.expect_request("/chat/completions").respond_with_json({
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
        httpserver.expect_request("/embeddings").respond_with_json({
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

    def test_upload_pdf(self, subject, httpserver: HTTPServer, milvus_client):
        httpserver.expect_request("/embeddings").respond_with_json({
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
        assert milvus_client.has_collection("document_embeddings")
        actual = milvus_client.query(
            collection_name="document_embeddings", ids=response.json().get("id")
        )
        assert len(actual) == 1
        assert (
            "Buyers Brokers Only, LLC \n| \nExclusive Buyer Agents - MA & NH \n| Tel: 617.501.0233"
            in actual[0].get("text")
        )
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
            "OPENAI_BASE_URL": base_url,
            "OPENAI_MODEL": "gpt-4",
            "RENTCAST_API_KEY": "fake-key",
            "RENTCAST_BASE_URL": base_url,
            "GOOGLE_MAPS_API_KEY": "fake-key",
            "GOOGLE_MAPS_BASE_URL": base_url,
        }
        with patch.dict(os.environ, env_overrides):
            yield TestClient(create_app(test_container))
        drop_document_embeddings_schema()
