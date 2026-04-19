import uuid
from datetime import UTC, datetime, timedelta

from backend.exceptions import InvalidMagicLinkError
from backend.models import MagicLinkToken
from backend.repositories.magic_link import MagicLinkRepository
from backend.repositories.representation import RepresentationRepository


class MagicLinkService:
    def __init__(
        self,
        magic_link_repository: MagicLinkRepository,
        representation_repository: RepresentationRepository,
        token_ttl_hours: int,
    ) -> None:
        self._repository = magic_link_repository
        self._representation_repository = representation_repository
        self._token_ttl_hours = token_ttl_hours

    def create_magic_link(self, representation_id: str, brokerage_id: str) -> MagicLinkToken:
        rep = self._representation_repository.get(representation_id)
        if rep is None or rep.brokerage_id != brokerage_id:
            raise InvalidMagicLinkError(f"Representation {representation_id} not found for brokerage")
        self._repository.revoke_all_for_representation(representation_id)
        now = datetime.now(UTC)
        token = MagicLinkToken(
            representation_id=representation_id,
            token=str(uuid.uuid4()),
            expires_at=now + timedelta(hours=self._token_ttl_hours),
            created_at=now,
        )
        return self._repository.create(token)

    def validate_token(self, token: str) -> MagicLinkToken:
        record = self._repository.get_by_token(token)
        if record is None or record.revoked:
            raise InvalidMagicLinkError("Token not found or revoked")
        now = datetime.now(UTC)
        expires = record.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if now > expires:
            raise InvalidMagicLinkError("Token expired")
        self._repository.touch(record.id, now)
        return record

    def revoke_token(self, token_id: str, brokerage_id: str) -> None:
        record = self._repository.get_by_id(token_id)
        if record is None:
            raise InvalidMagicLinkError(f"Token {token_id} not found")
        rep = self._representation_repository.get(record.representation_id)
        if rep is None or rep.brokerage_id != brokerage_id:
            raise InvalidMagicLinkError("Token does not belong to this brokerage")
        self._repository.revoke(token_id)

    def list_tokens(self, representation_id: str, brokerage_id: str) -> list[MagicLinkToken]:
        rep = self._representation_repository.get(representation_id)
        if rep is None or rep.brokerage_id != brokerage_id:
            raise InvalidMagicLinkError(f"Representation {representation_id} not found for brokerage")
        return self._repository.list_active_by_representation(representation_id)
