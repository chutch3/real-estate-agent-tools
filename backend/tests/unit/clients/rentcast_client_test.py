import pytest
import pytest_asyncio
from pytest_httpserver import HTTPServer

from rentcast_client.api.default_rentcast import DefaultRentcast
from rentcast_client.api_client import ApiClient
from rentcast_client.configuration import Configuration


class TestRentcastClient:
    @pytest.mark.asyncio
    async def test_defaults_to_rentcast_api_host(self, default_subject: DefaultRentcast):
        assert default_subject.api_client.configuration.host == "https://api.rentcast.io/v1"

    @pytest.mark.asyncio
    async def test_property_records_calls_configured_host(self, subject: DefaultRentcast, httpserver: HTTPServer):
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

        results = await subject.property_records(address="1600 Amphitheatre Pkwy, Mountain View, CA 94043")

        assert len(results) == 1
        assert results[0].id == "prop-1"
        assert results[0].formatted_address == "1600 Amphitheatre Pkwy, Mountain View, CA 94043"

    @pytest_asyncio.fixture
    async def default_subject(self) -> DefaultRentcast:
        api_client = ApiClient(
            configuration=Configuration(),
            header_name="X-Api-Key",
            header_value="fake-key",
        )
        yield DefaultRentcast(api_client=api_client)
        await api_client.close()

    @pytest_asyncio.fixture
    async def subject(self, httpserver: HTTPServer) -> DefaultRentcast:
        base_url = httpserver.url_for("").rstrip("/")
        api_client = ApiClient(
            configuration=Configuration(host=base_url),
            header_name="X-Api-Key",
            header_value="fake-key",
        )
        yield DefaultRentcast(api_client=api_client)
        await api_client.close()
