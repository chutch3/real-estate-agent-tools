import httpx


class BackendClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url

    def list_county_fips(self) -> list[str]:
        response = httpx.get(f"{self._base_url}/api/internal/counties")
        response.raise_for_status()
        return response.json()["county_fips"]
