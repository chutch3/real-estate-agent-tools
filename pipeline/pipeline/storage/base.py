from typing import Protocol


class LayerStorage(Protocol):
    """Protocol for storing and retrieving crime layer data."""

    def store_cog(
        self,
        layer_id: str,
        region_slug: str,
        cog_bytes: bytes,
    ) -> None:
        """Store the Cloud Optimized GeoTIFF (COG) for the specified layer and region."""
        ...

    def store_meta(
        self,
        layer_id: str,
        region_slug: str,
        meta_bytes: bytes,
    ) -> None:
        """Store the metadata JSON for the specified layer and region."""
        ...
