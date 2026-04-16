import os
from http import HTTPStatus
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pytest_httpserver import HTTPServer
from sqlmodel import select

from backend.container import Container
from backend.main import create_app
from backend.models import Brokerage, DocumentInfo, PropertyInfo, User
from backend.schema import drop_document_embeddings_schema
from tests.integration.conftest import make_jwt, seed_brokerage_and_user

MILVUS_URI = "http://localhost:19530"
_MOTO_URL = "http://localhost:5005"
_S3_BUCKET = "test-documents"

_ARCGIS_PARCEL_RESPONSE = {
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-86.1590, 39.7690],
                        [-86.1580, 39.7690],
                        [-86.1580, 39.7680],
                        [-86.1590, 39.7680],
                        [-86.1590, 39.7690],
                    ]
                ],
            },
            "properties": {
                "nguid": "urn:emergency:uid:gis:PCL:test-parcel-nguid:test.in.gov",
                "state_parcel_id": "102403200259000013",
            },
        }
    ]
}


class TestProperties:
    def test_create_property_returns_parcel_polygon(self, subject, httpserver: HTTPServer):
        httpserver.expect_request("/query").respond_with_json(_ARCGIS_PARCEL_RESPONSE)
        property_data = PropertyInfo(rentcast_id="some-rentcast-id", latitude=39.7684, longitude=-86.1581, state="IN")
        response = subject.post("/api/properties", json=property_data.model_dump())
        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert body["parcel_polygon"] is not None
        assert body["parcel_polygon"]["type"] == "Polygon"

    def test_create_property_persists_state_parcel_id(self, subject, test_container: Container, httpserver: HTTPServer):
        httpserver.expect_request("/query").respond_with_json(_ARCGIS_PARCEL_RESPONSE)
        property_data = PropertyInfo(rentcast_id="some-rentcast-id", latitude=39.7684, longitude=-86.1581, state="IN")

        response = subject.post("/api/properties", json=property_data.model_dump())

        assert response.status_code == HTTPStatus.CREATED
        with test_container.db().session() as session:
            saved = session.exec(select(PropertyInfo).where(PropertyInfo.state == "IN")).first()
        assert saved is not None
        assert saved.state_parcel_id == "102403200259000013"

    def test_list_properties_returns_empty_when_no_properties(self, subject):
        response = subject.get("/api/properties/list")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == []

    def test_create_and_list_properties(self, subject, httpserver: HTTPServer):
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
        assert upload_response.status_code == HTTPStatus.CREATED
        doc_id = upload_response.json().get("id")
        property_data = PropertyInfo(
            rentcast_id="some-rentcast-id",
            latitude=37.4225103,
            longitude=-122.0847089,
            documents_ids=[doc_id],
        )
        create_response = subject.post("/api/properties", json=property_data.model_dump())
        assert create_response.status_code == HTTPStatus.CREATED
        created_id = create_response.json().get("id")
        assert created_id is not None
        list_response = subject.get("/api/properties/list")
        assert list_response.status_code == HTTPStatus.OK
        properties = list_response.json()
        assert len(properties) == 1
        assert properties[0]["id"] == created_id

    def test_delete_document_from_property(self, subject, httpserver: HTTPServer):
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

    def test_create_property_enriches_with_county_polygon(self, subject, httpserver: HTTPServer):
        httpserver.expect_request("/geocoder/geographies/coordinates").respond_with_json(
            {"result": {"geographies": {"Counties": [{"GEOID": "21111", "NAME": "Jefferson", "STATE": "21"}]}}}
        )
        httpserver.expect_request("/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query").respond_with_json(
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
        response = subject.post("/api/properties", json=PropertyInfo(latitude=38.254, longitude=-85.759).model_dump())
        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert body["county_fips"] == "21111"
        assert body["county_polygon"]["type"] == "Polygon"

    def test_create_property_reuses_county_boundary_for_same_fips(self, subject, httpserver: HTTPServer):
        polygon = {
            "type": "Polygon",
            "coordinates": [[[-86.035, 37.997], [-85.404, 37.997], [-85.404, 38.375], [-86.035, 37.997]]],
        }
        httpserver.expect_request("/geocoder/geographies/coordinates").respond_with_json(
            {"result": {"geographies": {"Counties": [{"GEOID": "21111", "NAME": "Jefferson", "STATE": "21"}]}}}
        )
        httpserver.expect_oneshot_request(
            "/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query"
        ).respond_with_json(
            {
                "features": [
                    {
                        "geometry": {
                            "rings": [[[-86.035, 37.997], [-85.404, 37.997], [-85.404, 38.375], [-86.035, 37.997]]],
                            "spatialReference": {"wkid": 4326},
                        }
                    }
                ]
            }
        )
        responses = [
            subject.post("/api/properties", json=PropertyInfo(latitude=38.254, longitude=-85.759).model_dump())
            for _ in range(2)
        ]
        assert all(r.status_code == HTTPStatus.CREATED for r in responses)
        assert responses[0].json()["county_polygon"] == polygon
        assert responses[1].json()["county_polygon"] == polygon

    def test_user_b_cannot_access_user_a_property(self, subject, test_container: Container, httpserver: HTTPServer):
        httpserver.expect_request("/v1/embeddings").respond_with_json(
            {"data": [{"embedding": [0.1] * 1536}], "usage": {"total_tokens": 10}}
        )
        db = test_container.db()
        with db.session() as session:
            brokerage_a = Brokerage(name="Brokerage A")
            session.add(brokerage_a)
            brokerage_b = Brokerage(name="Brokerage B")
            session.add(brokerage_b)
            session.commit()
            session.refresh(brokerage_a)
            session.refresh(brokerage_b)
            user_a = User(
                email="agentA@brokerageA.com", hashed_password="fake-hash", role="AGENT", brokerage_id=brokerage_a.id
            )
            user_b = User(
                email="agentB@brokerageB.com", hashed_password="fake-hash", role="AGENT", brokerage_id=brokerage_b.id
            )
            session.add(user_a)
            session.add(user_b)
            session.commit()
            session.refresh(user_a)
            session.refresh(user_b)
            token_a = make_jwt(user_a.id, brokerage_a.id, role=user_a.role)
            token_b = make_jwt(user_b.id, brokerage_b.id, role=user_b.role)
        create_resp = subject.post(
            "/api/properties",
            json=PropertyInfo(latitude=39.7684, longitude=-86.1581, state="IN").model_dump(),
            cookies={"access_token": token_a},
        )
        assert create_resp.status_code == HTTPStatus.CREATED
        property_id = create_resp.json()["id"]
        list_resp_b = subject.get("/api/properties/list", cookies={"access_token": token_b})
        assert list_resp_b.status_code == HTTPStatus.OK
        assert len(list_resp_b.json()) == 0
        upload_resp = subject.post(
            "/api/documents",
            files={"file": open("tests/integration/fixtures/mls_sheet.pdf", "rb")},
            cookies={"access_token": token_b},
        )
        doc_id = upload_resp.json()["id"]
        append_resp = subject.patch(
            f"/api/properties/{property_id}/documents",
            json={"id": doc_id, "filename": "mls_sheet.pdf"},
            cookies={"access_token": token_b},
        )
        assert append_resp.status_code == HTTPStatus.NOT_FOUND

    def test_create_property_rejects_dual_agency_when_brokerage_disallows(self, subject):
        response = subject.post(
            "/api/properties",
            json=PropertyInfo(is_listing_side=True, is_buyer_side=True).model_dump(),
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_create_property_allows_dual_agency_when_brokerage_permits(self, subject, test_container: Container):
        db = test_container.db()
        brokerage_id, user_id = seed_brokerage_and_user(
            db, name="Dual Agency Firm", email="dual@firm.com", allow_dual_agency=True
        )
        token = make_jwt(user_id, brokerage_id)
        subject.cookies.set("access_token", token)
        response = subject.post(
            "/api/properties",
            json=PropertyInfo(is_listing_side=True, is_buyer_side=True).model_dump(),
        )
        assert response.status_code == HTTPStatus.CREATED

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
