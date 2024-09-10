from backend.services import PropertyService, PostGenerationService


class PostCoordinator:
    def __init__(
        self,
        property_service: PropertyService,
        post_generation_service: PostGenerationService,
    ):
        self._property_service = property_service
        self._post_generation_service = post_generation_service

    async def generate_post(self, address, agent_info, custom_template):
        property = await self._property_service.get_property(address)
        return await self._post_generation_service.generate_post(
            property, agent_info, custom_template
        )

    async def post_to_instagram(self, post):
        pass