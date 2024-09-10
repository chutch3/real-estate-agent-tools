from pathlib import Path
from backend.container import Container
from backend.models import AgentInfo, PropertyInfo
from backend.template_loader import TemplateLoader, TEMPLATE_DIR
import jinja2
import pytest


class TestTemplateLoader:
    def test_render_system_prompt(
        self, subject: TemplateLoader, jinja_env: jinja2.Environment
    ):
        actual = subject.render_system_prompt()
        assert actual == jinja_env.get_template("system_prompt.txt").render()

    def test_render_user_prompt(
        self, subject: TemplateLoader, jinja_env: jinja2.Environment
    ):
        actual_property_info = PropertyInfo(
            formatted_address="123 Main St",
        )
        actual_agent_info = AgentInfo(
            agent_name="John Doe",
            agent_company="John Doe Real Estate",
            agent_contact="john.doe@example.com",
        )

        actual = subject.render_user_prompt(
            property_info=actual_property_info,
            agent_info=actual_agent_info,
            custom_template=None,
        )
        assert actual == jinja_env.get_template("post_prompt.txt").render(
            **actual_property_info.model_dump(),
            **actual_agent_info.model_dump(),
        )

    def test_render_user_prompt_with_custom_template(
        self,
        subject: TemplateLoader,
    ):
        actual_property_info = PropertyInfo(
            formatted_address="123 Main St",
        )
        actual_agent_info = AgentInfo(
            agent_name="John Doe",
            agent_company="John Doe Real Estate",
            agent_contact="john.doe@example.com",
        )
        custom_template = "Custom template: {{ formatted_address }}"

        actual = subject.render_user_prompt(
            property_info=actual_property_info,
            agent_info=actual_agent_info,
            custom_template=custom_template,
        )
        assert actual == jinja2.Environment().from_string(custom_template).render(
            **actual_property_info.model_dump(),
            **actual_agent_info.model_dump(),
        )

    @pytest.fixture
    def jinja_env(self):
        yield jinja2.Environment(loader=jinja2.FileSystemLoader("backend/templates"))

    @pytest.fixture
    def subject(self, test_container: Container):
        yield test_container.template_loader()
