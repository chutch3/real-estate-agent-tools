from backend.services import PropertyService, PostGenerationService
from backend.models import GeocodeLocation


class PostCoordinator:
    def __init__(
        self,
        property_service: PropertyService,
        post_generation_service: PostGenerationService,
    ):

        self._property_service = property_service
        self._post_generation_service = post_generation_service

    async def generate_post(self, address, agent_info, custom_template, pdf_id=None):
        """
        Generate a post for a property.

        Args:
            address (str): The address of the property.
            agent_info (AgentInfo): The agent info.
            custom_template (str): The custom template.

        Returns:
            str: The generated post.
        """
        property = await self._property_service.get_property(address)
        return await self._post_generation_service.generate_post(
            property, agent_info, custom_template, pdf_id
        )

    async def post_to_instagram(self, post):
        raise NotImplementedError("Not implemented yet")
