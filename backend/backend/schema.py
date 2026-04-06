import logging
import time

from dependency_injector.wiring import Provide, inject
from pymilvus import CollectionSchema, DataType, FieldSchema, MilvusClient

from backend.container import Container

logger = logging.getLogger(__name__)


@inject
def create_document_embeddings_schema(
    milvus_client: MilvusClient = Provide[Container.milvus_client],
    name: str = Provide[Container.embeddings_collection_name],
    dim: int = Provide[Container.config.openai.embeddings_dimension],
) -> None:
    if milvus_client.has_collection(name):
        logger.info(f"Collection {name} already exists")
        return

    schema = CollectionSchema(
        fields=[
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True,
            ),
            FieldSchema(
                name="doc_id",
                dtype=DataType.VARCHAR,
                max_length=36,
            ),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        ]
    )
    index_params = MilvusClient.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        metric_type="L2",
        index_type="IVF_FLAT",
        index_name="embedding_index",
        params={"nlist": 1024},
    )

    last_exc = None
    for attempt in range(5):
        try:
            collection = milvus_client.create_collection(
                collection_name=name,
                consistency_level="Strong",
                schema=schema,
            )
            milvus_client.create_index(
                collection_name=name,
                index_params=index_params,
            )
            logger.info(f"Collection {name} created")
            return collection
        except Exception as exc:
            last_exc = exc
            logger.warning(f"create_collection attempt {attempt + 1} failed: {exc}. Retrying...")
            time.sleep(5)

    raise last_exc


@inject
def drop_document_embeddings_schema(
    milvus_client: MilvusClient = Provide[Container.milvus_client],
    name: str = Provide[Container.embeddings_collection_name],
) -> None:
    milvus_client.drop_collection(name)
    logger.info(f"Collection {name} dropped")
