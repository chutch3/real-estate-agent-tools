import logging
from typing import List, Optional

from pymilvus import MilvusClient
from pymilvus.client.types import LoadState

class DocumentEmbeddingRepository:
    def __init__(self, client: MilvusClient, collection_name: str):
        self.client = client
        self._collection_name = collection_name
        self._logger = logging.getLogger(self.__class__.__name__)

    def _load_if_needed(self):
        load_state = self.client.get_load_state(self._collection_name)
        if load_state["state"] != LoadState.Loaded:
            self.client.load_collection(self._collection_name)

    async def insert_embeddings(
        self,
        doc_id: str,
        text: str,
        embedding: list[float],
    ) -> None:
        self._load_if_needed()

        self._logger.info(f"Inserting embedding for document {doc_id}")

        inserted = self.client.insert(
            collection_name=self._collection_name,
            data=[{
                "doc_id": doc_id,
                "text": text,
                "embedding": embedding,
            }],
        )
        self._logger.info(f"Inserted {len(inserted['ids'])} embeddings")
        return inserted

    async def batch_insert_embeddings(
        self,
        doc_id: str,
        chunks: list[tuple[str, list[float]]],
    ):
        self._load_if_needed()

        data = [
            {"doc_id": doc_id, "text": text, "embedding": embedding}
            for text, embedding in chunks
        ]
        inserted = self.client.insert(
            collection_name=self._collection_name,
            data=data,
        )
        self._logger.info(f"Inserted {len(inserted['ids'])} embeddings for document {doc_id}")
        return inserted

    async def exists(self, doc_id: str) -> bool:
        self._load_if_needed()
        results = self.client.query(
            collection_name=self._collection_name,
            filter=f'doc_id == "{doc_id}"',
            limit=1,
        )
        return len(results) > 0

    async def query_embeddings(
        self,
        query_embedding: List[List[float]],
        limit: int,
        filter_ids: Optional[List[str]] = None,
    ) -> List[dict]:
        self._load_if_needed()

        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        filter_expr = None
        if filter_ids:
            ids_str = ", ".join(f'"{i}"' for i in filter_ids)
            filter_expr = f"doc_id in [{ids_str}]"

        results = self.client.search(
            collection_name=self._collection_name,
            data=query_embedding,
            anns_field="embedding",
            search_params=search_params,
            limit=limit,
            output_fields=["text"],
            filter=filter_expr,
        )
        if not results or not results[0]:
            return []
        return [{"text": hit["entity"]["text"]} for hit in results[0]]
