import logging
from typing import Optional

import aiohttp


class TigerWebClient:
    def __init__(self, base_url: str = "https://tigerweb.geo.census.gov") -> None:
        self._base_url = base_url
        self._logger = logging.getLogger(self.__class__.__name__)

    async def get_county_polygon(self, county_fips: str) -> Optional[dict]:
        url = f"{self._base_url}/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query"
        params = {
            "f": "json",
            "where": f"GEOID LIKE '{county_fips}%'",
            "returnGeometry": "true",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "orderByFields": "BASENAME",
            "resultRecordCount": 1,
            "outSR": 4326,
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()

        features = data.get("features", [])
        if not features:
            return None

        rings = features[0]["geometry"]["rings"]
        return {"type": "Polygon", "coordinates": rings}
