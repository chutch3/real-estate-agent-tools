import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.container import Container
from backend.main import create_app

_JWT_SECRET = "test-secret-key-for-integration-tests"


class TestIdentityIntegration:
    def test_should_create_brokerage_and_admin_user(self, client: TestClient):
        # 1. Create a Brokerage
        response = client.post("/api/brokerages", json={"name": "Acme Realty", "contact_info": "123 Main St"})
        assert response.status_code == 201
        created_brokerage = response.json()
        assert created_brokerage["name"] == "Acme Realty"
        assert "id" in created_brokerage

        # 2. Create an Admin User for that Brokerage
        response = client.post(
            "/api/users",
            json={
                "email": "admin@acmerealty.com",
                "password": "securepassword",
                "role": "ADMIN",
                "brokerage_id": created_brokerage["id"],
            },
        )
        assert response.status_code == 201
        created_user = response.json()
        assert created_user["email"] == "admin@acmerealty.com"
        assert created_user["brokerage_id"] == created_brokerage["id"]

        # 3. Authenticate — JWT is set as an httpOnly cookie, not returned in the body
        response = client.post(
            "/api/auth/token",
            data={"username": "admin@acmerealty.com", "password": "securepassword"},
        )
        assert response.status_code == 200
        assert response.json() == {"token_type": "bearer"}
        assert "access_token" in client.cookies

        # 4. /users/me reads the cookie automatically (TestClient forwards cookies)
        response = client.get("/api/users/me")
        assert response.status_code == 200
        me_data = response.json()
        assert me_data["email"] == "admin@acmerealty.com"
        assert me_data["brokerage"]["name"] == "Acme Realty"

        # 5. Logout clears the cookie
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        assert "access_token" not in client.cookies

        # 6. /users/me returns 401 after logout
        response = client.get("/api/users/me")
        assert response.status_code == 401

    @pytest.fixture
    def client(self, test_container: Container, tmp_path) -> TestClient:
        with patch.dict(
            os.environ,
            {
                "DB_URI": f"sqlite:///{tmp_path}/test.db",
                "JWT_SECRET_KEY": _JWT_SECRET,
            },
        ):
            app = create_app(test_container)
            yield TestClient(app)
