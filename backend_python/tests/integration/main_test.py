from http import HTTPStatus
from pathlib import Path

from backend.main import create_app
from backend.template_loader import TEMPLATE_DIR
import pytest
from backend.models import (
    AgentInfo,
    GeocodeLocation,
    GeocodeRequest,
    GeocodeResponse,
    PostGenerationRequest,
    TemplateResponse,
)
from dotenv import load_dotenv
from fastapi.testclient import TestClient


class TestApp:
    def test_health_check(self, subject):
        response = subject.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_generate_post(self, subject):
        response = subject.post(
            "/api/generate-post",
            json=PostGenerationRequest(
                address="1600 Amphitheatre Parkway Mountain View, CA 94043, USA",
                agent_info=AgentInfo(
                    agent_name="John Doe",
                    agent_company="John Doe Real Estate",
                    agent_contact="john.doe@example.com",
                ),
            ).model_dump(),
        )
        assert response.status_code == HTTPStatus.CREATED
        response_json = response.json()
        assert "post" in response_json
        assert "John Doe" in response_json["post"]
        assert "John Doe Real Estate" in response_json["post"]
        assert "john.doe@example.com" in response_json["post"]
        assert "Mountain View, CA" in response_json["post"]

    def test_geocode(self, subject):
        response = subject.post(
            "/api/geocode",
            json=GeocodeRequest(
                address="1600 Amphitheatre Parkway Mountain View, CA 94043, USA"
            ).model_dump(),
        )
        assert response.status_code == HTTPStatus.CREATED
        assert (
            response.json()
            == GeocodeResponse(
                location=GeocodeLocation(lat=37.4225103, lng=-122.0847089)
            ).model_dump()
        )

    def test_get_default_template(self, subject):
        response = subject.get("/api/default-template")
        assert response.status_code == HTTPStatus.OK
        with open(f"{TEMPLATE_DIR}/post_prompt.txt", "r") as file:
            assert (
                response.json() == TemplateResponse(template=file.read()).model_dump()
            )

    @pytest.mark.parametrize(
        "origin,expected_allow_origin,expected_status_code,expected_response",
        [
            ("http://localhost:3001", "http://localhost:3001", 200, "OK"),
            ("http://localhost", "http://localhost", 200, "OK"),
            ("http://localhost.tiangolo.com", None, 400, "Disallowed CORS origin"),
        ],
    )
    def test_cors(
        self,
        subject,
        origin,
        expected_allow_origin,
        expected_status_code,
        expected_response,
    ):
        response = subject.options(
            "/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )

        assert response.status_code == expected_status_code
        assert (
            response.headers.get("Access-Control-Allow-Origin") == expected_allow_origin
        )
        assert all(
            method in response.headers["Access-Control-Allow-Methods"]
            for method in ["DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"]
        )
        assert response.text == expected_response

    @pytest.fixture
    def subject(self):
        root_path = Path(__file__).parent.parent.parent
        load_dotenv(root_path / ".env")
        return TestClient(create_app())
