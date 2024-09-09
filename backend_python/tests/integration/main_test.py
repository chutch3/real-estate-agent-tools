import pytest
from backend.main import app
from fastapi.testclient import TestClient


class TestApp:
    def test_health_check(self, subject):
        response = subject.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_generate_post(self, subject):
        response = subject.post(
            "/api/generate-post",
            json={
                "address": "123 Main St, Anytown, USA",
                "agentInfo": {"name": "John Doe", "email": "john.doe@example.com"},
                "customTemplate": "This is a test post",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"post": "This is a test post"}

    # @pytest.mark.parametrize(
    #     "origin,expected_allow_origin,expected_status_code",
    #     [
    #         ("http://localhost:8080", "http://localhost:8080", 200, '{"status": "ok"}'),
    #         ("http://localhost", "http://localhost", 200, '{"status": "ok"}'),
    #         ("http://localhost.tiangolo.com", None, 400, "Disallowed CORS origin"),
    #     ],
    # )
    # def test_cors(
    #     self,
    #     subject,
    #     origin,
    #     expected_allow_origin,
    #     expected_status_code,
    #     expected_response,
    # ):
    #     response = subject.options(
    #         "/health",
    #         headers={
    #             "Origin": origin,
    #             "Access-Control-Request-Method": "GET",
    #         },
    #     )

    #     assert response.status_code == expected_status_code
    #     assert response.headers["Access-Control-Allow-Origin"] == expected_allow_origin
    #     assert all(
    #         method in response.headers["Access-Control-Allow-Methods"]
    #         for method in ["DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"]
    #     )
    #     assert response.text == expected_response

    @pytest.fixture
    def subject(self):
        return TestClient(app)
