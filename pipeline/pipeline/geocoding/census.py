import csv
import io
import logging

import httpx

from pipeline.geocoding.base import AddressRecord

_logger = logging.getLogger(__name__)

_CENSUS_GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"


class CensusGeocoder:
    def __init__(self, url: str = _CENSUS_GEOCODER_URL) -> None:
        self._url = url

    def geocode(self, addresses: list[AddressRecord]) -> dict[int, tuple[float, float]]:
        buf = io.StringIO()
        writer = csv.writer(buf)
        for idx, address, city, state, zip_code in addresses:
            writer.writerow([idx, address or "", city or "", state or "", zip_code or ""])

        response = httpx.post(
            self._url,
            data={"benchmark": "Public_AR_Current"},
            files={"addressFile": ("addresses.csv", buf.getvalue().encode(), "text/csv")},
            timeout=300,
        )
        response.raise_for_status()

        coords: dict[int, tuple[float, float]] = {}
        reader = csv.reader(io.StringIO(response.text))
        for row in reader:
            if len(row) >= 6 and row[2].strip() == "Match" and row[5].strip():
                try:
                    lon_str, lat_str = row[5].strip().strip('"').split(",")
                    coords[int(row[0])] = (float(lat_str), float(lon_str))
                except (ValueError, IndexError):
                    pass
        return coords
