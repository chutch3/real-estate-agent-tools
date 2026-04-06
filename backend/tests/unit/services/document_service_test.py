import io
import random
from unittest.mock import AsyncMock, MagicMock

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from backend.clients.openai import OpenAIClient
from backend.repositories.document_embeddings import DocumentEmbeddingRepository
from backend.repositories.document_storage import DocumentStorageRepository
from backend.services.document import DocumentService


def generate_fake_pdf_content(num_pages: int = 2, bad_pdf: bool = False) -> bytes:
    if bad_pdf:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(100, 750, "This is a broken PDF")
        c.showPage()
        c.save()
        corrupted_pdf = buffer.getvalue()[: len(buffer.getvalue()) // 2]
        return corrupted_pdf

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    for page in range(num_pages):
        c.drawString(100, 750, f"This is page {page + 1} of {num_pages}")
        c.drawString(100, 700, "This is some fake content for testing purposes.")
        for _ in range(10):
            x, y = random.randint(50, 500), random.randint(50, 700)
            size = random.randint(10, 50)
            c.rect(x, y, size, size, fill=random.choice([0, 1]))
        c.showPage()

    c.save()
    return buffer.getvalue()


class TestDocumentService:
    @pytest.mark.asyncio
    async def test_process_pdf(self, subject, mock_embedding_repository, mock_openai_client):
        mock_openai_client.create_embeddings.return_value = [0.1] * 10

        pdf_content = generate_fake_pdf_content(num_pages=2)
        actual = await subject.process_pdf(pdf_content)
        assert actual is not None
        assert isinstance(actual, str)

        assert mock_openai_client.create_embeddings.await_count == 2
        mock_embedding_repository.batch_insert_embeddings.assert_awaited_once_with(
            actual,
            [
                (
                    "This is page 1 of 2\nThis is some fake content for testing purposes.\n",
                    [0.1] * 10,
                ),
                (
                    "This is page 2 of 2\nThis is some fake content for testing purposes.\n",
                    [0.1] * 10,
                ),
            ],
        )

    @pytest.mark.asyncio
    async def test_process_pdf_saves_raw_pdf_to_storage(self, subject, mock_storage_repository, mock_openai_client):
        mock_openai_client.create_embeddings.return_value = [0.1] * 10
        pdf_content = generate_fake_pdf_content(num_pages=1)

        doc_id = await subject.process_pdf(pdf_content)

        mock_storage_repository.save.assert_called_once_with(doc_id, pdf_content)

    @pytest.mark.asyncio
    async def test_process_pdf_with_empty_content(self, subject):
        with pytest.raises(ValueError):
            await subject.process_pdf(b"")

    @pytest.mark.asyncio
    async def test_process_pdf_with_invalid_pdf(self, subject):
        with pytest.raises(ValueError):
            await subject.process_pdf(generate_fake_pdf_content(bad_pdf=True))

    @pytest.mark.asyncio
    async def test_exists_returns_true_when_document_found(self, subject, mock_embedding_repository):
        mock_embedding_repository.exists.return_value = True
        assert await subject.exists("doc-123") is True
        mock_embedding_repository.exists.assert_called_once_with("doc-123")

    @pytest.mark.asyncio
    async def test_exists_returns_false_when_document_not_found(self, subject, mock_embedding_repository):
        mock_embedding_repository.exists.return_value = False
        assert await subject.exists("nonexistent-id") is False

    @pytest.mark.asyncio
    async def test_delete_removes_document_from_storage(self, subject, mock_storage_repository):
        await subject.delete("doc-123")

        mock_storage_repository.delete.assert_called_once_with("doc-123")

    @pytest.fixture
    def mock_openai_client(self):
        yield AsyncMock(spec=OpenAIClient)

    @pytest.fixture
    def mock_embedding_repository(self):
        yield AsyncMock(spec=DocumentEmbeddingRepository)

    @pytest.fixture
    def mock_storage_repository(self):
        yield MagicMock(spec=DocumentStorageRepository)

    @pytest.fixture
    def subject(self, mock_openai_client, mock_embedding_repository, mock_storage_repository):
        yield DocumentService(
            repository=mock_embedding_repository,
            client=mock_openai_client,
            storage_repository=mock_storage_repository,
        )
