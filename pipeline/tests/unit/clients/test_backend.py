import pytest
from pytest_httpserver import HTTPServer

from pipeline.clients.backend import BackendClient


class TestBackendClient:
    def test_list_county_fips_returns_list(self, httpserver: HTTPServer) -> None:
        httpserver.expect_request("/api/internal/counties").respond_with_json(
            {"county_fips": ["21111", "18019"]}
        )

        client = BackendClient(base_url=httpserver.url_for("").rstrip("/"))
        result = client.list_county_fips()

        assert result == ["21111", "18019"]

    def test_list_county_fips_returns_empty_when_no_counties(self, httpserver: HTTPServer) -> None:
        httpserver.expect_request("/api/internal/counties").respond_with_json(
            {"county_fips": []}
        )

        client = BackendClient(base_url=httpserver.url_for("").rstrip("/"))
        result = client.list_county_fips()

        assert result == []
