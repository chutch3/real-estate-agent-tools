import pytest
from pytest_httpserver import HTTPServer

from pipeline.indiana.flows.property_tax import indiana_property_tax_sync
from tests.indiana.taxdata import make_taxbill_zip, make_taxdata_record


def test_indiana_property_tax_sync_upserts_both_counties(
    httpserver: HTTPServer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BACKEND_URL", httpserver.url_for("").rstrip("/"))
    monkeypatch.setenv("DLGF_BASE_URL", httpserver.url_for("").rstrip("/"))

    # DLGF: GET for session page — return minimal HTML (no hidden fields needed)
    httpserver.expect_request("/public/download.aspx", method="GET").respond_with_data(
        "<html></html>", content_type="text/html"
    )
    # DLGF: POST to download zip — return same zip for both counties
    httpserver.expect_request("/public/download.aspx", method="POST").respond_with_data(
        make_taxbill_zip(make_taxdata_record("102403200259000013", 6480.00)),
        content_type="application/zip",
    )
    # Backend: receive upserts
    httpserver.expect_request("/api/internal/tax-cache", method="POST").respond_with_data("", status=204)

    indiana_property_tax_sync(year="2023")

    upsert_requests = [req for req, _ in httpserver.log if "/api/internal/tax-cache" in req.path]
    assert len(upsert_requests) == 2
    county_fips_seen = {req.get_json()["county_fips"] for req in upsert_requests}
    assert "18019" in county_fips_seen
    assert "18043" in county_fips_seen
    for req in upsert_requests:
        body = req.get_json()
        assert body["tax_year"] == 2023
        assert len(body["records"]) > 0
