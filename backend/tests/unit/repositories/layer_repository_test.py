import json
from unittest.mock import MagicMock

import pytest

from backend.exceptions import LayerNotFoundError
from backend.repositories.layer import LayerRepository


class TestLayerRepository:
    @pytest.fixture
    def s3_client(self):
        return MagicMock()

    @pytest.fixture
    def subject(self, s3_client) -> LayerRepository:
        return LayerRepository(client=s3_client, bucket_name="test-bucket")

    def test_list_region_slugs_returns_slugs_with_latest_tif(self, subject, s3_client):
        s3_client.get_paginator.return_value.paginate.return_value = [
            {"Contents": [{"Key": "layers/crime-violent/louisville-metro/latest.tif"}]}
        ]

        result = subject.list_region_slugs("crime-violent")

        assert result == ["louisville-metro"]
        s3_client.get_paginator.return_value.paginate.assert_called_once_with(
            Bucket="test-bucket", Prefix="layers/crime-violent/"
        )

    def test_list_region_slugs_returns_empty_when_no_data(self, subject, s3_client):
        s3_client.get_paginator.return_value.paginate.return_value = [{}]

        result = subject.list_region_slugs("crime-violent")

        assert result == []

    def test_list_region_slugs_ignores_keys_without_latest_tif(self, subject, s3_client):
        s3_client.get_paginator.return_value.paginate.return_value = [
            {"Contents": [{"Key": "layers/crime-violent/louisville-metro/meta.json"}]}
        ]

        result = subject.list_region_slugs("crime-violent")

        assert result == []

    def test_list_region_slugs_returns_multiple_regions(self, subject, s3_client):
        s3_client.get_paginator.return_value.paginate.return_value = [
            {
                "Contents": [
                    {"Key": "layers/crime-violent/louisville-metro/latest.tif"},
                    {"Key": "layers/crime-violent/clark-county-in/latest.tif"},
                ]
            }
        ]

        result = subject.list_region_slugs("crime-violent")

        assert sorted(result) == ["clark-county-in", "louisville-metro"]

    def test_get_meta_returns_parsed_dict(self, subject, s3_client):
        meta = {
            "region_slug": "louisville-metro",
            "date_from": "2025-04-01",
            "date_to": "2026-04-01",
            "record_count": 42,
            "bbox": [-86.035, 37.997, -85.404, 38.375],
        }
        s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps(meta).encode())
        }

        result = subject.get_meta("crime-violent", "louisville-metro")

        assert result == meta
        s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="layers/crime-violent/louisville-metro/meta.json",
        )

    def test_get_meta_raises_layer_not_found_for_missing_key(self, subject, s3_client):
        from botocore.exceptions import ClientError

        s3_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "GetObject"
        )

        with pytest.raises(LayerNotFoundError):
            subject.get_meta("crime-violent", "unknown-region")

    def test_has_region_returns_true_when_latest_tif_exists(self, subject, s3_client):
        s3_client.head_object.return_value = {}

        result = subject.has_region("crime-violent", "21111")

        assert result is True
        s3_client.head_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="layers/crime-violent/21111/latest.tif",
        )

    def test_has_region_returns_false_when_latest_tif_does_not_exist(self, subject, s3_client):
        from botocore.exceptions import ClientError

        s3_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
        )

        result = subject.has_region("crime-violent", "18019")

        assert result is False
