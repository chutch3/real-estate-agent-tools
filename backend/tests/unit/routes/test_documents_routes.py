from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.exceptions import DocumentNotFoundError
from backend.models import DocumentUploadResponse
from backend.repositories.document_storage import DocumentStorageRepository
from backend.routes.documents import router
from backend.services.document import DocumentService


class TestDocumentRoutes:
    def test_document_upload(self, subject, mock_document_service):
        mock_document_service.process_pdf.return_value = "123"
        response = subject.post(
            "/documents",
            files={"file": ("test.pdf", b"test content", "application/pdf")},
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json() == DocumentUploadResponse(id="123").model_dump()
        mock_document_service.process_pdf.assert_called_once_with(b"test content")

    def test_document_upload_with_unsupported_file(self, subject):
        response = subject.post(
            "/documents",
            files={"file": ("test.txt", b"test content", "text/plain")},
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json() == {"detail": "File must be a PDF"}

    def test_document_upload_with_invalid_pdf(self, subject, mock_document_service):
        mock_document_service.process_pdf.side_effect = Exception("bad pdf")
        response = subject.post(
            "/documents",
            files={"file": ("test.pdf", b"invalid content", "application/pdf")},
        )
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "Error processing PDF: bad pdf"}

    def test_get_document_returns_pdf_content(self, subject, mock_document_storage_repository):
        mock_document_storage_repository.get.return_value = b"%PDF-1.4 fake content"

        response = subject.get("/documents/doc-123")

        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == b"%PDF-1.4 fake content"
        mock_document_storage_repository.get.assert_called_once_with("doc-123")

    def test_get_document_returns_404_when_not_found(self, subject, mock_document_storage_repository):
        mock_document_storage_repository.get.side_effect = DocumentNotFoundError("not found")

        response = subject.get("/documents/nonexistent")

        assert response.status_code == HTTPStatus.NOT_FOUND

    @pytest.fixture
    def mock_document_storage_repository(self):
        yield MagicMock(spec=DocumentStorageRepository)

    @pytest.fixture
    def mock_document_service(self):
        yield AsyncMock(spec=DocumentService)

    @pytest.fixture
    def subject(self, test_container, mock_document_service, mock_document_storage_repository):
        with test_container.override_providers(
            document_service=mock_document_service,
            document_storage_repository=mock_document_storage_repository,
        ):
            app = FastAPI()
            app.include_router(router)
            yield TestClient(app)
