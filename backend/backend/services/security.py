from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

_ALGORITHM = "HS256"
_REQUIRED_CLAIMS = {"sub", "org", "role"}


class SecurityService:
    def __init__(self, secret_key: str, token_expire_minutes: int = 30) -> None:
        self._secret_key = secret_key
        self._token_expire_minutes = token_expire_minutes

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

    @property
    def token_expire_minutes(self) -> int:
        return self._token_expire_minutes

    def create_access_token(self, user_id: str, brokerage_id: str, role: str) -> str:
        expire = datetime.now(UTC) + timedelta(minutes=self._token_expire_minutes)
        claims = {"sub": user_id, "org": brokerage_id, "role": role, "exp": expire}
        return jwt.encode(claims, self._secret_key, algorithm=_ALGORITHM)

    def decode_token(self, token: str) -> dict:
        claims = jwt.decode(token, self._secret_key, algorithms=[_ALGORITHM])
        missing = _REQUIRED_CLAIMS - claims.keys()
        if missing:
            raise JWTError(f"Token missing required claims: {missing}")
        return claims
