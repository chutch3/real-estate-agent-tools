from backend.models import AgentInfo
from backend.services import PostGenerationService, PropertyService


class PostCoordinator:
    def __init__(
        self,
        property_service: PropertyService,
        post_generation_service: PostGenerationService,
    ):
        self._property_service = property_service
        self._post_generation_service = post_generation_service

    async def generate_post(
        self,
        property_id: str,
        brokerage_id: str,
        agent_info: AgentInfo,
        custom_template: str | None = None,
    ) -> str:
        prop = await self._property_service.get_property(property_id, brokerage_id)
        doc_ids = [d.id for d in prop.documents]
        return await self._post_generation_service.generate_post(
            prop.model_dump(), agent_info, custom_template, doc_ids=doc_ids
        )
