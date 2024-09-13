import io
import uuid
from backend.clients.openai import OpenAIClient
from backend.repositories.document_embeddings import DocumentEmbeddingRepository
import pypdf


class DocumentService:
    def __init__(self, repository: DocumentEmbeddingRepository, client: OpenAIClient):
        self.repository = repository
        self.client = client

    async def process_pdf(self, content: bytes) -> str:
        if not content:
            raise ValueError("Content is empty")

        try:
            pdf_reader = pypdf.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        except pypdf.errors.PdfReadError:
            raise ValueError("Invalid PDF content")

        doc_id = str(uuid.uuid4())
        embedding = await self.client.create_embeddings(text)
        await self.repository.insert_embeddings(doc_id, text, embedding)
        return doc_id
