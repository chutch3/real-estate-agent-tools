import random
import string

import bcrypt

from backend.exceptions import InvalidAccessError
from backend.models import AccessCode, Representation
from backend.repositories.access_code import AccessCodeRepository
from backend.repositories.representation import RepresentationRepository

_CODE_LENGTH = 8
_CODE_CHARS = string.ascii_uppercase + string.digits


def _generate_plaintext() -> str:
    return "".join(random.choices(_CODE_CHARS, k=_CODE_LENGTH))


def _hash_code(plaintext: str) -> str:
    return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()


def _verify_code(plaintext: str, code_hash: str) -> bool:
    return bcrypt.checkpw(plaintext.encode(), code_hash.encode())


class AccessCodeService:
    def __init__(
        self,
        access_code_repository: AccessCodeRepository,
        representation_repository: RepresentationRepository,
        portal_base_url: str,
    ) -> None:
        self._access_code_repository = access_code_repository
        self._representation_repository = representation_repository
        self._portal_base_url = portal_base_url

    def _get_rep(self, representation_id: str, brokerage_id: str) -> Representation:
        rep = self._representation_repository.get(representation_id)
        if rep is None or rep.brokerage_id != brokerage_id:
            raise InvalidAccessError(f"Representation {representation_id} not found for brokerage")
        return rep

    def portal_url(self, portal_token: str) -> str:
        return f"{self._portal_base_url}/portal/{portal_token}"

    def generate(self, representation_id: str, brokerage_id: str) -> tuple[str, str]:
        rep = self._get_rep(representation_id, brokerage_id)
        plaintext = _generate_plaintext()
        self._access_code_repository.upsert(
            AccessCode(representation_id=representation_id, code_hash=_hash_code(plaintext))
        )
        return plaintext, self.portal_url(rep.portal_token)

    def validate(self, portal_token: str, plaintext_code: str) -> Representation:
        rep = self._representation_repository.get_by_portal_token(portal_token)
        if rep is None:
            raise InvalidAccessError("Invalid portal token")
        record = self._access_code_repository.get_by_representation(rep.id)
        if record is None:
            raise InvalidAccessError("No active access code")
        if not _verify_code(plaintext_code, record.code_hash):
            raise InvalidAccessError("Invalid access code")
        return rep

    def has_active_code(self, representation_id: str, brokerage_id: str) -> tuple[bool, str]:
        rep = self._get_rep(representation_id, brokerage_id)
        has_code = self._access_code_repository.get_by_representation(representation_id) is not None
        return has_code, self.portal_url(rep.portal_token)
