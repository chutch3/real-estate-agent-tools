from collections.abc import Callable

from sqlmodel import select

from backend.models import Property, Representation, RepresentationRole


class RepresentationRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    def insert(self, rep: Representation) -> Representation:
        with self._session_factory() as session:
            session.add(rep)
            session.commit()
            session.refresh(rep)
            return rep

    def get(self, rep_id: str) -> Representation | None:
        with self._session_factory() as session:
            return session.get(Representation, rep_id)

    def get_by_portal_token(self, portal_token: str) -> Representation | None:
        with self._session_factory() as session:
            return session.exec(select(Representation).where(Representation.portal_token == portal_token)).first()

    def list_with_property(self, brokerage_id: str) -> list[tuple[Representation, Property]]:
        with self._session_factory() as session:
            rows = session.exec(
                select(Representation, Property)
                .join(Property, Representation.property_id == Property.id)
                .where(Representation.brokerage_id == brokerage_id)
            ).all()
            return list(rows)

    def count_opposite_role(self, property_id: str, brokerage_id: str, role: str) -> int:
        opposite = (
            RepresentationRole.BUYERS_AGENT
            if role == RepresentationRole.LISTING_AGENT
            else RepresentationRole.LISTING_AGENT
        )
        with self._session_factory() as session:
            rows = session.exec(
                select(Representation).where(
                    Representation.property_id == property_id,
                    Representation.brokerage_id == brokerage_id,
                    Representation.role == opposite,
                )
            ).all()
            return len(rows)
