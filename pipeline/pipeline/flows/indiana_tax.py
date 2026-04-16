"""
Indiana DLGF property tax bulk ETL.

Downloads the Tax Bill (TAXDATA) file for each supported Indiana county from
the Indiana Gateway public download portal, extracts the net annual tax amount
per parcel, and upserts the results into the backend's property_tax_cache table
via the internal API.

Usage (Prefect flow):
    prefect run pipeline/flows/indiana_tax.py

Environment variables:
    BACKEND_URL   - Base URL of the real-estate-agent backend (e.g. http://localhost:5000)
    DLGF_BASE_URL - Base URL of the Indiana Gateway (default: https://gateway.ifionline.org)

Supported counties (Gateway form code → FIPS):
    Clark County  → county_num=10, county_fips=18019
    Floyd County  → county_num=22, county_fips=18043
"""

import io
import logging
import os
import zipfile
from datetime import date

from prefect import flow, task
from prefect.cache_policies import NO_CACHE

from pipeline.clients.backend import BackendClient
from pipeline.clients.dlgf import DLGFClient

_logger = logging.getLogger(__name__)

# ── Fixed-width field layout for the 778-char TAXDATA record ──────────────────
# Confirmed by downloading Clark County 2023 pay 2024 data and cross-validating
# net_tax = gross_tax − circuit_breaker_credit against known parcel values.
TAXDATA_PARCEL_ID_START = 0
TAXDATA_PARCEL_ID_WIDTH = 18  # 18-digit state parcel number (matches ArcGIS state_parcel_id)
TAXDATA_NET_TAX_START = 736
TAXDATA_NET_TAX_WIDTH = (
    14  # "Total Property Tax Due This Tax Year" per 50 IAC 26-20-8, Format 12.2 (implied 2 decimal places)
)

_COUNTY_CONFIG: dict[str, dict] = {
    "18019": {"county_num": "10", "name": "Clark"},
    "18043": {"county_num": "22", "name": "Floyd"},
}


def _parse_taxbill_record(record: bytes) -> dict | None:
    """Extract state_parcel_id and net_tax_amount from one fixed-width record.

    Returns None for records with a blank parcel ID or zero net tax (exempt/industrial).
    """
    if len(record) < TAXDATA_NET_TAX_START + TAXDATA_NET_TAX_WIDTH:
        return None
    state_parcel_id = (
        record[TAXDATA_PARCEL_ID_START : TAXDATA_PARCEL_ID_START + TAXDATA_PARCEL_ID_WIDTH].decode("latin-1").strip()
    )
    if not state_parcel_id:
        return None
    net_tax_raw = (
        record[TAXDATA_NET_TAX_START : TAXDATA_NET_TAX_START + TAXDATA_NET_TAX_WIDTH].decode("latin-1").strip()
    )
    try:
        if "." in net_tax_raw:
            net_tax_amount = float(net_tax_raw)  # old format: literal decimal, already in dollars
        else:
            net_tax_amount = float(net_tax_raw) / 100.0  # Format 12.2: implied decimal (50 IAC 26-20-2(a)(6))
    except ValueError:
        return None
    if net_tax_amount <= 0:
        return None
    return {"state_parcel_id": state_parcel_id, "net_tax_amount": net_tax_amount}


@task(cache_policy=NO_CACHE, retries=2, retry_delay_seconds=30)
def download_taxbill(*, county_num: str, year: str, dlgf_client: DLGFClient) -> list[dict]:
    """Download and parse the TAXDATA zip for one county and pay year.

    Returns a list of {state_parcel_id, net_tax_amount} dicts (zeros excluded).
    """
    _logger.info("Downloading Tax Bill for county=%s year=%s", county_num, year)
    zip_bytes = dlgf_client.fetch_taxbill_zip(county_num=county_num, year=year)
    buf = io.BytesIO(zip_bytes)
    records: list[dict] = []
    with zipfile.ZipFile(buf) as zf:
        txt_name = next(n for n in zf.namelist() if n.endswith(".txt"))
        with zf.open(txt_name) as f:
            raw = f.read()
    lines = raw.split(b"\r\n")
    for line in lines[1:]:  # skip header record
        if not line.strip():
            continue
        parsed = _parse_taxbill_record(line)
        if parsed:
            records.append(parsed)
    _logger.info("Parsed %d taxable parcels for county=%s year=%s", len(records), county_num, year)
    return records


@task(cache_policy=NO_CACHE)
def upsert_tax_cache(
    *,
    records: list[dict],
    county_fips: str,
    tax_year: int,
    backend_client: BackendClient,
) -> None:
    """Upsert parsed tax records into the backend property_tax_cache via internal API."""
    if not records:
        _logger.info("No records to upsert for county_fips=%s tax_year=%s", county_fips, tax_year)
        return
    _logger.info("Upserting %d records for county_fips=%s tax_year=%s", len(records), county_fips, tax_year)
    backend_client.upsert_tax_cache(records=records, county_fips=county_fips, tax_year=tax_year)


@flow(name="indiana-property-tax-sync")
def indiana_property_tax_sync(year: str | None = None) -> None:
    """Download DLGF Tax Bill data for Clark and Floyd counties and sync to the backend.

    Args:
        year: Assessment year string (e.g. "2023" = 2023 pay 2024).
              Defaults to two years prior to today (Indiana taxes billed in arrears).
    """
    if year is None:
        year = str(date.today().year - 2)

    backend_url = os.environ["BACKEND_URL"]
    dlgf_base_url = os.environ.get("DLGF_BASE_URL", "https://gateway.ifionline.org")
    backend_client = BackendClient(base_url=backend_url)
    dlgf_client = DLGFClient(base_url=dlgf_base_url)

    for county_fips, config in _COUNTY_CONFIG.items():
        records = download_taxbill(county_num=config["county_num"], year=year, dlgf_client=dlgf_client)
        upsert_tax_cache(
            records=records,
            county_fips=county_fips,
            tax_year=int(year),
            backend_client=backend_client,
        )
