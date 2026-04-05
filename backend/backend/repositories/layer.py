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
        for page in paginator.paginate(Bucket=self._bucket_name, Prefix=f"layers/{layer_id}/"):
            for obj in page.get("Contents", []):
                parts = obj["Key"].split("/")
                if len(parts) == 4 and parts[3] == "latest.tif":
                    slugs.append(parts[2])
        self._logger.info("Discovered %d region(s) for layer %s: %s", len(slugs), layer_id, slugs)
        return slugs

    def has_region(self, layer_id: str, region_slug: str) -> bool:
        try:
            self._client.head_object(
                Bucket=self._bucket_name,
                Key=f"layers/{layer_id}/{region_slug}/latest.tif",
            )
            return True
        except ClientError:
            return False

    def get_meta(self, layer_id: str, region_slug: str) -> dict:
        try:
            response = self._client.get_object(
                Bucket=self._bucket_name,
                Key=f"layers/{layer_id}/{region_slug}/meta.json",
            )
            return json.loads(response["Body"].read())
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                raise LayerNotFoundError(
                    f"Metadata not found for layer {layer_id!r}, region {region_slug!r}"
                )
            raise
