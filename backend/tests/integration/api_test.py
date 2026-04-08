import json
import os
from http import HTTPStatus
from unittest.mock import AsyncMock, patch

import boto3
import jose.jwt as jwt
import pytest
from fastapi.testclient import TestClient
from pymilvus import MilvusClient
from pymilvus.exceptions import MilvusException
from pytest_httpserver import HTTPServer
from werkzeug.wrappers import Response as WerkzeugResponse

from backend.container import Container
from backend.main import create_app
from backend.models import (
    AgentInfo,
    Brokerage,
    DocumentInfo,
    GeocodeLocation,
    GeocodeRequest,
    GeocodeResponse,
    PostGenerationRequest,
    PropertyInfo,
    TemplateResponse,
    User,
)
from backend.schema import drop_document_embeddings_schema
from backend.template_loader import TEMPLATE_DIR

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
            },
        }
    ]
}


def _make_test_png() -> bytes:
    from io import BytesIO

    import numpy as np
    from PIL import Image

    rgba = np.zeros((256, 256, 4), dtype=np.uint8)
    rgba[:, :, 0] = 100
    rgba[:, :, 3] = 200
    buf = BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, format="PNG")
    return buf.getvalue()


class TestApp:
    def test_health_check(self, subject):
        response = subject.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

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

    def test_get_default_template(self, subject):
        response = subject.get("/api/templates/default")
        assert response.status_code == HTTPStatus.OK
        with open(f"{TEMPLATE_DIR}/post_prompt.txt") as file:
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
        assert response.headers.get("Access-Control-Allow-Origin") == expected_allow_origin
        assert all(
            method in response.headers["Access-Control-Allow-Methods"]
            for method in ["DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"]
        )
        assert response.text == expected_response

    def test_create_property_returns_parcel_polygon(self, subject, httpserver: HTTPServer):
        httpserver.expect_request("/query").respond_with_json(_ARCGIS_PARCEL_RESPONSE)

        property_data = PropertyInfo(
            rentcast_id="some-rentcast-id",
            latitude=39.7684,
            longitude=-86.1581,
            state="IN",
        )
        response = subject.post("/api/properties", json=property_data.model_dump())

        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert body["parcel_polygon"] is not None
        assert body["parcel_polygon"]["type"] == "Polygon"

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

    def test_upload_pdf(self, subject, httpserver: HTTPServer, milvus_client, test_container: Container):
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
        assert any(
            "Buyers Brokers Only, LLC \n| \nExclusive Buyer Agents - MA & NH \n| Tel: 617.501.0233" in chunk.get("text")
            for chunk in actual
        )
        assert actual[0].get("embedding") is not None

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

    def test_get_layers_returns_groups_with_categories_when_data_exists(self, subject, s3_client):
        for layer_id in ("crime-violent", "crime-property"):
            s3_client.put_object(
                Bucket=_S3_BUCKET,
                Key=f"tiles/meta/{layer_id}/21111/meta.json",
                Body=json.dumps(
                    {
                        "date_from": "2025-04-01",
                        "date_to": "2026-04-01",
                        "record_count": 42,
                        "bbox": [-86.035, 37.997, -85.404, 38.375],
                        "tile_zoom": 12,
                    }
                ).encode(),
                ContentType="application/json",
            )

        response = subject.get("/api/layers")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert "groups" in body
        assert len(body["groups"]) == 1
        group = body["groups"][0]
        assert group["id"] == "crime"
        assert group["label"] == "Crime"
        assert len(group["categories"]) == 2
        ids = {c["id"] for c in group["categories"]}
        assert ids == {"crime-violent", "crime-property"}
        violent = next(c for c in group["categories"] if c["id"] == "crime-violent")
        assert violent["label"] == "Violent Crime"
        assert violent["date_from"] == "2025-04-01"
        assert violent["date_to"] == "2026-04-01"
        assert violent["record_count"] == 42
        assert violent["bbox"] == [-86.035, 37.997, -85.404, 38.375]
        assert violent["tile_zoom"] == 12

    def test_get_layers_returns_empty_groups_when_no_data(self, subject, s3_client):
        response = subject.get("/api/layers")

        assert response.status_code == HTTPStatus.OK
        body = response.json()
        assert body["groups"] == []

    def test_get_layer_tile_returns_pre_rendered_png(self, subject, s3_client):
        png_bytes = _make_test_png()
        s3_client.put_object(
            Bucket=_S3_BUCKET,
            Key="tiles/png/crime-violent/12/1234/3456.png",
            Body=png_bytes,
            ContentType="image/png",
        )

        response = subject.get("/api/layers/crime-violent/tiles/12/1234/3456")

        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "image/png"
        assert response.content == png_bytes

    def test_get_layer_tile_returns_transparent_png_when_no_tile_exists(self, subject, s3_client):
        response = subject.get("/api/layers/crime-violent/tiles/12/0/0")

        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "image/png"
        assert response.content[:4] == b"\x89PNG"

    @pytest.fixture
    def s3_client(self, integration_services):
        client = boto3.client(
            "s3",
            endpoint_url=_MOTO_URL,
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name="us-east-1",
        )
        yield client
        for prefix in ("tiles/",):
            response = client.list_objects_v2(Bucket=_S3_BUCKET, Prefix=prefix)
            for obj in response.get("Contents", []):
                client.delete_object(Bucket=_S3_BUCKET, Key=obj["Key"])

    @pytest.fixture
    def milvus_client(self, subject, test_container: Container) -> MilvusClient:
        yield test_container.milvus_client()

    def test_create_property_enriches_with_county_polygon(self, subject, httpserver: HTTPServer):
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

        response = subject.post(
            "/api/properties",
            json=PropertyInfo(latitude=38.254, longitude=-85.759).model_dump(),
        )

        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert body["county_fips"] == "21111"
        assert body["county_polygon"] == {
            "type": "Polygon",
            "coordinates": [
                [
                    [-86.035, 37.997],
                    [-85.404, 37.997],
                    [-85.404, 38.375],
                    [-86.035, 38.375],
                    [-86.035, 37.997],
                ]
            ],
        }

    def test_create_property_reuses_county_boundary_for_same_fips(self, subject, httpserver: HTTPServer):
        polygon = {
            "type": "Polygon",
            "coordinates": [[[-86.035, 37.997], [-85.404, 37.997], [-85.404, 38.375], [-86.035, 37.997]]],
        }
        httpserver.expect_request(
            "/geocoder/geographies/coordinates",
        ).respond_with_json(
            {"result": {"geographies": {"Counties": [{"GEOID": "21111", "NAME": "Jefferson", "STATE": "21"}]}}}
        )
        # oneshot — only handles one request; a second call would return 500
        httpserver.expect_oneshot_request(
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
                                    [-86.035, 37.997],
                                ]
                            ],
                            "spatialReference": {"wkid": 4326},
                        }
                    }
                ]
            }
        )

        responses = []
        for _ in range(2):
            responses.append(
                subject.post(
                    "/api/properties",
                    json=PropertyInfo(latitude=38.254, longitude=-85.759).model_dump(),
                )
            )

        assert all(r.status_code == HTTPStatus.CREATED for r in responses)
        assert responses[0].json()["county_polygon"] == polygon
        assert responses[1].json()["county_polygon"] == polygon

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

    def test_get_layers_filters_by_county_fips(self, subject, s3_client):
        county_fips = "21111"
        for layer_id in ("crime-violent", "crime-property"):
            s3_client.put_object(
                Bucket=_S3_BUCKET,
                Key=f"tiles/meta/{layer_id}/{county_fips}/meta.json",
                Body=json.dumps(
                    {
                        "date_from": "2025-04-01",
                        "date_to": "2026-04-01",
                        "record_count": 42,
                        "bbox": [-86.035, 37.997, -85.404, 38.375],
                        "tile_zoom": 12,
                    }
                ).encode(),
                ContentType="application/json",
            )

        matching_response = subject.get(f"/api/layers?county_fips={county_fips}")
        assert matching_response.status_code == HTTPStatus.OK
        body = matching_response.json()
        assert len(body["groups"]) == 1
        assert len(body["groups"][0]["categories"]) == 2

        empty_response = subject.get("/api/layers?county_fips=18019")
        assert empty_response.status_code == HTTPStatus.OK
        assert empty_response.json()["groups"] == []

    def test_user_b_cannot_access_user_a_property(self, subject, test_container: Container, httpserver: HTTPServer):
        httpserver.expect_request("/v1/embeddings").respond_with_json(
            {"data": [{"embedding": [0.1] * 1536}], "usage": {"total_tokens": 10}}
        )

        db = test_container.db()
        secret_key = "test-secret"

        with db.session() as session:
            brokerage_a = Brokerage(name="Brokerage A")
            session.add(brokerage_a)
            session.commit()
            session.refresh(brokerage_a)

            user_a = User(
                email="agentA@brokerageA.com", hashed_password="fake-hash", role="AGENT", brokerage_id=brokerage_a.id
            )
            session.add(user_a)

            brokerage_b = Brokerage(name="Brokerage B")
            session.add(brokerage_b)
            session.commit()
            session.refresh(brokerage_b)

            user_b = User(
                email="agentB@brokerageB.com", hashed_password="fake-hash", role="AGENT", brokerage_id=brokerage_b.id
            )
            session.add(user_b)
            session.commit()
            session.refresh(user_a)
            session.refresh(user_b)

            user_a_id = user_a.id
            user_a_role = user_a.role
            brokerage_a_id = brokerage_a.id

            user_b_id = user_b.id
            user_b_role = user_b.role
            brokerage_b_id = brokerage_b.id

        token_a = jwt.encode(
            {"sub": user_a_id, "org": brokerage_a_id, "role": user_a_role}, secret_key, algorithm="HS256"
        )
        token_b = jwt.encode(
            {"sub": user_b_id, "org": brokerage_b_id, "role": user_b_role}, secret_key, algorithm="HS256"
        )

        # User A creates a property
        cookies_a = {"access_token": token_a}
        property_data = PropertyInfo(latitude=39.7684, longitude=-86.1581, state="IN")
        create_resp = subject.post("/api/properties", json=property_data.model_dump(), cookies=cookies_a)

        # We expect a 201 when auth is enforced. Currently it might be 201 without auth.
        assert create_resp.status_code == HTTPStatus.CREATED
        property_id = create_resp.json()["id"]

        # User B attempts to access User A's property list
        cookies_b = {"access_token": token_b}
        list_resp_b = subject.get("/api/properties/list", cookies=cookies_b)
        assert list_resp_b.status_code == HTTPStatus.OK
        properties_b = list_resp_b.json()
        assert len(properties_b) == 0  # User B should see 0 properties

        # User B attempts to append a document to User A's property
        upload_resp = subject.post(
            "/api/documents", files={"file": open("tests/integration/fixtures/mls_sheet.pdf", "rb")}, cookies=cookies_b
        )
        doc_id = upload_resp.json()["id"]
        doc_data = {"id": doc_id, "filename": "mls_sheet.pdf"}
        append_resp_b = subject.patch(f"/api/properties/{property_id}/documents", json=doc_data, cookies=cookies_b)
        # Should be a 404 because the property doesn't exist for User B
        assert append_resp_b.status_code == HTTPStatus.NOT_FOUND

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
                db = test_container.db()
                with db.session() as session:
                    brokerage = Brokerage(name="Default Brokerage")
                    session.add(brokerage)
                    session.commit()
                    session.refresh(brokerage)

                    user = User(
                        email="default@brokerage.com",
                        hashed_password="fake-hash",
                        role="AGENT",
                        brokerage_id=brokerage.id,
                    )
                    session.add(user)
                    session.commit()
                    session.refresh(user)

                    user_id = user.id
                    brokerage_id = brokerage.id
                    user_role = user.role

                token = jwt.encode(
                    {"sub": user_id, "org": brokerage_id, "role": user_role}, "test-secret", algorithm="HS256"
                )
                client.cookies.set("access_token", token)
                yield client
        drop_document_embeddings_schema()
