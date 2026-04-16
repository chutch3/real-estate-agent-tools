# Fixed-width field layout for the TAXDATA record (50 IAC 26-20-8)
# Confirmed by downloading Clark County 2023 pay 2024 data and cross-validating
# net_tax = gross_tax − circuit_breaker_credit against known parcel values.
TAXDATA_PARCEL_ID_START = 0
TAXDATA_PARCEL_ID_WIDTH = 18  # 18-digit state parcel number (matches ArcGIS state_parcel_id)
TAXDATA_NET_TAX_START = 736
TAXDATA_NET_TAX_WIDTH = (
    14  # "Total Property Tax Due This Tax Year" per 50 IAC 26-20-8, Format 12.2 (implied 2 decimal places)
)


def parse_taxbill_record(record: bytes) -> dict | None:
    """Extract state_parcel_id and net_tax_amount from one fixed-width TAXDATA record.

    Returns None for records with a blank parcel ID or zero/negative net tax
    (exempt parcels and industrial circuit-breaker zeroes are excluded).

    Handles both:
      - Format 12.2 (2024+): no decimal point, implied 2 decimal places — divide by 100
      - Legacy format (pre-2024): literal decimal point, already in dollars
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
            net_tax_amount = float(net_tax_raw)  # legacy format: literal decimal, already in dollars
        else:
            net_tax_amount = float(net_tax_raw) / 100.0  # Format 12.2: implied decimal (50 IAC 26-20-2(a)(6))
    except ValueError:
        return None
    if net_tax_amount <= 0:
        return None
    return {"state_parcel_id": state_parcel_id, "net_tax_amount": net_tax_amount}
