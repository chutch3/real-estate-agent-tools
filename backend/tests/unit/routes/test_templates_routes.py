from http import HTTPStatus
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.models import TemplateResponse
from backend.routes.templates import router
from backend.template_loader import TemplateLoader


class TestTemplateRoutes:
    def test_get_default_template(self, subject, mock_template_loader):
        mock_template_loader.read_user_prompt.return_value = "This is a test template"
        response = subject.get("/templates/default")
        assert response.status_code == HTTPStatus.OK
        assert response.json() == TemplateResponse(template="This is a test template").model_dump()

    @pytest.fixture
    def mock_template_loader(self):
        yield Mock(spec=TemplateLoader)

    @pytest.fixture
    def subject(self, test_container, mock_template_loader):
        with test_container.override_providers(
            template_loader=mock_template_loader,
        ):
            app = FastAPI()
            app.include_router(router)
            yield TestClient(app)
