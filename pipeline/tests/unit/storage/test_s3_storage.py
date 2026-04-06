import json
from datetime import date

import boto3
import pytest
from moto import mock_aws

from pipeline.storage.s3 import S3TileStorage


class TestS3TileStorage:
    _BUCKET = "test-bucket"
    _REGION = "us-east-1"

    @pytest.fixture
    def s3_setup(self):
        with mock_aws():
            client = boto3.client("s3", region_name=self._REGION)
            client.create_bucket(Bucket=self._BUCKET)
            yield client

    @pytest.fixture
    def subject(self, s3_setup) -> S3TileStorage:
        return S3TileStorage(
            bucket=self._BUCKET,
            region_name=self._REGION,
        )

    def test_store_data_tile_uploads_to_correct_key(self, subject, s3_setup):
        cog_bytes = b"fake-cog"

        subject.store_data_tile(
            crime_category="violent",
            resolution_m=200,
            date_from=date(2025, 1, 1),
            date_to=date(2025, 12, 31),
            version="v1",
            fips="21111",
            cog_bytes=cog_bytes,
        )

        response = s3_setup.get_object(
            Bucket=self._BUCKET,
            Key="tiles/data/violent/200m/2025-01-01/2025-12-31/v1/21111/latest.tif",
        )
        assert response["Body"].read() == cog_bytes
        assert response["ContentType"] == "image/tiff"

    def test_store_data_tile_uses_category_in_key(self, subject, s3_setup):
        subject.store_data_tile(
            crime_category="property",
            resolution_m=200,
            date_from=date(2025, 1, 1),
            date_to=date(2025, 12, 31),
            version="v1",
            fips="21111",
            cog_bytes=b"bytes",
        )

        s3_setup.get_object(
            Bucket=self._BUCKET,
            Key="tiles/data/property/200m/2025-01-01/2025-12-31/v1/21111/latest.tif",
        )

    def test_store_png_tile_uploads_to_correct_key(self, subject, s3_setup):
        png_bytes = b"\x89PNG-fake"

        subject.store_png_tile(layer_id="crime-violent", z=12, x=1234, y=3456, png_bytes=png_bytes)

        response = s3_setup.get_object(
            Bucket=self._BUCKET,
            Key="tiles/png/crime-violent/12/1234/3456.png",
        )
        assert response["Body"].read() == png_bytes
        assert response["ContentType"] == "image/png"

    def test_store_meta_uploads_to_correct_key(self, subject, s3_setup):
        meta = {"date_from": "2025-01-01", "record_count": 42}
        meta_bytes = json.dumps(meta).encode()

        subject.store_meta(layer_id="crime-violent", fips="21111", meta_bytes=meta_bytes)

        response = s3_setup.get_object(
            Bucket=self._BUCKET,
            Key="tiles/meta/crime-violent/21111/meta.json",
        )
        assert json.loads(response["Body"].read()) == meta
        assert response["ContentType"] == "application/json"
