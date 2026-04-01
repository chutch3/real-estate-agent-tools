import logging
from dataclasses import dataclass
from datetime import date

import geopandas as gpd
import httpx
from shapely.geometry import Point, Polygon

_logger = logging.getLogger(__name__)

_VIOLENT_OFFENSES = frozenset(
    [
        "ASSAULT",
        "HOMICIDE",
        "RAPE",
        "ROBBERY",
        "ASSAULT 4TH DEGREE",
        "ASSAULT - FELONY",
        "ASSAULT - MISDEMEANOR",
    ]
)
_PROPERTY_OFFENSES = frozenset(
    [
        "BURGLARY",
        "THEFT",
        "MOTOR VEHICLE THEFT",
        "VANDALISM/CRIMINAL MISCHIEF",
        "ARSON",
    ]
)


def _map_category(offense: str) -> str:
    upper = offense.upper().strip()
    for prefix in _VIOLENT_OFFENSES:
        if upper.startswith(prefix):
            return "violent"
    for prefix in _PROPERTY_OFFENSES:
        if upper.startswith(prefix):
            return "property"
    return "other"


@dataclass
class SocrataSource:
    """Fetches crime incident data from a Socrata open data portal."""

    name: str
    dataset_id: str
    date_field: str
    lat_field: str
    lon_field: str
    category_field: str
    base_url: str
    app_token: str | None = None

    def _endpoint(self) -> str:
        return f"{self.base_url}/resource/{self.dataset_id}.json"

    def fetch(
        self,
        polygon: Polygon,
        date_from: date,
        date_to: date,
    ) -> gpd.GeoDataFrame:
        minx, miny, maxx, maxy = polygon.bounds
        where = (
            f"{self.date_field} >= '{date_from}T00:00:00.000'"
            f" AND {self.date_field} <= '{date_to}T23:59:59.999'"
            f" AND {self.lat_field} >= '{miny}' AND {self.lat_field} <= '{maxy}'"
            f" AND {self.lon_field} >= '{minx}' AND {self.lon_field} <= '{maxx}'"
        )
        params = {"$where": where, "$limit": "50000"}
        headers = {}
        if self.app_token:
            headers["X-App-Token"] = self.app_token

        response = httpx.get(self._endpoint(), params=params, headers=headers)
        response.raise_for_status()
        rows = response.json()

        records = []
        skipped = 0
        for row in rows:
            try:
                lat = float(row[self.lat_field])
                lon = float(row[self.lon_field])
                raw_date = row.get(self.date_field, "")[:10]
                category = _map_category(row.get(self.category_field, ""))
                records.append(
                    {
                        "lat": lat,
                        "lon": lon,
                        "category": category,
                        "date": raw_date,
                        "source": self.name,
                        "geometry": Point(lon, lat),
                    }
                )
            except (KeyError, ValueError):
                skipped += 1

        if skipped:
            _logger.warning(
                "Skipped %d of %d rows from %s due to missing or invalid coordinates",
                skipped,
                len(rows),
                self.name,
            )

        if not records:
            return gpd.GeoDataFrame(
                columns=["lat", "lon", "category", "date", "source", "geometry"],
                geometry="geometry",
                crs="EPSG:4326",
            )

        return gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
