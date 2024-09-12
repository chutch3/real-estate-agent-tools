from pymilvus import CollectionSchema, DataType, FieldSchema
from pymilvus.milvus_client.index import IndexParams

document_embeddings_schema = CollectionSchema(
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
)
document_embeddings_index_params = IndexParams(
    field_name="embedding",
    index_type="IVF_FLAT",
    metric_type="L2",
    params={"nlist": 1024},
)
