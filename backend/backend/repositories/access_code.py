from collections.abc import Callable

from sqlmodel import select

from backend.models import AccessCode


class AccessCodeRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    def upsert(self, access_code: AccessCode) -> AccessCode:
        with self._session_factory() as session:
            existing = session.exec(
                select(AccessCode).where(AccessCode.representation_id == access_code.representation_id)
            ).first()
            if existing:
                existing.code_hash = access_code.code_hash
                existing.created_at = access_code.created_at
                session.commit()
                session.refresh(existing)
                return existing
            session.add(access_code)
            session.commit()
            session.refresh(access_code)
            return access_code

    def get_by_representation(self, representation_id: str) -> AccessCode | None:
        with self._session_factory() as session:
            return session.exec(select(AccessCode).where(AccessCode.representation_id == representation_id)).first()
