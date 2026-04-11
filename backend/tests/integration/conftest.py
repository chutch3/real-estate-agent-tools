import os
from unittest.mock import patch

import jose.jwt as jwt
import pytest
from fastapi.testclient import TestClient

from backend.container import Container
from backend.main import create_app
from backend.models import Brokerage, User


def seed_brokerage_and_user(
    db,
    *,
    name: str = "Default Brokerage",
    email: str = "agent@test.com",
    allow_dual_agency: bool = False,
) -> tuple[str, str]:
    """Seed a brokerage and agent user. Returns (brokerage_id, user_id)."""
    with db.session() as session:
        brokerage = Brokerage(name=name, allow_dual_agency=allow_dual_agency)
        session.add(brokerage)
        session.commit()
        session.refresh(brokerage)
        user = User(
            email=email,
            hashed_password="fake-hash",
            role="AGENT",
            brokerage_id=brokerage.id,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return brokerage.id, user.id


def make_jwt(user_id: str, brokerage_id: str, role: str = "AGENT", secret: str = "test-secret") -> str:
    return jwt.encode({"sub": user_id, "org": brokerage_id, "role": role}, secret, algorithm="HS256")


@pytest.fixture
def lightweight_client(test_container: Container, tmp_path) -> TestClient:
    """TestClient backed by SQLite — no Docker services required."""
    env_overrides = {
        "DB_URI": f"sqlite:///{tmp_path}/test.db",
        "JWT_SECRET_KEY": "test-secret",
    }
    with patch.dict(os.environ, env_overrides):
        with TestClient(create_app(test_container)) as client:
            brokerage_id, user_id = seed_brokerage_and_user(test_container.db())
            token = make_jwt(user_id, brokerage_id)
            client.cookies.set("access_token", token)
            yield client
