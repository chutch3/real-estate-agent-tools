from unittest.mock import MagicMock

import pytest

from pipeline.clients.backend import BackendClient
from pipeline.clients.dlgf import DLGFClient
from pipeline.flows.indiana_tax import (
    _parse_taxbill_record,
    download_taxbill,
    upsert_tax_cache,
)
from tests.taxdata import make_taxbill_zip, make_taxdata_record


@pytest.fixture
def dlgf_client() -> MagicMock:
    return MagicMock(spec=DLGFClient)


@pytest.fixture
def backend_client() -> MagicMock:
    return MagicMock(spec=BackendClient)


# ── _parse_taxbill_record ──────────────────────────────────────────────────────


def test_parse_taxbill_record_extracts_parcel_id_and_net_tax():
    record = make_taxdata_record("102403200259000013", 6480.00)

    result = _parse_taxbill_record(record)

    assert result is not None
    assert result["state_parcel_id"] == "102403200259000013"
    assert result["net_tax_amount"] == pytest.approx(6480.00)


def test_parse_taxbill_record_applies_format_12_2_implied_decimal():
    # 50 IAC 26-20-2(a)(6): "All decimal precision is implied."
    # Format 12.2 means no decimal point in the file; divide by 100 to get dollars.
    # "Total Property Tax Due This Tax Year" (cols 737-750, offset 736, Format 12.2)
    # $4,407.00 is stored as "00000000440700" — NOT $440,700.
    record = bytearray(b" " * 779)
    record[0:18] = b"101903501334000009"
    record[736:750] = b"00000000440700"

    result = _parse_taxbill_record(bytes(record))

    assert result is not None
    assert result["state_parcel_id"] == "101903501334000009"
    assert result["net_tax_amount"] == pytest.approx(4407.00)


def test_parse_taxbill_record_handles_legacy_decimal_format():
    # Older TAXDATA files (e.g. 2023 pay 2024) stored values with a literal decimal
    # point rather than Format 12.2. The parser must not double-divide by 100.
    record = bytearray(b" " * 778)
    record[0:18] = b"102403200259000013"
    record[736:750] = b"00000000318.40"  # literal decimal — already in dollars

    result = _parse_taxbill_record(bytes(record))

    assert result is not None
    assert result["net_tax_amount"] == pytest.approx(318.40)


def test_parse_taxbill_record_returns_none_for_zero_net_tax():
    record = make_taxdata_record("102403200259000013", 0.0)

    result = _parse_taxbill_record(record)

    assert result is None


def test_parse_taxbill_record_returns_none_for_blank_parcel_id():
    record = make_taxdata_record("", 1234.56)

    result = _parse_taxbill_record(record)

    assert result is None


# ── download_taxbill ───────────────────────────────────────────────────────────


def test_download_taxbill_parses_records_from_zip(dlgf_client: MagicMock):
    dlgf_client.fetch_taxbill_zip.return_value = make_taxbill_zip(
        make_taxdata_record("102403200259000013", 6480.00),
        make_taxdata_record("102403200259000014", 0.00),  # zero → excluded
        make_taxdata_record("102403200259000015", 1200.00),
        filename="TaxBill_Clark.txt",
    )

    result = download_taxbill(county_num="10", year="2023", dlgf_client=dlgf_client)

    assert len(result) == 2
    record_by_id = {r["state_parcel_id"]: r for r in result}
    assert record_by_id["102403200259000013"]["net_tax_amount"] == pytest.approx(6480.00)
    assert record_by_id["102403200259000015"]["net_tax_amount"] == pytest.approx(1200.00)


def test_download_taxbill_fetches_with_correct_county_and_year(dlgf_client: MagicMock):
    dlgf_client.fetch_taxbill_zip.return_value = make_taxbill_zip()

    download_taxbill(county_num="22", year="2024", dlgf_client=dlgf_client)

    dlgf_client.fetch_taxbill_zip.assert_called_once_with(county_num="22", year="2024")


# ── upsert_tax_cache ───────────────────────────────────────────────────────────


def test_upsert_tax_cache_posts_records_to_backend(backend_client: MagicMock):
    records = [
        {"state_parcel_id": "102403200259000013", "net_tax_amount": 6480.00},
        {"state_parcel_id": "102403200259000015", "net_tax_amount": 1200.00},
    ]

    upsert_tax_cache(records=records, county_fips="18019", tax_year=2023, backend_client=backend_client)

    backend_client.upsert_tax_cache.assert_called_once_with(records=records, county_fips="18019", tax_year=2023)


def test_upsert_tax_cache_skips_empty_records(backend_client: MagicMock):
    upsert_tax_cache(records=[], county_fips="18019", tax_year=2023, backend_client=backend_client)

    backend_client.upsert_tax_cache.assert_not_called()
