from http import HTTPStatus

from backend.models import TemplateResponse
from backend.template_loader import TEMPLATE_DIR


class TestTemplates:
    def test_get_default_template(self, lightweight_client):
        response = lightweight_client.get("/api/templates/default")
        assert response.status_code == HTTPStatus.OK
        with open(f"{TEMPLATE_DIR}/post_prompt.txt") as file:
            assert response.json() == TemplateResponse(template=file.read()).model_dump()
