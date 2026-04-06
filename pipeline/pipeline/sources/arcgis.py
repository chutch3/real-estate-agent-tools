import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime

import geopandas as gpd
import httpx
from shapely.geometry import Polygon

_logger = logging.getLogger(__name__)

_VIOLENT_PREFIXES = frozenset(
    [
        "MURDER",
        "MANSLAUGHTER",
        "RAPE",
        "SODOMY",
        "SEX",
        "ROBBERY",
        "ASSAULT",
        "INTIMIDATION",
        "KIDNAP",
        "HUMAN TRAFFICKING",
    ]
)
_PROPERTY_PREFIXES = frozenset(
    [
        "ARSON",
        "BURGLARY",
        "LARCENY",
        "THEFT",
        "MOTOR VEHICLE",
        "VANDALISM",
        "DESTRUCTION",
        "EMBEZZLEMENT",
        "FRAUD",
        "COUNTERFEITING",
        "STOLEN",
    ]
)


def _map_nibrs_category(offense_classification: str | None) -> str:
    if not offense_classification:
        return "other"
    parts = offense_classification.upper().strip().split(None, 1)
    if len(parts) < 2:
        return "other"
    offense = parts[1]
    for prefix in _VIOLENT_PREFIXES:
        if prefix in offense:
            return "violent"
    for prefix in _PROPERTY_PREFIXES:
        if prefix in offense:
            return "property"
    return "other"


@dataclass
class ArcGISFeatureSource:
    """Fetches crime incident data from an ArcGIS FeatureServer layer."""

    name: str
    service_url: str
    date_field: str
    category_field: str
    address_field: str
    city_field: str
    zip_field: str
    state_code: str
    page_size: int = 2000

    def _endpoint(self) -> str:
        return f"{self.service_url}/query"

    def fetch(
        self,
        polygon: Polygon,
        date_from: date,
        date_to: date,
    ) -> gpd.GeoDataFrame:
        where = (
            f"{self.date_field} >= timestamp '{date_from.isoformat()} 00:00:00'"
            f" AND {self.date_field} <= timestamp '{date_to.isoformat()} 23:59:59'"
        )
        out_fields = ",".join(
            [
                self.date_field,
                self.category_field,
                self.address_field,
                self.city_field,
                self.zip_field,
            ]
        )

        records = []
        skipped = 0
        offset = 0

        while True:
            params = {
                "where": where,
                "outFields": out_fields,
                "returnGeometry": "false",
                "f": "json",
                "resultRecordCount": self.page_size,
                "resultOffset": offset,
            }
            response = httpx.get(self._endpoint(), params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            features = data.get("features", [])
            if not features:
                break

            for feat in features:
                attrs = feat.get("attributes", {})
                try:
                    date_ms = attrs[self.date_field]
                    date_str = (
                        datetime.fromtimestamp(date_ms / 1000, tz=UTC).strftime("%Y-%m-%d")
                        if date_ms is not None
                        else ""
                    )
                    records.append(
                        {
                            "lat": None,
                            "lon": None,
                            "category": _map_nibrs_category(attrs.get(self.category_field, "")),
                            "date": date_str,
                            "source": self.name,
                            "address": attrs.get(self.address_field, ""),
                            "city": attrs.get(self.city_field, ""),
                            "zip_code": attrs.get(self.zip_field, ""),
                            "state": self.state_code,
                            "geometry": None,
                        }
                    )
                except (KeyError, TypeError, ValueError):
                    skipped += 1

            offset += len(features)
            if not data.get("exceededTransferLimit", False):
                break

        if skipped:
            _logger.warning(
                "Skipped %d records from %s due to missing or invalid fields",
                skipped,
                self.name,
            )

        if not records:
            return gpd.GeoDataFrame(
                columns=[
                    "lat",
                    "lon",
                    "category",
                    "date",
                    "source",
                    "address",
                    "city",
                    "zip_code",
                    "state",
                    "geometry",
                ],
                geometry="geometry",
                crs="EPSG:4326",
            )

        return gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
