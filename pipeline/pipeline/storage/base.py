from datetime import date
from typing import Protocol


class TileStorage(Protocol):
    """Protocol for storing crime layer tiles and metadata."""

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
        """Store the COG data tile for the given category, date range, and FIPS."""
        ...

    def store_png_tile(
        self,
        layer_id: str,
        z: int,
        x: int,
        y: int,
        png_bytes: bytes,
    ) -> None:
        """Store a pre-rendered PNG tile."""
        ...

    def store_meta(
        self,
        layer_id: str,
        fips: str,
        meta_bytes: bytes,
    ) -> None:
        """Store the metadata JSON for the given layer and FIPS."""
        ...
