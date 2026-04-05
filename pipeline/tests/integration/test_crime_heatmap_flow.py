import json
from datetime import date
from pathlib import Path

import pytest
import yaml
from pytest_httpserver import HTTPServer
from rasterio.io import MemoryFile
from shapely.geometry import box

from pipeline.flows.crime_heatmap import crime_heatmap_pipeline, execute_heatmap
from pipeline.regions.loader import Region
from pipeline.sources.socrata import SocrataSource
from pipeline.storage.s3 import S3LayerStorage
from tests.conftest import _AWS_ACCESS_KEY, _AWS_REGION, _AWS_SECRET_KEY, _MOTO_URL, _TEST_BUCKET

_LOUISVILLE_BBOX = (-86.035, 37.997, -85.404, 38.375)

_LOUISVILLE_POLYGON = box(-86.035, 37.997, -85.404, 38.375)

_THREE_INCIDENTS = [
    {
        "latitude": "38.25",
        "longitude": "-85.75",
        "date_occured": "2025-06-15T00:00:00.000",
        "offense": "ASSAULT",
    },
    {
        "latitude": "38.20",
        "longitude": "-85.80",
        "date_occured": "2025-07-01T00:00:00.000",
        "offense": "BURGLARY",
    },
    {
        "latitude": "38.18",
        "longitude": "-85.72",
        "date_occured": "2025-08-10T00:00:00.000",
        "offense": "THEFT",
    },
]


@pytest.fixture
def region(httpserver: HTTPServer) -> Region:
    return Region(
        slug="louisville-metro",
        polygon=_LOUISVILLE_POLYGON,
        sources=[
            SocrataSource(
                name="louisville-metro-pd",
                dataset_id="4sxa-cwis",
                date_field="date_occured",
                lat_field="latitude",
                lon_field="longitude",
                category_field="offense",
                base_url=httpserver.url_for("").rstrip("/"),
            )
        ],
    )


@pytest.fixture
def storage() -> S3LayerStorage:
    return S3LayerStorage(
        bucket=_TEST_BUCKET,
        endpoint_url=_MOTO_URL,
        access_key=_AWS_ACCESS_KEY,
        secret_key=_AWS_SECRET_KEY,
        region_name=_AWS_REGION,
    )


def test_execute_heatmap_produces_cog_per_category(
    region: Region,
    storage: S3LayerStorage,
    s3_client,
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_request("/resource/4sxa-cwis.json").respond_with_json(_THREE_INCIDENTS)

    execute_heatmap(
        region=region,
        date_from=date(2025, 1, 1),
        date_to=date(2025, 12, 31),
        storage=storage,
    )

    for layer_id in ("crime-violent", "crime-property"):
        cog_response = s3_client.get_object(
            Bucket=_TEST_BUCKET,
            Key=f"layers/{layer_id}/louisville-metro/latest.tif",
        )
        cog_bytes = cog_response["Body"].read()
        with MemoryFile(cog_bytes) as memfile:
            with memfile.open() as dataset:
                assert dataset.count == 1
                assert dataset.crs.to_epsg() == 3857


def test_execute_heatmap_writes_correct_meta(
    region: Region,
    storage: S3LayerStorage,
    s3_client,
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_request("/resource/4sxa-cwis.json").respond_with_json(_THREE_INCIDENTS)

    execute_heatmap(
        region=region,
        date_from=date(2025, 1, 1),
        date_to=date(2025, 12, 31),
        storage=storage,
    )

    violent_meta = json.loads(
        s3_client.get_object(
            Bucket=_TEST_BUCKET,
            Key="layers/crime-violent/louisville-metro/meta.json",
        )["Body"].read()
    )
    assert violent_meta["date_from"] == "2025-01-01"
    assert violent_meta["date_to"] == "2025-12-31"
    assert violent_meta["record_count"] == 1
    assert violent_meta["bbox"] == list(_LOUISVILLE_POLYGON.bounds)
    assert "region_slug" not in violent_meta
    assert "generated_at" not in violent_meta

    property_meta = json.loads(
        s3_client.get_object(
            Bucket=_TEST_BUCKET,
            Key="layers/crime-property/louisville-metro/meta.json",
        )["Body"].read()
    )
    assert property_meta["record_count"] == 2


def test_execute_heatmap_produces_cog_for_each_category_when_no_records(
    region: Region,
    storage: S3LayerStorage,
    s3_client,
    httpserver: HTTPServer,
) -> None:
    httpserver.expect_request("/resource/4sxa-cwis.json").respond_with_json([])

    execute_heatmap(
        region=region,
        date_from=date(2025, 1, 1),
        date_to=date(2025, 12, 31),
        storage=storage,
    )

    for layer_id in ("crime-violent", "crime-property"):
        cog_bytes = s3_client.get_object(
            Bucket=_TEST_BUCKET,
            Key=f"layers/{layer_id}/louisville-metro/latest.tif",
        )["Body"].read()
        with MemoryFile(cog_bytes) as memfile:
            with memfile.open() as dataset:
                assert dataset.count == 1
                assert dataset.crs.to_epsg() == 3857

        meta = json.loads(
            s3_client.get_object(
                Bucket=_TEST_BUCKET,
                Key=f"layers/{layer_id}/louisville-metro/meta.json",
            )["Body"].read()
        )
        assert meta["record_count"] == 0


_TIGER_COUNTY_RESPONSE = {
    "features": [
        {
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [[
                        [-86.035, 37.997],
                        [-85.404, 37.997],
                        [-85.404, 38.375],
                        [-86.035, 38.375],
                        [-86.035, 37.997],
                    ]]
                ],
            }
        }
    ]
}


