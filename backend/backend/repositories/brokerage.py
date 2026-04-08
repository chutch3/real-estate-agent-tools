from collections.abc import Callable

from backend.models import Brokerage


class BrokerageRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    def create(self, brokerage: Brokerage) -> Brokerage:
        with self._session_factory() as session:
            session.add(brokerage)
            session.commit()
            session.refresh(brokerage)
            return brokerage

    def get_by_id(self, brokerage_id: str) -> Brokerage | None:
        with self._session_factory() as session:
            return session.get(Brokerage, brokerage_id)
