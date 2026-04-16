import httpx
import pytest
from pytest_httpserver import HTTPServer

from pipeline.clients.backend import BackendClient


class TestBackendClient:
    def test_list_county_fips_returns_list(self, subject: BackendClient, httpserver: HTTPServer) -> None:
        httpserver.expect_request("/api/internal/counties").respond_with_json({"county_fips": ["21111", "18019"]})

        result = subject.list_county_fips()

        assert result == ["21111", "18019"]

    def test_list_county_fips_returns_empty_when_no_counties(
        self, subject: BackendClient, httpserver: HTTPServer
    ) -> None:
        httpserver.expect_request("/api/internal/counties").respond_with_json({"county_fips": []})

        result = subject.list_county_fips()

        assert result == []

    def test_upsert_tax_cache_posts_correct_body(self, subject: BackendClient, httpserver: HTTPServer) -> None:
        httpserver.expect_request("/api/internal/tax-cache", method="POST").respond_with_data("", status=204)
        records = [{"state_parcel_id": "102403200259000013", "net_tax_amount": 6480.00}]

        subject.upsert_tax_cache(records=records, county_fips="18019", tax_year=2023)

        request, _ = httpserver.log[-1]
        body = request.get_json()
        assert body["county_fips"] == "18019"
        assert body["tax_year"] == 2023
        assert body["records"] == records

    def test_upsert_tax_cache_raises_on_server_error(self, subject: BackendClient, httpserver: HTTPServer) -> None:
        httpserver.expect_request("/api/internal/tax-cache", method="POST").respond_with_data("", status=500)

        with pytest.raises(httpx.HTTPStatusError):
            subject.upsert_tax_cache(
                records=[{"state_parcel_id": "102403200259000013", "net_tax_amount": 6480.00}],
                county_fips="18019",
                tax_year=2023,
            )

    @pytest.fixture
    def subject(self, httpserver: HTTPServer) -> BackendClient:
        return BackendClient(base_url=httpserver.url_for("").rstrip("/"))
