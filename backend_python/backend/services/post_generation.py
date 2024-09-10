from backend.clients.openai import OpenAIClient
from backend.template_loader import TemplateLoader


class PostGenerationService:
    def __init__(
        self,
        openai_client: OpenAIClient,
        template_loader: TemplateLoader,
    ):
        self.openai_client = openai_client
        self.template_loader = template_loader

    async def generate_post(
        self,
        property_info: dict,
        agent_info: dict,
        custom_template: str = None,
    ):
        """
        Generate the post using openai and leveraging the templates.

        Args:
            property_info (dict): The property info.
            agent_info (dict): The agent info.
            custom_template (str): The custom template.

        Returns:
            str: The generated post.
        """
        system_prompt = self.template_loader.render_system_prompt()
        user_prompt = self.template_loader.render_user_prompt(
            property_info=property_info,
            agent_info=agent_info,
            custom_template=custom_template,
        )

        return await self.openai_client.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=200,
        )
