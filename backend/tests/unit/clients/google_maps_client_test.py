import pytest
from pytest_httpserver import HTTPServer

from backend.clients.google_maps import GoogleMapsClient
from backend.exceptions import AddressNotFoundError
from backend.models import GeocodeLocation


class TestGoogleMapsClient:
    @pytest.mark.asyncio
    async def test_geocode_returns_location(self, httpserver: HTTPServer):
        httpserver.expect_request("/maps/api/geocode/json").respond_with_json(
            {"results": [{"geometry": {"location": {"lat": 37.4225, "lng": -122.0847}}}]}
        )

        client = GoogleMapsClient(api_key="fake-key", base_url=httpserver.url_for("").rstrip("/"))
        result = await client.geocode("1600 Amphitheatre Pkwy")

        assert result == GeocodeLocation(lat=37.4225, lng=-122.0847)

    @pytest.mark.asyncio
    async def test_geocode_raises_when_no_results(self, httpserver: HTTPServer):
        httpserver.expect_request("/maps/api/geocode/json").respond_with_json({"results": []})

        client = GoogleMapsClient(api_key="fake-key", base_url=httpserver.url_for("").rstrip("/"))

        with pytest.raises(AddressNotFoundError):
            await client.geocode("nowhere")
