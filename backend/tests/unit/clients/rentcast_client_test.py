import pytest
from pytest_httpserver import HTTPServer

from backend.container import init_rentcast_client


class TestRentcastClient:
    @pytest.mark.asyncio
    async def test_uses_default_base_url_when_none_provided(self):
        client = next(init_rentcast_client(api_key="fake-key", base_url=None))
        assert client.api_client.configuration.host == "https://api.rentcast.io/v1"

    @pytest.mark.asyncio
    async def test_uses_provided_base_url(self, httpserver: HTTPServer):
        base_url = httpserver.url_for("").rstrip("/")
        client = next(init_rentcast_client(api_key="fake-key", base_url=base_url))
        assert client.api_client.configuration.host == base_url

    @pytest.mark.asyncio
    async def test_property_records_calls_configured_host(self, httpserver: HTTPServer):
        httpserver.expect_request("/properties").respond_with_json([
            {
                "id": "prop-1",
                "formattedAddress": "1600 Amphitheatre Pkwy, Mountain View, CA 94043",
                "addressLine1": "1600 Amphitheatre Pkwy",
                "city": "Mountain View",
                "state": "CA",
                "zipCode": "94043",
                "latitude": 37.4225103,
                "longitude": -122.0847089,
            }
        ])

        base_url = httpserver.url_for("").rstrip("/")
        client = next(init_rentcast_client(api_key="fake-key", base_url=base_url))
        results = await client.property_records(address="1600 Amphitheatre Pkwy, Mountain View, CA 94043")

        assert len(results) == 1
        assert results[0].id == "prop-1"
        assert results[0].formatted_address == "1600 Amphitheatre Pkwy, Mountain View, CA 94043"
