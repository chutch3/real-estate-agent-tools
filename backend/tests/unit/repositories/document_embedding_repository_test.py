from unittest.mock import MagicMock

import pytest
from pymilvus import MilvusClient

from backend.repositories.document_embeddings import DocumentEmbeddingRepository


@pytest.fixture
def milvus_client():
    client = MagicMock(spec=MilvusClient)
    client.get_load_state.return_value = {"state": "Loaded"}
    return client


@pytest.mark.asyncio
async def test_insert_embeddings_uses_collection_name(milvus_client):
    subject = DocumentEmbeddingRepository(
        client=milvus_client, collection_name="document_embeddings_nomic_embed_text_768"
    )

    await subject.insert_embeddings("doc-1", "some text", [0.1] * 768)

    milvus_client.insert.assert_called_once()
    assert milvus_client.insert.call_args[1]["collection_name"] == "document_embeddings_nomic_embed_text_768"


@pytest.mark.asyncio
async def test_batch_insert_embeddings_uses_collection_name(milvus_client):
    subject = DocumentEmbeddingRepository(
        client=milvus_client, collection_name="document_embeddings_nomic_embed_text_768"
    )
    chunks = [("text 1", [0.1] * 768), ("text 2", [0.2] * 768)]

    await subject.batch_insert_embeddings("doc-1", chunks)

    milvus_client.insert.assert_called_once()
    assert milvus_client.insert.call_args[1]["collection_name"] == "document_embeddings_nomic_embed_text_768"
    assert milvus_client.insert.call_args[1]["data"] == [
        {"doc_id": "doc-1", "text": "text 1", "embedding": [0.1] * 768},
        {"doc_id": "doc-1", "text": "text 2", "embedding": [0.2] * 768},
    ]


@pytest.mark.asyncio
async def test_exists_uses_collection_name(milvus_client):
    milvus_client.query.return_value = [{"id": "doc-1"}]
    subject = DocumentEmbeddingRepository(
        client=milvus_client, collection_name="document_embeddings_nomic_embed_text_768"
    )

    await subject.exists("doc-1")

    assert milvus_client.query.call_args[1]["collection_name"] == "document_embeddings_nomic_embed_text_768"
