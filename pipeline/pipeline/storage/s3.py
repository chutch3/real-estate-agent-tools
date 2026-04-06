import os
from dataclasses import dataclass
from datetime import date
from typing import Any

import boto3


@dataclass
class S3TileStorage:
    """Stores crime layer tiles in an S3-compatible bucket."""

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

    def store_data_tile(
        self,
        crime_category: str,
        resolution_m: int,
        date_from: date,
        date_to: date,
        version: str,
        fips: str,
        cog_bytes: bytes,
    ) -> None:
        key = (
            f"tiles/data/{crime_category}/{resolution_m}m/"
            f"{date_from.isoformat()}/{date_to.isoformat()}/{version}/{fips}/latest.tif"
        )
        self._client().put_object(
            Bucket=self.bucket,
            Key=key,
            Body=cog_bytes,
            ContentType="image/tiff",
        )

    def store_png_tile(
        self,
        layer_id: str,
        z: int,
        x: int,
        y: int,
        png_bytes: bytes,
    ) -> None:
        key = f"tiles/png/{layer_id}/{z}/{x}/{y}.png"
        self._client().put_object(
            Bucket=self.bucket,
            Key=key,
            Body=png_bytes,
            ContentType="image/png",
        )

    def store_meta(
        self,
        layer_id: str,
        fips: str,
        meta_bytes: bytes,
    ) -> None:
        key = f"tiles/meta/{layer_id}/{fips}/meta.json"
        self._client().put_object(
            Bucket=self.bucket,
            Key=key,
            Body=meta_bytes,
            ContentType="application/json",
        )
