import logging
from pymilvus import CollectionSchema, DataType, FieldSchema, MilvusClient
from pymilvus.milvus_client.index import IndexParams
from dependency_injector.wiring import inject, Provide
from backend.container import Container

logger = logging.getLogger(__name__)

COLLECTION_NAME = "document_embeddings"


@inject
def create_document_embeddings_schema(
    milvus_client: MilvusClient = Provide[Container.milvus_client],
) -> None:
    if milvus_client.has_collection(COLLECTION_NAME):
        logger.info(f"Collection {COLLECTION_NAME} already exists")
        return

    collection = milvus_client.create_collection(
        collection_name=COLLECTION_NAME,
        schema=CollectionSchema(
            fields=[
                FieldSchema(
                    name="id",
                    dtype=DataType.VARCHAR,
                    is_primary=True,
                    auto_id=False,
                    max_length=36,
                ),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
            ]
        ),
    )

    index_params = MilvusClient.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        metric_type="L2",
        index_type="IVF_FLAT",
        index_name="embedding_index",
        params={"nlist": 1024},
    )

    milvus_client.create_index(
        collection_name=COLLECTION_NAME,
        index_params=index_params,
    )

    logger.info(f"Collection {COLLECTION_NAME} created")
    return collection


@inject
def drop_document_embeddings_schema(
    milvus_client: MilvusClient = Provide[Container.milvus_client],
) -> None:
    milvus_client.drop_collection(COLLECTION_NAME)
    logger.info(f"Collection {COLLECTION_NAME} dropped")
