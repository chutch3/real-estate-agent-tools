import json
from datetime import date
from unittest.mock import patch

import pytest
from prefect.testing.utilities import prefect_test_harness
from pytest_httpserver import HTTPServer
from rasterio.io import MemoryFile
from shapely.geometry import box

from pipeline.flows.crime_heatmap import crime_heatmap_pipeline, execute_heatmap
from pipeline.regions.loader import Region, load_region
from pipeline.sources.socrata import SocrataSource
from pipeline.storage.s3 import S3LayerStorage
from tests.conftest import _AWS_ACCESS_KEY, _AWS_REGION, _AWS_SECRET_KEY, _MOTO_URL, _TEST_BUCKET

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


@pytest.fixture(scope="module")
def prefect_harness():
    with prefect_test_harness():
        yield


@pytest.fixture
def storage() -> S3LayerStorage:
    return S3LayerStorage(
        bucket=_TEST_BUCKET,
        endpoint_url=_MOTO_URL,
        access_key=_AWS_ACCESS_KEY,
        secret_key=_AWS_SECRET_KEY,
        region_name=_AWS_REGION,
    )


def test_execute_heatmap_produces_valid_cog_in_s3(
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

    cog_response = s3_client.get_object(
        Bucket=_TEST_BUCKET, Key="layers/crime/louisville-metro/latest.tif"
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

    meta_response = s3_client.get_object(
        Bucket=_TEST_BUCKET, Key="layers/crime/louisville-metro/meta.json"
    )
    meta = json.loads(meta_response["Body"].read())
    assert meta["region_slug"] == "louisville-metro"
    assert meta["record_count"] == 3
    assert meta["generated_at"] == "2025-12-31"
    assert meta["bbox"] == list(_LOUISVILLE_POLYGON.bounds)


def test_execute_heatmap_produces_cog_when_no_records(
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

    cog_response = s3_client.get_object(
        Bucket=_TEST_BUCKET, Key="layers/crime/louisville-metro/latest.tif"
    )
    cog_bytes = cog_response["Body"].read()
    with MemoryFile(cog_bytes) as memfile:
        with memfile.open() as dataset:
            assert dataset.count == 1
            assert dataset.crs.to_epsg() == 3857

    meta_response = s3_client.get_object(
        Bucket=_TEST_BUCKET, Key="layers/crime/louisville-metro/meta.json"
    )
    meta = json.loads(meta_response["Body"].read())
    assert meta["record_count"] == 0


def test_crime_heatmap_pipeline_runs_as_prefect_flow(
    prefect_harness,
    region: Region,
    s3_client,
    httpserver: HTTPServer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CRIME_DATA_S3_BUCKET", _TEST_BUCKET)
    monkeypatch.setenv("AWS_ENDPOINT_URL_S3", _MOTO_URL)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", _AWS_ACCESS_KEY)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", _AWS_SECRET_KEY)
    monkeypatch.setenv("AWS_DEFAULT_REGION", _AWS_REGION)

    httpserver.expect_request("/resource/4sxa-cwis.json").respond_with_json(_THREE_INCIDENTS)

    with patch(
        "pipeline.flows.crime_heatmap.load_region",
        spec=load_region,
        return_value=region,
    ) as mock_load_region:
        crime_heatmap_pipeline(
            region_slug="louisville-metro",
            date_from="2025-01-01",
            date_to="2025-12-31",
        )

    mock_load_region.assert_called_once_with("louisville-metro")

    cog_response = s3_client.get_object(
        Bucket=_TEST_BUCKET, Key="layers/crime/louisville-metro/latest.tif"
    )
    cog_bytes = cog_response["Body"].read()
    with MemoryFile(cog_bytes) as memfile:
        with memfile.open() as dataset:
            assert dataset.count == 1
            assert dataset.crs.to_epsg() == 3857
