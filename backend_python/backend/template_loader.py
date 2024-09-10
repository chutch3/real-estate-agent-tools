from typing import Optional
from backend.models import AgentInfo, PropertyInfo
import jinja2

TEMPLATE_DIR = "backend/templates"
print(TEMPLATE_DIR)


class TemplateLoader:
    def __init__(self):
        self._default_jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATE_DIR)
        )

    def render_user_prompt(
        self,
        property_info: PropertyInfo,
        agent_info: AgentInfo,
        custom_template: Optional[str] = None,
    ) -> Optional[str]:
        template = None
        if custom_template is not None:
            template = jinja2.Environment().from_string(custom_template)
        else:
            template = self._default_jinja_env.get_template("post_prompt.txt")
        return template.render(**property_info.model_dump(), **agent_info.model_dump())

    def render_system_prompt(self) -> str:
        return self._default_jinja_env.get_template("system_prompt.txt").render()
