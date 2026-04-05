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

        subject.store_cog("crime-violent", "louisville-metro", cog_bytes)

        response = s3_setup.get_object(
            Bucket=self._BUCKET,
            Key="layers/crime-violent/louisville-metro/latest.tif",
        )
        assert response["Body"].read() == cog_bytes
        assert response["ContentType"] == "image/tiff"

    def test_store_cog_uses_layer_id_in_key(self, subject, s3_setup):
        subject.store_cog("crime-property", "louisville-metro", b"bytes")

        s3_setup.get_object(
            Bucket=self._BUCKET,
            Key="layers/crime-property/louisville-metro/latest.tif",
        )

    def test_store_meta_uploads_to_correct_key(self, subject, s3_setup):
        meta = {"test": "data"}
        meta_bytes = json.dumps(meta).encode()

        subject.store_meta("crime-violent", "louisville-metro", meta_bytes)

        response = s3_setup.get_object(
            Bucket=self._BUCKET,
            Key="layers/crime-violent/louisville-metro/meta.json",
        )
        assert json.loads(response["Body"].read()) == meta
        assert response["ContentType"] == "application/json"