@pytest.fixture
def sources_config_path(tmp_path: Path, httpserver: HTTPServer) -> Path:
    config = {
        "21111": [
            {
                "name": "test-pd",
                "type": "socrata",
                "base_url": httpserver.url_for("").rstrip("/"),
                "dataset_id": "4sxa-cwis",
                "date_field": "date_occured",
                "lat_field": "latitude",
                "lon_field": "longitude",
                "category_field": "offense",
                "status": "active",
            }
        ]
    }
    path = tmp_path / "sources_config.yml"
    path.write_text(yaml.dump(config))
    return path


def test_crime_heatmap_pipeline_runs_as_prefect_flow(
    s3_client,
    httpserver: HTTPServer,
    sources_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CRIME_DATA_S3_BUCKET", _TEST_BUCKET)
    monkeypatch.setenv("AWS_ENDPOINT_URL_S3", _MOTO_URL)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", _AWS_ACCESS_KEY)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", _AWS_SECRET_KEY)
    monkeypatch.setenv("AWS_DEFAULT_REGION", _AWS_REGION)
    monkeypatch.setenv("BACKEND_URL", httpserver.url_for("").rstrip("/"))
    monkeypatch.setenv("TIGER_BASE_URL", httpserver.url_for("").rstrip("/"))
    monkeypatch.setenv("SOURCES_CONFIG_PATH", str(sources_config_path))

    httpserver.expect_request("/api/internal/counties").respond_with_json(
        {"county_fips": ["21111"]}
    )
    httpserver.expect_request(
        "/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/13/query"
    ).respond_with_json(_TIGER_COUNTY_RESPONSE)
    httpserver.expect_request("/resource/4sxa-cwis.json").respond_with_json(_THREE_INCIDENTS)

    crime_heatmap_pipeline(
        date_from="2025-01-01",
        date_to="2025-12-31",
    )

    for layer_id in ("crime-violent", "crime-property"):
        cog_bytes = s3_client.get_object(
            Bucket=_TEST_BUCKET,
            Key=f"layers/{layer_id}/21111/latest.tif",
        )["Body"].read()
        with MemoryFile(cog_bytes) as memfile:
            with memfile.open() as dataset:
                assert dataset.count == 1
                assert dataset.crs.to_epsg() == 3857


def test_repeated_pipeline_run_uses_cached_fetch_result(
    s3_client,
    httpserver: HTTPServer,
    sources_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CRIME_DATA_S3_BUCKET", _TEST_BUCKET)
    monkeypatch.setenv("AWS_ENDPOINT_URL_S3", _MOTO_URL)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", _AWS_ACCESS_KEY)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", _AWS_SECRET_KEY)
    monkeypatch.setenv("AWS_DEFAULT_REGION", _AWS_REGION)
    monkeypatch.setenv("BACKEND_URL", httpserver.url_for("").rstrip("/"))
    monkeypatch.setenv("TIGER_BASE_URL", httpserver.url_for("").rstrip("/"))
    monkeypatch.setenv("SOURCES_CONFIG_PATH", str(sources_config_path))

    httpserver.expect_request("/api/internal/counties").respond_with_json(
        {"county_fips": ["21111"]}
    )
    httpserver.expect_request(
        "/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/13/query"
    ).respond_with_json(_TIGER_COUNTY_RESPONSE)
    httpserver.expect_request("/resource/4sxa-cwis.json").respond_with_json(_THREE_INCIDENTS)

    crime_heatmap_pipeline(date_from="2025-01-01", date_to="2025-12-31")
    crime_heatmap_pipeline(date_from="2025-01-01", date_to="2025-12-31")

    source_hits = [req for req, _resp in httpserver.log if "/resource/4sxa-cwis.json" in req.path]
    assert len(source_hits) == 1, (
        f"Expected source to be fetched once (cache hit on second run), got {len(source_hits)} hits"
    )
