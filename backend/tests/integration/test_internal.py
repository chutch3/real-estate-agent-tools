import os
from http import HTTPStatus
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pytest_httpserver import HTTPServer
from sqlmodel import select

from backend.container import Container
from backend.main import create_app
from backend.models import PropertyInfo, PropertyTaxCache
from backend.schema import drop_document_embeddings_schema
from tests.integration.conftest import make_jwt, seed_brokerage_and_user

MILVUS_URI = "http://localhost:19530"


class TestInternal:
    def test_get_internal_counties_returns_distinct_fips(self, subject, httpserver: HTTPServer):
        httpserver.expect_request(
            "/geocoder/geographies/coordinates",
        ).respond_with_json(
            {"result": {"geographies": {"Counties": [{"GEOID": "21111", "NAME": "Jefferson", "STATE": "21"}]}}}
        )
        httpserver.expect_request(
            "/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query",
        ).respond_with_json(
            {
                "features": [
                    {
                        "geometry": {
                            "rings": [
                                [
                                    [-86.035, 37.997],
                                    [-85.404, 37.997],
                                    [-85.404, 38.375],
                                    [-86.035, 38.375],
                                    [-86.035, 37.997],
                                ]
                            ],
                            "spatialReference": {"wkid": 4326},
                        }
                    }
                ]
            }
        )

        for _ in range(2):
            subject.post(
                "/api/properties",
                json=PropertyInfo(latitude=38.254, longitude=-85.759).model_dump(),
            )

        response = subject.get("/api/internal/counties")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["county_fips"] == ["21111"]

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


def test_upsert_tax_cache_persists_records(lightweight_client: TestClient, test_container: Container):
    response = lightweight_client.post(
        "/api/internal/tax-cache",
        json={
            "records": [
                {"state_parcel_id": "102403200259000013", "net_tax_amount": 6480.00},
                {"state_parcel_id": "102403200259000014", "net_tax_amount": 1200.00},
            ],
            "county_fips": "18019",
            "tax_year": 2023,
        },
    )

    assert response.status_code == HTTPStatus.NO_CONTENT

    with test_container.db().session() as session:
        rows = session.exec(select(PropertyTaxCache)).all()
    assert len(rows) == 2
    row_by_id = {r.state_parcel_id: r for r in rows}
    assert row_by_id["102403200259000013"].net_tax_amount == pytest.approx(6480.00)
    assert row_by_id["102403200259000013"].county_fips == "18019"
    assert row_by_id["102403200259000013"].tax_year == 2023
    assert row_by_id["102403200259000014"].net_tax_amount == pytest.approx(1200.00)


def test_upsert_tax_cache_updates_existing_record(lightweight_client: TestClient, test_container: Container):
    lightweight_client.post(
        "/api/internal/tax-cache",
        json={
            "records": [{"state_parcel_id": "102403200259000013", "net_tax_amount": 6480.00}],
            "county_fips": "18019",
            "tax_year": 2023,
        },
    )

    response = lightweight_client.post(
        "/api/internal/tax-cache",
        json={
            "records": [{"state_parcel_id": "102403200259000013", "net_tax_amount": 7200.00}],
            "county_fips": "18019",
            "tax_year": 2023,
        },
    )

    assert response.status_code == HTTPStatus.NO_CONTENT
    with test_container.db().session() as session:
        rows = session.exec(select(PropertyTaxCache)).all()
    assert len(rows) == 1
    assert rows[0].net_tax_amount == pytest.approx(7200.00)
