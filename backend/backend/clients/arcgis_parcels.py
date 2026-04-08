import logging

import aiohttp


class ArcGISParcelsClient:
    def __init__(
        self,
        base_url: str = "https://gisdata.in.gov/server/rest/services/Hosted/Parcel_Boundaries_of_Indiana_Current/FeatureServer/0",
    ) -> None:
        self._base_url = base_url
        self._logger = logging.getLogger(self.__class__.__name__)

    async def get_parcel(self, lat: float, lon: float) -> dict | None:
        url = f"{self._base_url}/query"
        params = {
            "geometry": f"{lon},{lat}",
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "nguid",
            "returnGeometry": "true",
            "f": "geojson",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()

        features = data.get("features", [])
        if not features:
            return None

        feature = features[0]
        return {
            "nguid": feature["properties"]["nguid"],
            "geometry": feature["geometry"],
        }
