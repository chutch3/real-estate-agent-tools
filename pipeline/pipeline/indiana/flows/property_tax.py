"""
Indiana DLGF property tax bulk ETL.

Downloads the Tax Bill (TAXDATA) file for each supported Indiana county from
the Indiana Gateway public download portal, extracts the net annual tax amount
per parcel, and upserts the results into the backend's property_tax_cache table
via the internal API.

Usage (Prefect flow):
    prefect run pipeline/indiana/flows/property_tax.py

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
from pipeline.indiana.clients.dlgf import DLGFClient
from pipeline.indiana.tax.parser import parse_taxbill_record

_logger = logging.getLogger(__name__)

_COUNTY_CONFIG: dict[str, dict] = {
    "18019": {"county_num": "10", "name": "Clark"},
    "18043": {"county_num": "22", "name": "Floyd"},
}


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
        parsed = parse_taxbill_record(line)
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
