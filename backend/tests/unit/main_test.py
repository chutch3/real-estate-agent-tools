import os
from unittest.mock import MagicMock, patch

import pytest

from backend.repositories.document_storage import DocumentStorageRepository
from backend.startup import _on_startup


@pytest.fixture(autouse=True)
def isolate_os_environ():
    snapshot = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(snapshot)


def test_on_startup_creates_document_embeddings_schema(test_container):
    with patch("backend.startup.create_document_embeddings_schema") as mock_create_schema:
        with test_container.override_providers(
            document_storage_repository=MagicMock(spec=DocumentStorageRepository),
        ):
            _on_startup()

    mock_create_schema.assert_called_once()


def test_on_startup_ensures_bucket_exists(test_container):
    mock_storage = MagicMock(spec=DocumentStorageRepository)
    with patch("backend.startup.create_document_embeddings_schema"):
        with test_container.override_providers(
            document_storage_repository=mock_storage,
        ):
            _on_startup()

    mock_storage.ensure_bucket_exists.assert_called_once()
