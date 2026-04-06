import logging

import aiohttp


class CensusGeocoderClient:
    def __init__(self, base_url: str = "https://geocoding.geo.census.gov") -> None:
        self._base_url = base_url
        self._logger = logging.getLogger(self.__class__.__name__)

    async def get_county_fips(self, lat: float, lon: float) -> str | None:
        url = f"{self._base_url}/geocoder/geographies/coordinates"
        params = {
            "x": lon,
            "y": lat,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "layers": "Counties",
            "format": "json",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()

        counties = data.get("result", {}).get("geographies", {}).get("Counties", [])
        if not counties:
            return None
        return counties[0]["GEOID"]
