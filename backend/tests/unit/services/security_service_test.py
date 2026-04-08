import base64
import json

import pytest
from jose import JWTError, jwt

from backend.services.security import SecurityService

_SECRET = "test-secret-key"
_ALG = "HS256"


class TestSecurityService:
    # --- Password hashing ---

    def test_hash_password_does_not_store_plain_text(self, subject: SecurityService):
        result = subject.hash_password("mysecretpassword")

        assert result != "mysecretpassword"

    def test_same_password_produces_different_hashes(self, subject: SecurityService):
        hash1 = subject.hash_password("mysecretpassword")
        hash2 = subject.hash_password("mysecretpassword")

        assert hash1 != hash2

    def test_verify_password_returns_true_for_correct_password(self, subject: SecurityService):
        hashed = subject.hash_password("mysecretpassword")

        assert subject.verify_password("mysecretpassword", hashed) is True

    def test_verify_password_returns_false_for_wrong_password(self, subject: SecurityService):
        hashed = subject.hash_password("mysecretpassword")

        assert subject.verify_password("wrongpassword", hashed) is False

    # --- Token creation and decoding ---

    def test_decode_token_returns_expected_claims(self, subject: SecurityService):
        token = subject.create_access_token(
            user_id="user-123",
            brokerage_id="brokerage-456",
            role="ADMIN",
        )

        claims = subject.decode_token(token)

        assert claims["sub"] == "user-123"
        assert claims["org"] == "brokerage-456"
        assert claims["role"] == "ADMIN"

    def test_decode_token_raises_for_invalid_token(self, subject: SecurityService):
        with pytest.raises(JWTError):
            subject.decode_token("not.a.valid.token")

    def test_decode_token_raises_for_expired_token(self):
        expired_service = SecurityService(secret_key=_SECRET, token_expire_minutes=-1)
        token = expired_service.create_access_token(user_id="user-123", brokerage_id="brokerage-456", role="ADMIN")

        with pytest.raises(JWTError):
            expired_service.decode_token(token)

    def test_decode_token_raises_for_token_signed_with_different_key(self, subject: SecurityService):
        other_service = SecurityService(secret_key="completely-different-secret")
        token = other_service.create_access_token(user_id="user-123", brokerage_id="brokerage-456", role="ADMIN")

        with pytest.raises(JWTError):
            subject.decode_token(token)

    def test_decode_token_raises_for_tampered_payload(self, subject: SecurityService):
        token = subject.create_access_token(user_id="user-123", brokerage_id="brokerage-456", role="AGENT")
        header, payload_b64, signature = token.split(".")
        payload = json.loads(base64.b64decode(payload_b64 + "=="))
        payload["role"] = "ADMIN"
        tampered_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        tampered_token = f"{header}.{tampered_payload}.{signature}"

        with pytest.raises(JWTError):
            subject.decode_token(tampered_token)

    def test_decode_token_raises_when_required_claims_are_missing(self, subject: SecurityService):
        token = jwt.encode({"sub": "user-123"}, _SECRET, algorithm=_ALG)

        with pytest.raises(JWTError):
            subject.decode_token(token)

    @pytest.fixture
    def subject(self) -> SecurityService:
        return SecurityService(secret_key=_SECRET)
