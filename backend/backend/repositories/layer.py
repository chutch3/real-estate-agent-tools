import json
import logging

from botocore.exceptions import ClientError

from backend.exceptions import LayerNotFoundError


class LayerRepository:
    def __init__(self, client, bucket_name: str) -> None:
        self._client = client
        self._bucket_name = bucket_name
        self._logger = logging.getLogger(self.__class__.__name__)

    def list_region_slugs(self, layer_id: str) -> list[str]:
        paginator = self._client.get_paginator("list_objects_v2")
        slugs = []
        for page in paginator.paginate(Bucket=self._bucket_name, Prefix=f"tiles/meta/{layer_id}/"):
            for obj in page.get("Contents", []):
                parts = obj["Key"].split("/")
                # tiles/meta/{layer_id}/{fips}/meta.json → 5 parts, last is meta.json
                if len(parts) == 5 and parts[4] == "meta.json":
                    slugs.append(parts[3])
        self._logger.info("Discovered %d region(s) for layer %s: %s", len(slugs), layer_id, slugs)
        return slugs

    def has_region(self, layer_id: str, region_slug: str) -> bool:
        try:
            self._client.head_object(
                Bucket=self._bucket_name,
                Key=f"tiles/meta/{layer_id}/{region_slug}/meta.json",
            )
            return True
        except ClientError:
            return False

    def get_meta(self, layer_id: str, region_slug: str) -> dict:
        try:
            response = self._client.get_object(
                Bucket=self._bucket_name,
                Key=f"tiles/meta/{layer_id}/{region_slug}/meta.json",
            )
            return json.loads(response["Body"].read())
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                raise LayerNotFoundError(
                    f"Metadata not found for layer {layer_id!r}, region {region_slug!r}"
                )
            raise

    def get_png_tile(self, layer_id: str, z: int, x: int, y: int) -> bytes:
        try:
            response = self._client.get_object(
                Bucket=self._bucket_name,
                Key=f"tiles/png/{layer_id}/{z}/{x}/{y}.png",
            )
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                raise LayerNotFoundError(
                    f"PNG tile not found for layer {layer_id!r} at z={z}, x={x}, y={y}"
                )
            raise
