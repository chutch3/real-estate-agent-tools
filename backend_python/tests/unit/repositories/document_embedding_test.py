import random
from typing import Container

import pytest
from backend.repositories.document_embeddings import DocumentEmbeddingRepository
from pymilvus import MilvusClient


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
        self, subject: DocumentEmbeddingRepository, milvus_client: MilvusClient
    ):
        actual = await subject.insert_embeddings(
            "1",
            "test",
            [1.0] * 1536,
        )
        assert actual["insert_count"] == 1
        assert actual["ids"] == ["1"]
        assert milvus_client.query(collection_name="test", ids=actual["ids"]) == [
            {"id": "1", "text": "test", "embedding": [1.0] * 1536}
        ]

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
                "different text content",
                2,
                [
                    {"text": "some different text content"},
                    # {"text": "some other text content"},
                ],
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_query_embeddings(
        self,
        subject: DocumentEmbeddingRepository,
        milvus_client: MilvusClient,
        document_contents: list[str],
        search_text: str,
        limit: int,
        expected: list[dict],
    ):
        milvus_client.insert(
            collection_name="test",
            data=[
                {
                    "id": str(i),
                    "text": content,
                    "embedding": generate_simple_embedding(content),
                }
                for i, content in enumerate(document_contents)
            ],
        )
        actual = await subject.query_embeddings(
            [generate_simple_embedding(search_text)], limit
        )
        # assert all(text in actual for text in expected)
        assert len(actual) == len(expected)
        print(actual)
        print(expected)
        assert all(text in actual for text in expected)

    @pytest.fixture
    def milvus_client(self, test_container: Container):
        client = test_container.milvus_client()
        yield client
        # client.delete(collection_name="test", ids=["1", "2", "3"])

    @pytest.fixture
    def subject(self, test_container: Container):
        test_container.config.milvus.uri.from_value("http://localhost:19530")
        test_container.config.milvus.collection_name.from_value("test")
        yield test_container.document_embedding_repository()
