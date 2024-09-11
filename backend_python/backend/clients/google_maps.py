import aiohttp

from backend.exceptions import AddressNotFoundError
from backend.models import GeocodeLocation


class GoogleMapsClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def geocode(self, address: str) -> GeocodeLocation:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": address, "key": self.api_key},
            ) as response:
                response.raise_for_status()
                data = await response.json()
                if data["results"]:
                    location = data["results"][0]["geometry"]["location"]
                    return GeocodeLocation(
                        latitude=location["lat"], longitude=location["lng"]
                    )
                else:
                    raise AddressNotFoundError()
