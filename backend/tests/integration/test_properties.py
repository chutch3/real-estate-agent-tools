import os
from http import HTTPStatus
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from backend.container import Container
from backend.main import create_app
from backend.models import Brokerage, CreatePropertyRequest, Property, Representation, User
from backend.schema import drop_document_embeddings_schema
from tests.integration.conftest import make_jwt, seed_brokerage_and_user

MILVUS_URI = "http://localhost:19530"

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


class TestCreateProperty:
    def test_returns_representation_id_and_role(self, subject):
        body = CreatePropertyRequest(role="listing_agent").model_dump()

        response = subject.post("/api/properties", json=body)

        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert "representation_id" in data
        assert data["representation_id"] is not None
        assert data["role"] == "listing_agent"

    def test_creates_representation_row(self, subject, test_container: Container):
        body = CreatePropertyRequest(role="buyers_agent").model_dump()

        response = subject.post("/api/properties", json=body)

        assert response.status_code == HTTPStatus.CREATED
        property_id = response.json()["id"]
        with test_container.db().session() as session:
            rep = session.exec(select(Representation).where(Representation.property_id == property_id)).first()
        assert rep is not None
        assert rep.role == "buyers_agent"

    def test_returns_parcel_polygon(self, subject, httpserver):
        httpserver.expect_request("/query").respond_with_json(_ARCGIS_PARCEL_RESPONSE)
        body = CreatePropertyRequest(
            role="listing_agent", latitude=39.7684, longitude=-86.1581, state="IN"
        ).model_dump()

        response = subject.post("/api/properties", json=body)

        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data["parcel_polygon"] is not None
        assert data["parcel_polygon"]["type"] == "Polygon"

    def test_persists_parcel_with_state_parcel_id(self, subject, test_container: Container, httpserver):
        httpserver.expect_request("/query").respond_with_json(_ARCGIS_PARCEL_RESPONSE)
        body = CreatePropertyRequest(
            role="listing_agent", latitude=39.7684, longitude=-86.1581, state="IN"
        ).model_dump()

        response = subject.post("/api/properties", json=body)

        assert response.status_code == HTTPStatus.CREATED
        property_id = response.json()["id"]
        with test_container.db().session() as session:
            prop = session.get(Property, property_id)
        assert prop is not None
        # state_parcel_id now lives on the parcel row, not the property
        from backend.models import Parcel

        with test_container.db().session() as session:
            parcel = session.exec(select(Parcel).where(Parcel.property_id == property_id)).first()
        assert parcel is not None
        assert parcel.state_parcel_id == "102403200259000013"

    def test_enriches_with_county_polygon(self, subject, httpserver):
        httpserver.expect_request("/geocoder/geographies/coordinates").respond_with_json(
            {"result": {"geographies": {"Counties": [{"GEOID": "21111", "NAME": "Jefferson", "STATE": "21"}]}}}
        )
        httpserver.expect_request("/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query").respond_with_json(
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
        body = CreatePropertyRequest(role="listing_agent", latitude=38.254, longitude=-85.759).model_dump()

        response = subject.post("/api/properties", json=body)

        assert response.status_code == HTTPStatus.CREATED
        data = response.json()
        assert data["county_fips"] == "21111"
        assert data["county_polygon"]["type"] == "Polygon"

    def test_returns_formatted_address(self, subject):
        body = CreatePropertyRequest(
            role="listing_agent",
            address_line1="123 Main St",
            city="Jeffersonville",
            state="IN",
            zip_code="47130",
        ).model_dump()

        response = subject.post("/api/properties", json=body)

        assert response.status_code == HTTPStatus.CREATED
        assert response.json()["formatted_address"] == "123 Main St, Jeffersonville, IN, 47130"

    def test_rejects_when_role_missing(self, subject):
        response = subject.post("/api/properties", json={})

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    @pytest.fixture
    def subject(self, test_container, tmp_path, httpserver, integration_services):
        yield from _make_client(test_container, tmp_path, httpserver)


class TestListProperties:
    def test_returns_empty_when_no_properties(self, subject):
        response = subject.get("/api/properties/list")

        assert response.status_code == HTTPStatus.OK
        assert response.json() == []

    def test_returns_representation_id_and_role(self, subject):
        body = CreatePropertyRequest(role="listing_agent", city="Jeffersonville").model_dump()
        create_resp = subject.post("/api/properties", json=body)
        assert create_resp.status_code == HTTPStatus.CREATED

        list_resp = subject.get("/api/properties/list")

        assert list_resp.status_code == HTTPStatus.OK
        properties = list_resp.json()
        assert len(properties) == 1
        assert "representation_id" in properties[0]
        assert properties[0]["role"] == "listing_agent"

    def test_brokerage_isolation(self, subject, test_container: Container, httpserver):
        db = test_container.db()
        with db.session() as session:
            brokerage_b = Brokerage(name="Brokerage B")
            session.add(brokerage_b)
            session.commit()
            session.refresh(brokerage_b)
            user_b = User(
                email="agentB@test.com",
                hashed_password="fake-hash",
                role="AGENT",
                brokerage_id=brokerage_b.id,
            )
            session.add(user_b)
            session.commit()
            session.refresh(user_b)
            token_b = make_jwt(user_b.id, brokerage_b.id, role=user_b.role)

        subject.post("/api/properties", json=CreatePropertyRequest(role="listing_agent").model_dump())

        list_resp = subject.get("/api/properties/list", cookies={"access_token": token_b})
        assert list_resp.status_code == HTTPStatus.OK
        assert list_resp.json() == []

    @pytest.fixture
    def subject(self, test_container, tmp_path, httpserver, integration_services):
        yield from _make_client(test_container, tmp_path, httpserver)


class TestAddRepresentation:
    def test_adds_second_representation_to_existing_property(self, subject, test_container: Container):
        create_resp = subject.post("/api/properties", json=CreatePropertyRequest(role="listing_agent").model_dump())
        assert create_resp.status_code == HTTPStatus.CREATED
        property_id = create_resp.json()["id"]

        rep_resp = subject.post(
            f"/api/properties/{property_id}/representations",
            json={"role": "buyers_agent"},
        )

        assert rep_resp.status_code == HTTPStatus.CREATED
        with test_container.db().session() as session:
            reps = session.exec(select(Representation).where(Representation.property_id == property_id)).all()
        assert len(reps) == 2
        roles = {r.role for r in reps}
        assert roles == {"listing_agent", "buyers_agent"}

    def test_rejects_dual_agency_when_brokerage_disallows(self, subject):
        create_resp = subject.post("/api/properties", json=CreatePropertyRequest(role="listing_agent").model_dump())
        assert create_resp.status_code == HTTPStatus.CREATED
        property_id = create_resp.json()["id"]

        rep_resp = subject.post(
            f"/api/properties/{property_id}/representations",
            json={"role": "buyers_agent"},
        )

        assert rep_resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_allows_dual_agency_when_brokerage_permits(self, subject_with_dual_agency):
        create_resp = subject_with_dual_agency.post(
            "/api/properties", json=CreatePropertyRequest(role="listing_agent").model_dump()
        )
        assert create_resp.status_code == HTTPStatus.CREATED
        property_id = create_resp.json()["id"]

        rep_resp = subject_with_dual_agency.post(
            f"/api/properties/{property_id}/representations",
            json={"role": "buyers_agent"},
        )

        assert rep_resp.status_code == HTTPStatus.CREATED

    def test_returns_404_for_unknown_property(self, subject):
        response = subject.post(
            "/api/properties/nonexistent/representations",
            json={"role": "buyers_agent"},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    @pytest.fixture
    def subject(self, test_container, tmp_path, httpserver, integration_services):
        yield from _make_client(test_container, tmp_path, httpserver)

    @pytest.fixture
    def subject_with_dual_agency(self, test_container, tmp_path, httpserver, integration_services):
        yield from _make_client(test_container, tmp_path, httpserver, allow_dual_agency=True)


def _make_client(test_container, tmp_path, httpserver, *, allow_dual_agency: bool = False):
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
            brokerage_id, user_id = seed_brokerage_and_user(test_container.db(), allow_dual_agency=allow_dual_agency)
            token = make_jwt(user_id, brokerage_id)
            client.cookies.set("access_token", token)
            yield client
    drop_document_embeddings_schema()
