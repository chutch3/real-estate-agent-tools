from typing import Protocol

# (id, street, city, state, zip)
AddressRecord = tuple[int, str | None, str | None, str | None, str | None]


class Geocoder(Protocol):
    def geocode(self, addresses: list[AddressRecord]) -> dict[int, tuple[float, float]]:
        ...
