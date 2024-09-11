import io
import random
from typing import Container
from unittest.mock import AsyncMock
from backend.clients.openai import OpenAIClient
from backend.repositories.document_embeddings import DocumentEmbeddingRepository
import pytest
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


def generate_fake_pdf_content(num_pages: int = 2, bad_pdf: bool = False) -> bytes:
    """
    Generate fake PDF content, with a random number of pages.
    """
    if bad_pdf:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(100, 750, "This is a broken PDF")
        c.showPage()
        c.save()
        # Corrupt the PDF by truncating it
        corrupted_pdf = buffer.getvalue()[: len(buffer.getvalue()) // 2]
        return corrupted_pdf

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    for page in range(num_pages):
        c.drawString(100, 750, f"This is page {page + 1} of {num_pages}")
        c.drawString(100, 700, "This is some fake content for testing purposes.")

        # Add some random shapes
        for _ in range(10):
            x, y = random.randint(50, 500), random.randint(50, 700)
            size = random.randint(10, 50)
            c.rect(x, y, size, size, fill=random.choice([0, 1]))

        c.showPage()

    c.save()
    return buffer.getvalue()


class TestDocumentService:
    @pytest.mark.asyncio
    async def test_process_pdf(
        self,
        subject,
        mock_embedding_repository: AsyncMock,
        mock_openai_client: AsyncMock,
    ):
        mock_openai_client.create_embeddings.return_value = [
            0.1,
            0.2,
            0.3,
            0.4,
            0.5,
            0.6,
            0.7,
            0.8,
            0.9,
            1.0,
        ]

        pdf_content = generate_fake_pdf_content()
        actual = await subject.process_pdf(
            pdf_content, {"address": "123 Main St, Anytown, USA"}
        )
        assert actual is not None
        assert isinstance(actual, str)

        mock_embedding_repository.insert_embeddings.assert_called_once_with(
            actual,
            "This is page 1 of 2\nThis is some fake content for testing purposes.\nThis is page 2 of 2\nThis is some fake content for testing purposes.\n",
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        )

    @pytest.mark.asyncio
    async def test_process_pdf_with_empty_content(
        self,
        subject,
    ):
        pdf_content = b""
        with pytest.raises(ValueError):
            await subject.process_pdf(
                pdf_content, {"address": "123 Main St, Anytown, USA"}
            )

    @pytest.mark.asyncio
    async def test_process_pdf_with_invalid_pdf(
        self,
        subject,
    ):
        pdf_content = generate_fake_pdf_content(bad_pdf=True)
        with pytest.raises(ValueError):
            await subject.process_pdf(
                pdf_content, {"address": "123 Main St, Anytown, USA"}
            )

    @pytest.fixture
    def mock_openai_client(self):
        yield AsyncMock(spec=OpenAIClient)

    @pytest.fixture
    def mock_embedding_repository(self):
        yield AsyncMock(spec=DocumentEmbeddingRepository)

    @pytest.fixture
    def subject(
        self,
        test_container: Container,
        mock_openai_client: AsyncMock,
        mock_embedding_repository: AsyncMock,
    ):
        with test_container.override_providers(
            openai_client=mock_openai_client,
            document_embedding_repository=mock_embedding_repository,
        ):
            yield test_container.document_service()
