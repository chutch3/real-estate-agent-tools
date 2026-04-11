import os
from http import HTTPStatus
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pytest_httpserver import HTTPServer

from backend.container import Container
from backend.main import create_app
from backend.models import AgentInfo, PostGenerationRequest
from backend.schema import drop_document_embeddings_schema
from tests.integration.conftest import make_jwt, seed_brokerage_and_user

MILVUS_URI = "http://localhost:19530"


class TestPosts:
    def test_generate_post(self, subject, httpserver: HTTPServer):
        httpserver.expect_request("/properties").respond_with_json(
            [
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
            ]
        )
        httpserver.expect_request("/v1/embeddings").respond_with_json(
            {
                "data": [{"embedding": [0.1] * 1536, "index": 0, "object": "embedding"}],
                "model": "text-embedding-ada-002",
                "object": "list",
                "usage": {"prompt_tokens": 5, "total_tokens": 5},
            }
        )
        httpserver.expect_request("/v1/chat/completions").respond_with_json(
            {
                "choices": [
                    {
                        "message": {
                            "content": "John Doe from John Doe Real Estate — Mountain View, CA. Contact: john.doe@example.com",
                            "role": "assistant",
                        }
                    }
                ],
                "model": "gpt-4",
                "object": "chat.completion",
            }
        )

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
