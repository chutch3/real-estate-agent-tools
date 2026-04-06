import random
from collections.abc import Container

import pytest
from pymilvus import MilvusClient

from backend.repositories.document_embeddings import DocumentEmbeddingRepository
from backend.schema import (
    create_document_embeddings_schema,
    drop_document_embeddings_schema,
)


def generate_simple_embedding(text: str, dimension: int = 1536) -> list[float]:
    """
    Generate a simple embedding based on the input text.
    This is not a real embedding, just a deterministic way to generate a vector for testing.
    """
    # Use the hash of the text as a seed for reproducibility
    random.seed(hash(text))
    return [random.uniform(-1, 1) for _ in range(dimension)]


class TestDocumentEmbeddingRepository:
    @pytest.mark.asyncio
    async def test_insert_embeddings(
        self,
        subject: DocumentEmbeddingRepository,
        milvus_client: MilvusClient,
        test_container: Container,
    ):
        collection_name = test_container.embeddings_collection_name()
        actual = await subject.insert_embeddings("1", "test", [1.0] * 1536)
        assert actual["insert_count"] == 1
        query_results = milvus_client.query(collection_name=collection_name, filter='doc_id == "1"')
        assert len(query_results) == 1
        assert query_results[0]["doc_id"] == "1"
        assert query_results[0]["text"] == "test"
        assert query_results[0]["embedding"] == [1.0] * 1536

    @pytest.mark.parametrize(
        "document_contents,search_text,limit,expected",
        [
            (
                [
                    "test",
                    "test again",
                ],
                "test",
                1,
                [{"text": "test"}],
            ),
            (
                [
                    "some other text content",
                    "some different text content",
                ],
                "some different text content",
                2,
                [
                    {"text": "some different text content"},
                    {"text": "some other text content"},
                ],
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_query_embeddings(
        self,
        subject: DocumentEmbeddingRepository,
        milvus_client: MilvusClient,
        test_container: Container,
        document_contents: list[str],
        search_text: str,
        limit: int,
        expected: list[dict],
    ):
        collection_name = test_container.embeddings_collection_name()
        milvus_client.insert(
            collection_name=collection_name,
            data=[
                {
                    "doc_id": str(i),
                    "text": content,
                    "embedding": generate_simple_embedding(content),
                }
                for i, content in enumerate(document_contents)
            ],
        )
        actual = await subject.query_embeddings([generate_simple_embedding(search_text)], limit)
        assert len(actual) == len(expected)
        assert all(text in actual for text in expected)

    @pytest.mark.asyncio
    async def test_exists_returns_true_when_document_found(
        self,
        subject: DocumentEmbeddingRepository,
        milvus_client: MilvusClient,
        test_container: Container,
    ):
        collection_name = test_container.embeddings_collection_name()
        milvus_client.insert(
            collection_name=collection_name,
            data=[{"doc_id": "doc-123", "text": "test", "embedding": [1.0] * 1536}],
        )
        assert await subject.exists("doc-123") is True

    @pytest.mark.asyncio
    async def test_batch_insert_embeddings(
        self,
        subject: DocumentEmbeddingRepository,
        milvus_client: MilvusClient,
        test_container: Container,
    ):
        collection_name = test_container.embeddings_collection_name()
        chunks = [
            ("page one", [1.0] * 1536),
            ("page two", [0.5] * 1536),
        ]

        result = await subject.batch_insert_embeddings("doc-batch", chunks)

        assert result["insert_count"] == 2
        query_results = milvus_client.query(
            collection_name=collection_name,
            filter='doc_id == "doc-batch"',
            output_fields=["text"],
        )
        assert len(query_results) == 2
        assert any(r["text"] == "page one" for r in query_results)
        assert any(r["text"] == "page two" for r in query_results)

    @pytest.mark.asyncio
    async def test_exists_returns_false_when_document_not_found(
        self, subject: DocumentEmbeddingRepository, milvus_client: MilvusClient
    ):
        assert await subject.exists("nonexistent-id") is False

    @pytest.fixture
    def milvus_client(self, test_container: Container):
        yield test_container.milvus_client()

    @pytest.fixture
    def subject(self, test_container: Container, integration_services):
        test_container.config.milvus.uri.from_value("http://localhost:19530")
        test_container.config.openai.embeddings_model.from_value("text-embedding-ada-002")
        test_container.config.openai.embeddings_dimension.from_value(1536)
        create_document_embeddings_schema()
        yield test_container.document_embedding_repository()
        drop_document_embeddings_schema()
