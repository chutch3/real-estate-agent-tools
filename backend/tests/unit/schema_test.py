from unittest.mock import MagicMock
from pymilvus import MilvusClient
from backend.schema import create_document_embeddings_schema
from backend.embeddings import collection_name


def test_creates_collection_with_default_dimension():
    milvus_client = MagicMock(spec=MilvusClient)
    milvus_client.has_collection.return_value = False

    create_document_embeddings_schema(milvus_client=milvus_client, name="document_embeddings_text_embedding_ada_002_1536", dim=1536)

    schema_arg = milvus_client.create_collection.call_args[1]["schema"]
    embedding_field = next(f for f in schema_arg.fields if f.name == "embedding")
    assert embedding_field.params["dim"] == 1536


def test_creates_collection_with_custom_dimension():
    milvus_client = MagicMock(spec=MilvusClient)
    milvus_client.has_collection.return_value = False

    create_document_embeddings_schema(milvus_client=milvus_client, name="document_embeddings_nomic_embed_text_768", dim=768)

    schema_arg = milvus_client.create_collection.call_args[1]["schema"]
    embedding_field = next(f for f in schema_arg.fields if f.name == "embedding")
    assert embedding_field.params["dim"] == 768


def test_collection_name_sanitizes_model_and_includes_dim():
    assert collection_name("text-embedding-ada-002", 1536) == "document_embeddings_text_embedding_ada_002_1536"


def test_collection_name_sanitizes_colon_in_model():
    assert collection_name("qwen3-embedding:8b", 4096) == "document_embeddings_qwen3_embedding_8b_4096"


def test_creates_collection_with_derived_name():
    milvus_client = MagicMock(spec=MilvusClient)
    milvus_client.has_collection.return_value = False

    create_document_embeddings_schema(milvus_client=milvus_client, name="document_embeddings_nomic_embed_text_768", dim=768)

    call_kwargs = milvus_client.create_collection.call_args[1]
    assert call_kwargs["collection_name"] == "document_embeddings_nomic_embed_text_768"


def test_skips_creation_when_collection_exists():
    milvus_client = MagicMock(spec=MilvusClient)
    milvus_client.has_collection.return_value = True

    create_document_embeddings_schema(milvus_client=milvus_client, name="document_embeddings_text_embedding_ada_002_1536", dim=1536)

    milvus_client.create_collection.assert_not_called()
