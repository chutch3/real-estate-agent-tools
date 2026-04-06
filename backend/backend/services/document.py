import asyncio
import io
import uuid

import pypdf

from backend.clients.openai import OpenAIClient
from backend.repositories.document_embeddings import DocumentEmbeddingRepository
from backend.repositories.document_storage import DocumentStorageRepository


class DocumentService:
    def __init__(
        self,
        repository: DocumentEmbeddingRepository,
        client: OpenAIClient,
        storage_repository: DocumentStorageRepository,
    ):
        self._repository = repository
        self._client = client
        self._storage_repository = storage_repository

    async def exists(self, doc_id: str) -> bool:
        return await self._repository.exists(doc_id)

    async def delete(self, doc_id: str) -> None:
        await asyncio.to_thread(self._storage_repository.delete, doc_id)

    async def process_pdf(self, content: bytes) -> str:
        if not content:
            raise ValueError("Content is empty")

        try:
            pdf_reader = pypdf.PdfReader(io.BytesIO(content))
            pages_text = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text.strip():
                    pages_text.append(text)
        except pypdf.errors.PdfReadError:
            raise ValueError("Invalid PDF content")

        doc_id = str(uuid.uuid4())
        embeddings = await asyncio.gather(*[self._client.create_embeddings(text) for text in pages_text])
        await self._repository.batch_insert_embeddings(doc_id, list(zip(pages_text, embeddings)))
        await asyncio.to_thread(self._storage_repository.save, doc_id, content)
        return doc_id
