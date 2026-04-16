from collections.abc import Callable

from sqlmodel import delete, select

from backend.models import PropertyTaxCache


class PropertyTaxCacheRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    def lookup(self, state_parcel_id: str) -> float | None:
        with self._session_factory() as session:
            statement = (
                select(PropertyTaxCache)
                .where(PropertyTaxCache.state_parcel_id == state_parcel_id)
                .order_by(PropertyTaxCache.tax_year.desc())
                .limit(1)
            )
            result = session.exec(statement).first()
            return result.net_tax_amount if result else None

    def bulk_upsert(self, entries: list[PropertyTaxCache], county_fips: str, tax_year: int) -> None:
        with self._session_factory() as session:
            session.exec(
                delete(PropertyTaxCache).where(
                    PropertyTaxCache.county_fips == county_fips,
                    PropertyTaxCache.tax_year == tax_year,
                )
            )
            session.add_all(entries)
            session.commit()

    def upsert(self, entry: PropertyTaxCache) -> PropertyTaxCache:
        with self._session_factory() as session:
            statement = select(PropertyTaxCache).where(
                PropertyTaxCache.state_parcel_id == entry.state_parcel_id,
                PropertyTaxCache.tax_year == entry.tax_year,
            )
            existing = session.exec(statement).first()
            if existing:
                existing.net_tax_amount = entry.net_tax_amount
                existing.county_fips = entry.county_fips
                existing.updated_at = entry.updated_at
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            session.add(entry)
            session.commit()
            session.refresh(entry)
            return entry
