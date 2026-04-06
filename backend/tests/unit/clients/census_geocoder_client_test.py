import pytest
from pytest_httpserver import HTTPServer

from backend.clients.census_geocoder import CensusGeocoderClient


class TestCensusGeocoderClient:
    @pytest.mark.asyncio
    async def test_get_county_fips_returns_geoid(self, httpserver: HTTPServer):
        httpserver.expect_request("/geocoder/geographies/coordinates").respond_with_json(
            {"result": {"geographies": {"Counties": [{"GEOID": "21111", "NAME": "Jefferson"}]}}}
        )

        client = CensusGeocoderClient(base_url=httpserver.url_for("").rstrip("/"))
        result = await client.get_county_fips(38.2, -85.7)

        assert result == "21111"

    @pytest.mark.asyncio
    async def test_get_county_fips_returns_none_when_no_counties(self, httpserver: HTTPServer):
        httpserver.expect_request("/geocoder/geographies/coordinates").respond_with_json(
            {"result": {"geographies": {"Counties": []}}}
        )

        client = CensusGeocoderClient(base_url=httpserver.url_for("").rstrip("/"))
        result = await client.get_county_fips(0.0, 0.0)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_county_fips_returns_none_when_geographies_missing(self, httpserver: HTTPServer):
        httpserver.expect_request("/geocoder/geographies/coordinates").respond_with_json(
            {"result": {"geographies": {}}}
        )

        client = CensusGeocoderClient(base_url=httpserver.url_for("").rstrip("/"))
        result = await client.get_county_fips(0.0, 0.0)

        assert result is None
