import logging
from collections.abc import AsyncGenerator

from backend.clients.openai import OpenAIClient
from backend.models import ChatMessage, PropertyInfo
from backend.repositories.chat_messages import ChatMessageRepository
from backend.repositories.document_embeddings import DocumentEmbeddingRepository
from backend.repositories.properties import PropertyRepository


class ChatService:
    def __init__(
        self,
        chat_message_repository: ChatMessageRepository,
        property_repository: PropertyRepository,
        document_embedding_repository: DocumentEmbeddingRepository,
        openai_client: OpenAIClient,
        rag_top_k: int = 5,
        max_tokens: int = 1000,
    ):
        self._chat_message_repository = chat_message_repository
        self._property_repository = property_repository
        self._document_embedding_repository = document_embedding_repository
        self._openai_client = openai_client
        self._rag_top_k = rag_top_k
        self._max_tokens = max_tokens
        self._logger = logging.getLogger(self.__class__.__name__)

    async def prepare_chat_messages(self, property_id: str, user_message: str) -> list[dict]:
        await self._chat_message_repository.save_message(property_id, "user", user_message)

        property_info = await self._property_repository.get_property(property_id)
        embedding = await self._openai_client.create_embeddings(user_message)

        doc_ids = [doc.id for doc in (property_info.documents or [])]
        self._logger.info(f"Querying embeddings for doc_ids: {doc_ids}")
        rag_results = await self._document_embedding_repository.query_embeddings(
            [embedding],
            limit=self._rag_top_k,
            filter_ids=doc_ids if doc_ids else None,
        )
        self._logger.info(f"Found {len(rag_results)} rag results")

        system_prompt = self._build_system_prompt(property_info, rag_results)
        history = await self._chat_message_repository.get_history(property_id)
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg.role, "content": msg.content})
        return messages

    async def stream_response(self, property_id: str, messages: list[dict]) -> AsyncGenerator[str, None]:
        full_response = ""
        async for chunk in self._openai_client.stream_completion(messages, max_tokens=self._max_tokens):
            full_response += chunk
            yield chunk
        await self._chat_message_repository.save_message(property_id, "assistant", full_response)

    async def get_history(self, property_id: str) -> list[ChatMessage]:
        return await self._chat_message_repository.get_history(property_id)

    def _build_system_prompt(self, property_info: PropertyInfo, rag_results: list) -> str:
        property_summary = self._summarize_property(property_info)
        rag_context = "\n\n".join(r["text"] for r in rag_results) if rag_results else ""
        prompt = (
            "You are a helpful real estate assistant. Answer questions about the property below.\n\n"
            f"Property Information:\n{property_summary}"
        )
        if rag_context:
            prompt += f"\n\nRelevant Documents:\n{rag_context}"
        return prompt

    def _summarize_property(self, prop: PropertyInfo) -> str:
        lines = []
        if prop.formatted_address:
            lines.append(f"Address: {prop.formatted_address}")
        if prop.city and prop.state:
            lines.append(f"Location: {prop.city}, {prop.state}")
        if prop.property_type:
            lines.append(f"Type: {prop.property_type}")
        if prop.bedrooms:
            lines.append(f"Bedrooms: {prop.bedrooms}")
        if prop.bathrooms:
            lines.append(f"Bathrooms: {prop.bathrooms}")
        if prop.square_footage:
            lines.append(f"Square Footage: {prop.square_footage}")
        if prop.year_built:
            lines.append(f"Year Built: {prop.year_built}")
        return "\n".join(lines) if lines else "No details available."
