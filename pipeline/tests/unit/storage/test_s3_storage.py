import json

import boto3
import pytest
from moto import mock_aws

from pipeline.storage.s3 import S3LayerStorage


class TestS3LayerStorage:
    _BUCKET = "test-bucket"
    _REGION = "us-east-1"

    @pytest.fixture
    def s3_setup(self):
        with mock_aws():
            client = boto3.client("s3", region_name=self._REGION)
            client.create_bucket(Bucket=self._BUCKET)
            yield client

    @pytest.fixture
    def subject(self, s3_setup) -> S3LayerStorage:
        return S3LayerStorage(
            bucket=self._BUCKET,
            region_name=self._REGION,
        )

    def test_store_cog_uploads_to_correct_key(self, subject, s3_setup):
        cog_bytes = b"test-cog-content"
        region_slug = "test-region"

        subject.store_cog(region_slug, cog_bytes)

        response = s3_setup.get_object(
            Bucket=self._BUCKET,
            Key=f"layers/crime/{region_slug}/latest.tif"
        )
        assert response["Body"].read() == cog_bytes
        assert response["ContentType"] == "image/tiff"

    def test_store_meta_uploads_to_correct_key(self, subject, s3_setup):
        meta = {"test": "data"}
        meta_bytes = json.dumps(meta).encode()
        region_slug = "test-region"

        subject.store_meta(region_slug, meta_bytes)

        response = s3_setup.get_object(
            Bucket=self._BUCKET,
            Key=f"layers/crime/{region_slug}/meta.json"
        )
        assert json.loads(response["Body"].read()) == meta
        assert response["ContentType"] == "application/json"
