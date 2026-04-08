from collections.abc import Callable

from backend.models import ParcelBoundary


class ParcelBoundaryRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    def get_by_nguid(self, nguid: str) -> ParcelBoundary | None:
        with self._session_factory() as session:
            return session.get(ParcelBoundary, nguid)

    def upsert(self, boundary: ParcelBoundary) -> ParcelBoundary:
        with self._session_factory() as session:
            existing = session.get(ParcelBoundary, boundary.nguid)
            if existing:
                existing.geometry = boundary.geometry
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            session.add(boundary)
            session.commit()
            session.refresh(boundary)
            return boundary
