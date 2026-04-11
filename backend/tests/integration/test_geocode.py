import os
from http import HTTPStatus
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pytest_httpserver import HTTPServer

from backend.container import Container
from backend.main import create_app
from backend.models import GeocodeLocation, GeocodeRequest, GeocodeResponse
from backend.schema import drop_document_embeddings_schema
from tests.integration.conftest import make_jwt, seed_brokerage_and_user

MILVUS_URI = "http://localhost:19530"


class TestGeocode:
    def test_geocode(self, subject, httpserver: HTTPServer):
        httpserver.expect_request("/maps/api/geocode/json").respond_with_json(
            {"results": [{"geometry": {"location": {"lat": 37.4225103, "lng": -122.0847089}}}]}
        )

        response = subject.post(
            "/api/geocode",
            json=GeocodeRequest(address="1600 Amphitheatre Parkway Mountain View, CA 94043, USA").model_dump(),
        )
        assert response.status_code == HTTPStatus.CREATED
        assert (
            response.json() == GeocodeResponse(location=GeocodeLocation(lat=37.4225103, lng=-122.0847089)).model_dump()
        )

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
