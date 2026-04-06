from collections.abc import Callable

from backend.models import CountyBoundary


class CountyBoundaryRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    def get_by_fips(self, fips: str) -> CountyBoundary | None:
        with self._session_factory() as session:
            return session.get(CountyBoundary, fips)

    def upsert(self, boundary: CountyBoundary) -> CountyBoundary:
        with self._session_factory() as session:
            existing = session.get(CountyBoundary, boundary.fips)
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
