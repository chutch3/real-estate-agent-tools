import httpx


class BackendClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url

    def list_county_fips(self) -> list[str]:
        response = httpx.get(f"{self._base_url}/api/internal/counties")
        response.raise_for_status()
        return response.json()["county_fips"]

    def upsert_tax_cache(self, *, records: list[dict], county_fips: str, tax_year: int) -> None:
        response = httpx.post(
            f"{self._base_url}/api/internal/tax-cache",
            json={"records": records, "county_fips": county_fips, "tax_year": tax_year},
            timeout=300,
        )
        response.raise_for_status()
