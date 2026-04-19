from collections.abc import Callable
from datetime import UTC, datetime

from sqlmodel import select

from backend.models import MagicLinkToken


class MagicLinkRepository:
    def __init__(self, session_factory: Callable) -> None:
        self._session_factory = session_factory

    def create(self, token: MagicLinkToken) -> MagicLinkToken:
        with self._session_factory() as session:
            session.add(token)
            session.commit()
            session.refresh(token)
            return token

    def get_by_token(self, token: str) -> MagicLinkToken | None:
        with self._session_factory() as session:
            return session.exec(select(MagicLinkToken).where(MagicLinkToken.token == token)).first()

    def get_by_id(self, token_id: str) -> MagicLinkToken | None:
        with self._session_factory() as session:
            return session.get(MagicLinkToken, token_id)

    def list_active_by_representation(self, representation_id: str) -> list[MagicLinkToken]:
        now = datetime.now(UTC)
        with self._session_factory() as session:
            return list(
                session.exec(
                    select(MagicLinkToken).where(
                        MagicLinkToken.representation_id == representation_id,
                        MagicLinkToken.revoked == False,  # noqa: E712
                        MagicLinkToken.expires_at > now,
                    )
                ).all()
            )

    def revoke(self, token_id: str) -> None:
        with self._session_factory() as session:
            token = session.get(MagicLinkToken, token_id)
            if token:
                token.revoked = True
                session.commit()

    def touch(self, token_id: str, accessed_at: datetime) -> None:
        with self._session_factory() as session:
            token = session.get(MagicLinkToken, token_id)
            if token:
                token.last_accessed_at = accessed_at
                session.commit()
