import json
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from backend.exceptions import LayerNotFoundError
from backend.repositories.layer import LayerRepository


class TestLayerRepository:
    @pytest.fixture
    def s3_client(self):
        return MagicMock()

    @pytest.fixture
    def subject(self, s3_client) -> LayerRepository:
        return LayerRepository(client=s3_client, bucket_name="test-bucket")

    def test_list_region_slugs_returns_fips_from_meta_keys(self, subject, s3_client):
        s3_client.get_paginator.return_value.paginate.return_value = [
            {"Contents": [{"Key": "tiles/meta/crime-violent/21111/meta.json"}]}
        ]

        result = subject.list_region_slugs("crime-violent")

        assert result == ["21111"]
        s3_client.get_paginator.return_value.paginate.assert_called_once_with(
            Bucket="test-bucket", Prefix="tiles/meta/crime-violent/"
        )

    def test_list_region_slugs_returns_empty_when_no_data(self, subject, s3_client):
        s3_client.get_paginator.return_value.paginate.return_value = [{}]

        result = subject.list_region_slugs("crime-violent")

        assert result == []

    def test_list_region_slugs_ignores_keys_without_meta_json(self, subject, s3_client):
        s3_client.get_paginator.return_value.paginate.return_value = [
            {"Contents": [{"Key": "tiles/meta/crime-violent/21111/other.json"}]}
        ]

        result = subject.list_region_slugs("crime-violent")

        assert result == []

    def test_list_region_slugs_returns_multiple_fips(self, subject, s3_client):
        s3_client.get_paginator.return_value.paginate.return_value = [
            {
                "Contents": [
                    {"Key": "tiles/meta/crime-violent/21111/meta.json"},
                    {"Key": "tiles/meta/crime-violent/18019/meta.json"},
                ]
            }
        ]

        result = subject.list_region_slugs("crime-violent")

        assert sorted(result) == ["18019", "21111"]

    def test_get_meta_returns_parsed_dict(self, subject, s3_client):
        meta = {
            "date_from": "2025-04-01",
            "date_to": "2026-04-01",
            "record_count": 42,
            "bbox": [-86.035, 37.997, -85.404, 38.375],
        }
        s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps(meta).encode())
        }

        result = subject.get_meta("crime-violent", "21111")

        assert result == meta
        s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="tiles/meta/crime-violent/21111/meta.json",
        )

    def test_get_meta_raises_layer_not_found_for_missing_key(self, subject, s3_client):
        s3_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "GetObject"
        )

        with pytest.raises(LayerNotFoundError):
            subject.get_meta("crime-violent", "unknown-fips")

    def test_has_region_returns_true_when_meta_exists(self, subject, s3_client):
        s3_client.head_object.return_value = {}

        result = subject.has_region("crime-violent", "21111")

        assert result is True
        s3_client.head_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="tiles/meta/crime-violent/21111/meta.json",
        )

    def test_has_region_returns_false_when_meta_does_not_exist(self, subject, s3_client):
        s3_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
        )

        result = subject.has_region("crime-violent", "18019")

        assert result is False

    def test_get_png_tile_returns_bytes_from_s3(self, subject, s3_client):
        png_bytes = b"\x89PNG-fake"
        s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: png_bytes)
        }

        result = subject.get_png_tile("crime-violent", z=12, x=1234, y=3456)

        assert result == png_bytes
        s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="tiles/png/crime-violent/12/1234/3456.png",
        )

    def test_get_png_tile_raises_layer_not_found_when_missing(self, subject, s3_client):
        s3_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "GetObject"
        )

        with pytest.raises(LayerNotFoundError):
            subject.get_png_tile("crime-violent", z=12, x=0, y=0)
