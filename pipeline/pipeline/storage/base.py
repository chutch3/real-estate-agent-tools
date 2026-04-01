from typing import Protocol


class LayerStorage(Protocol):
    """Protocol for storing and retrieving crime layer data."""

    def store_cog(
        self,
        region_slug: str,
        cog_bytes: bytes,
    ) -> None:
        """Store the Cloud Optimized GeoTIFF (COG) for the specified region."""
        ...

    def store_meta(
        self,
        region_slug: str,
        meta_bytes: bytes,
    ) -> None:
        """Store the metadata JSON for the specified region."""
        ...
