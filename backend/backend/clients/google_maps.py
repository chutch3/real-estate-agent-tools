import aiohttp

from backend.exceptions import AddressNotFoundError
from backend.models import GeocodeLocation


class GoogleMapsClient:
    def __init__(self, api_key: str, base_url: str = "https://maps.googleapis.com"):
        self.api_key = api_key
        self._base_url = base_url

    async def geocode(self, address: str) -> GeocodeLocation:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self._base_url}/maps/api/geocode/json",
                params={"address": address, "key": self.api_key},
            ) as response:
                response.raise_for_status()
                data = await response.json()
                if data["results"]:
                    location = data["results"][0]["geometry"]["location"]
                    return GeocodeLocation(lat=location["lat"], lng=location["lng"])
                else:
                    raise AddressNotFoundError()
