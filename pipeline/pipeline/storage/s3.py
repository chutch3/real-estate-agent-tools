import os
from dataclasses import dataclass
from typing import Any

import boto3


@dataclass
class S3LayerStorage:
    """Stores layers in an S3-compatible bucket."""

    bucket: str
    endpoint_url: str | None = None
    access_key: str | None = None
    secret_key: str | None = None
    region_name: str | None = None

    def _client(self) -> Any:
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url or os.environ.get("AWS_ENDPOINT_URL_S3"),
            aws_access_key_id=self.access_key or os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=self.secret_key or os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=self.region_name or os.environ.get("AWS_DEFAULT_REGION"),
        )

    def store_cog(
        self,
        layer_id: str,
        region_slug: str,
        cog_bytes: bytes,
    ) -> None:
        client = self._client()
        key = f"layers/{layer_id}/{region_slug}/latest.tif"
        client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=cog_bytes,
            ContentType="image/tiff",
        )

    def store_meta(
        self,
        layer_id: str,
        region_slug: str,
        meta_bytes: bytes,
    ) -> None:
        client = self._client()
        key = f"layers/{layer_id}/{region_slug}/meta.json"
        client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=meta_bytes,
            ContentType="application/json",
        )
