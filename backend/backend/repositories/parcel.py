from collections.abc import Callable

from sqlmodel import select

from backend.models import Parcel


class ParcelRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    def get_by_nguid(self, nguid: str) -> Parcel | None:
        with self._session_factory() as session:
            return session.get(Parcel, nguid)

    def get_by_property_id(self, property_id: str) -> Parcel | None:
        with self._session_factory() as session:
            return session.exec(select(Parcel).where(Parcel.property_id == property_id)).first()

    def upsert(self, parcel: Parcel) -> Parcel:
        with self._session_factory() as session:
            existing = session.get(Parcel, parcel.nguid)
            if existing:
                existing.geometry = parcel.geometry
                if parcel.property_id is not None:
                    existing.property_id = parcel.property_id
                if parcel.state_parcel_id is not None:
                    existing.state_parcel_id = parcel.state_parcel_id
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            session.add(parcel)
            session.commit()
            session.refresh(parcel)
            return parcel
