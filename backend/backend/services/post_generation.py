import logging
from backend.clients.openai import OpenAIClient
from backend.template_loader import TemplateLoader
from backend.repositories.document_embeddings import DocumentEmbeddingRepository


class PostGenerationService:
    def __init__(
        self,
        openai_client: OpenAIClient,
        template_loader: TemplateLoader,
        document_embedding_repository: DocumentEmbeddingRepository,
    ):
        self.openai_client = openai_client
        self.template_loader = template_loader
        self.document_embedding_repository = document_embedding_repository
        self._logger = logging.getLogger(self.__class__.__name__)

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
            pdf_id (str): The PDF ID.

        Returns:
            str: The generated post.
        """
        system_prompt = self.template_loader.render_system_prompt()
        user_prompt = self.template_loader.render_user_prompt(
            property_info=property_info,
            agent_info=agent_info,
            custom_template=custom_template,
        )

        user_prompt_embedding = await self.openai_client.create_embeddings(user_prompt)
        relevant_chunks = await self.document_embedding_repository.query_embeddings(
            [user_prompt_embedding], limit=5
        )

        # TODO: move this the user prompt loader
        additional_info = "\n".join([chunk["text"] for chunk in relevant_chunks])
        user_prompt += f"\n\nAdditional information from MLS sheet:\n{additional_info}"

        self._logger.info(f"User prompt: {user_prompt}")

        return await self.openai_client.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=200,
        )
