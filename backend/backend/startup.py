from dependency_injector.wiring import Provide, inject

from backend.container import Container
from backend.repositories.document_storage import DocumentStorageRepository
from backend.schema import create_document_embeddings_schema


@inject
def _on_startup(
    document_storage_repository: DocumentStorageRepository = Provide[Container.document_storage_repository],
) -> None:
    create_document_embeddings_schema()
    document_storage_repository.ensure_bucket_exists()
