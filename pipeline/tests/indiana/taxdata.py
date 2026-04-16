import io
import zipfile

from pipeline.indiana.tax.parser import (
    TAXDATA_NET_TAX_START,
    TAXDATA_NET_TAX_WIDTH,
    TAXDATA_PARCEL_ID_START,
    TAXDATA_PARCEL_ID_WIDTH,
)


def make_taxdata_record(parcel_id: str, net_tax: float) -> bytes:
    """Build a minimal TAXDATA record with the parcel and net tax embedded (Format 12.2)."""
    record = bytearray(b" " * 779)
    pid = parcel_id.ljust(TAXDATA_PARCEL_ID_WIDTH).encode()
    record[TAXDATA_PARCEL_ID_START : TAXDATA_PARCEL_ID_START + TAXDATA_PARCEL_ID_WIDTH] = pid
    tax_str = f"{net_tax:.2f}".replace(".", "").rjust(TAXDATA_NET_TAX_WIDTH, "0").encode()
    record[TAXDATA_NET_TAX_START : TAXDATA_NET_TAX_START + TAXDATA_NET_TAX_WIDTH] = tax_str
    return bytes(record)


def make_taxbill_zip(*rows: bytes, filename: str = "TaxBill.txt") -> bytes:
    """Build a TAXDATA zip containing a header row followed by the given records."""
    header = b"TAXDATA HEADER\r\n"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(filename, header + b"".join(row + b"\r\n" for row in rows))
    buf.seek(0)
    return buf.read()
