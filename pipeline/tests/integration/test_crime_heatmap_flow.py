import json
from datetime import date
from pathlib import Path

import pytest
import yaml
from PIL import Image
from io import BytesIO
from pytest_httpserver import HTTPServer
from rasterio.io import MemoryFile
from shapely.geometry import box

from pipeline.flows.crime_heatmap import crime_heatmap_pipeline, execute_heatmap
from pipeline.regions.loader import Region
from pipeline.sources.socrata import SocrataSource
from pipeline.storage.s3 import S3TileStorage
from tests.conftest import _AWS_ACCESS_KEY, _AWS_REGION, _AWS_SECRET_KEY, _MOTO_URL, _TEST_BUCKET

_LOUISVILLE_BBOX = (-86.035, 37.997, -85.404, 38.375)
_LOUISVILLE_POLYGON = box(-86.035, 37.997, -85.404, 38.375)
_FIPS = "21111"

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
        slug=_FIPS,
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
def storage() -> S3TileStorage:
    return S3TileStorage(
        bucket=_TEST_BUCKET,
        endpoint_url=_MOTO_URL,
        access_key=_AWS_ACCESS_KEY,
        secret_key=_AWS_SECRET_KEY,
        region_name=_AWS_REGION,
    )


class TestExecuteHeatmap:
    def test_produces_data_cog_per_category(
        self,
        region: Region,
        storage: S3TileStorage,
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

        for crime_category in ("violent", "property"):
            response = s3_client.get_object(
                Bucket=_TEST_BUCKET,
                Key=f"tiles/data/{crime_category}/200m/2025-01-01/2025-12-31/v1/{_FIPS}/latest.tif",
            )
            cog_bytes = response["Body"].read()
            with MemoryFile(cog_bytes) as memfile:
                with memfile.open() as dataset:
                    assert dataset.count == 1
                    assert dataset.crs.to_epsg() == 3857

    def test_produces_png_tiles_per_category(
        self,
        region: Region,
        storage: S3TileStorage,
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
            paginator = s3_client.get_paginator("list_objects_v2")
            keys = [
                obj["Key"]
                for page in paginator.paginate(Bucket=_TEST_BUCKET, Prefix=f"tiles/png/{layer_id}/12/")
                for obj in page.get("Contents", [])
            ]
            assert len(keys) > 0, f"Expected PNG tiles for {layer_id}"
            for key in keys:
                png_bytes = s3_client.get_object(Bucket=_TEST_BUCKET, Key=key)["Body"].read()
                img = Image.open(BytesIO(png_bytes))
                assert img.format == "PNG"
                assert img.mode == "RGBA"
                assert img.size == (256, 256)

    def test_writes_correct_meta_per_category(
        self,
        region: Region,
        storage: S3TileStorage,
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
                Key=f"tiles/meta/crime-violent/{_FIPS}/meta.json",
            )["Body"].read()
        )
        assert violent_meta["date_from"] == "2025-01-01"
        assert violent_meta["date_to"] == "2025-12-31"
        assert violent_meta["record_count"] == 1
        assert violent_meta["bbox"] == list(_LOUISVILLE_POLYGON.bounds)
        assert violent_meta["tile_zoom"] == 12

        property_meta = json.loads(
            s3_client.get_object(
                Bucket=_TEST_BUCKET,
                Key=f"tiles/meta/crime-property/{_FIPS}/meta.json",
            )["Body"].read()
        )
        assert property_meta["record_count"] == 2

    def test_produces_output_when_no_records(
        self,
        region: Region,
        storage: S3TileStorage,
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

        for crime_category in ("violent", "property"):
            s3_client.get_object(
                Bucket=_TEST_BUCKET,
                Key=f"tiles/data/{crime_category}/200m/2025-01-01/2025-12-31/v1/{_FIPS}/latest.tif",
            )

        for layer_id in ("crime-violent", "crime-property"):
            meta = json.loads(
                s3_client.get_object(
                    Bucket=_TEST_BUCKET,
                    Key=f"tiles/meta/{layer_id}/{_FIPS}/meta.json",
                )["Body"].read()
            )
            assert meta["record_count"] == 0


_TIGER_COUNTY_RESPONSE = {
    "features": [
        {
            "geometry": {
                "type": "Polygon",
                "rings": [
                    [
                        [-86.035, 37.997],
                        [-85.404, 37.997],
                        [-85.404, 38.375],
                        [-86.035, 38.375],
                        [-86.035, 37.997],
                    ]
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


def test_crime_heatmap_pipeline_produces_png_tiles(
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
        "/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query"
    ).respond_with_json(_TIGER_COUNTY_RESPONSE)
    httpserver.expect_request("/resource/4sxa-cwis.json").respond_with_json(_THREE_INCIDENTS)

    crime_heatmap_pipeline(
        date_from="2025-01-01",
        date_to="2025-12-31",
    )

    for layer_id in ("crime-violent", "crime-property"):
        paginator = s3_client.get_paginator("list_objects_v2")
        keys = [
            obj["Key"]
            for page in paginator.paginate(Bucket=_TEST_BUCKET, Prefix=f"tiles/png/{layer_id}/12/")
            for obj in page.get("Contents", [])
        ]
        assert len(keys) > 0, f"Expected PNG tiles for {layer_id} in full pipeline run"


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
        "/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query"
    ).respond_with_json(_TIGER_COUNTY_RESPONSE)
    httpserver.expect_request("/resource/4sxa-cwis.json").respond_with_json(_THREE_INCIDENTS)

    crime_heatmap_pipeline(date_from="2025-01-01", date_to="2025-12-31")
    crime_heatmap_pipeline(date_from="2025-01-01", date_to="2025-12-31")

    source_hits = [req for req, _resp in httpserver.log if "/resource/4sxa-cwis.json" in req.path]
    assert len(source_hits) == 1, (
        f"Expected source to be fetched once (cache hit on second run), got {len(source_hits)} hits"
    )
