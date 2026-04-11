import os
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import jose.jwt as jwt
from fastapi.testclient import TestClient

from backend.main import create_app
from tests.integration.conftest import seed_brokerage_and_user


class TestHealth:
    def test_health_check(self, lightweight_client):
        response = lightweight_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_cors_allows_localhost(self, lightweight_client):
        response = lightweight_client.options(
            "/health",
            headers={"Origin": "http://localhost:3001", "Access-Control-Request-Method": "GET"},
        )
        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3001"

    def test_cors_blocks_unknown_origin(self, lightweight_client):
        response = lightweight_client.options(
            "/health",
            headers={"Origin": "http://localhost.tiangolo.com", "Access-Control-Request-Method": "GET"},
        )
        assert response.status_code == 400


class TestSlidingTokenRefresh:
    def test_issues_new_cookie_when_token_is_near_expiry(self, test_container, tmp_path):
        env_overrides = {"DB_URI": f"sqlite:///{tmp_path}/test.db", "JWT_SECRET_KEY": "test-secret"}
        with patch.dict(os.environ, env_overrides):
            with TestClient(create_app(test_container)) as client:
                brokerage_id, user_id = seed_brokerage_and_user(test_container.db())
                near_expiry_token = jwt.encode(
                    {
                        "sub": user_id,
                        "org": brokerage_id,
                        "role": "AGENT",
                        "exp": datetime.now(UTC) + timedelta(minutes=5),
                    },
                    "test-secret",
                    algorithm="HS256",
                )
                client.cookies.set("access_token", near_expiry_token)

                response = client.get("/api/users/me")

        assert response.status_code == 200
        assert "access_token" in response.cookies, "middleware should have issued a refreshed cookie"

    def test_does_not_reissue_cookie_when_token_has_plenty_of_time(self, test_container, tmp_path):
        env_overrides = {"DB_URI": f"sqlite:///{tmp_path}/test.db", "JWT_SECRET_KEY": "test-secret"}
        with patch.dict(os.environ, env_overrides):
            with TestClient(create_app(test_container)) as client:
                brokerage_id, user_id = seed_brokerage_and_user(test_container.db())
                fresh_token = jwt.encode(
                    {
                        "sub": user_id,
                        "org": brokerage_id,
                        "role": "AGENT",
                        "exp": datetime.now(UTC) + timedelta(minutes=29),
                    },
                    "test-secret",
                    algorithm="HS256",
                )
                client.cookies.set("access_token", fresh_token)

                response = client.get("/api/users/me")

        assert response.status_code == 200
        assert "access_token" not in response.cookies, "middleware should not refresh a fresh token"
