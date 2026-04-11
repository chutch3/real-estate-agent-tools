import json
import os
from http import HTTPStatus
from unittest.mock import patch

import boto3
import pytest
from fastapi.testclient import TestClient
from pytest_httpserver import HTTPServer

from backend.container import Container
from backend.main import create_app
from backend.schema import drop_document_embeddings_schema
from tests.integration.conftest import make_jwt, seed_brokerage_and_user

MILVUS_URI = "http://localhost:19530"
_MOTO_URL = "http://localhost:5005"
_S3_BUCKET = "test-documents"


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


class TestLayers:
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
