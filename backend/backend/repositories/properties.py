from collections.abc import Callable

from sqlmodel import distinct, select

from backend.models import Property


class PropertyRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    def insert(self, property_data: Property) -> Property:
        with self._session_factory() as session:
            session.add(property_data)
            session.commit()
            session.refresh(property_data)
            return property_data

    def get(self, property_id: str) -> Property | None:
        with self._session_factory() as session:
            return session.get(Property, property_id)

    def list_county_fips(self) -> list[str]:
        with self._session_factory() as session:
            rows = session.exec(select(distinct(Property.county_fips)).where(Property.county_fips.is_not(None))).all()
            return list(rows)
