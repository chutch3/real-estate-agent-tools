from datetime import date
from typing import Protocol

import geopandas as gpd
from shapely.geometry import Polygon


class Source(Protocol):
    """Protocol that all crime data sources must implement."""

    name: str

    def fetch(
        self,
        polygon: Polygon,
        date_from: date,
        date_to: date,
    ) -> gpd.GeoDataFrame:
        """Fetch crime incidents within the polygon and date range.

        Returns a GeoDataFrame with columns: lat, lon, category, date, source.
        The GeoDataFrame must have a geometry column in EPSG:4326.
        """
        ...
