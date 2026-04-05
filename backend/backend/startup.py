import os

from dependency_injector.wiring import Provide, inject

from backend.container import Container
from backend.repositories.document_storage import DocumentStorageRepository
from backend.schema import create_document_embeddings_schema


def _configure_gdal() -> None:
    """Configure GDAL global settings from environment.

    Maps application S3 config env vars to GDAL's expected AWS_* variables and
    sets performance defaults that operators can override by pre-setting the vars.

    Key variables (all optional):
      S3_ACCESS_KEY         → AWS_ACCESS_KEY_ID   (for GDAL /vsis3/ credential auth)
      S3_SECRET_KEY         → AWS_SECRET_ACCESS_KEY
      S3_ENDPOINT_URL       → AWS_S3_ENDPOINT (host:port), AWS_VIRTUAL_HOSTING, AWS_HTTPS
      GDAL_DISABLE_READDIR_ON_OPEN  default EMPTY_DIR (skip directory scans on S3)
      CPL_VSIL_CURL_CACHE_SIZE      default 100 MB tile cache
      GDAL_HTTP_MAX_RETRY           default 3 retries on transient failures
      GDAL_NUM_THREADS              default ALL_CPUS for intra-file COG reads
    """
    if access_key := os.getenv("S3_ACCESS_KEY"):
        os.environ.setdefault("AWS_ACCESS_KEY_ID", access_key)
    if secret_key := os.getenv("S3_SECRET_KEY"):
        os.environ.setdefault("AWS_SECRET_ACCESS_KEY", secret_key)

    if endpoint_url := os.getenv("S3_ENDPOINT_URL"):
        gdal_endpoint = endpoint_url.split("://", 1)[-1]
        os.environ.setdefault("AWS_S3_ENDPOINT", gdal_endpoint)
        os.environ.setdefault("AWS_VIRTUAL_HOSTING", "FALSE")
        if endpoint_url.startswith("http://"):
            os.environ.setdefault("AWS_HTTPS", "NO")

    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    os.environ.setdefault("CPL_VSIL_CURL_CACHE_SIZE", str(100 * 1024 * 1024))
    os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "3")
    os.environ.setdefault("GDAL_NUM_THREADS", "ALL_CPUS")


@inject
def _on_startup(
    document_storage_repository: DocumentStorageRepository = Provide[Container.document_storage_repository],
) -> None:
    _configure_gdal()
    create_document_embeddings_schema()
    document_storage_repository.ensure_bucket_exists()
