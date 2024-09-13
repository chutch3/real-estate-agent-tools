import logging

from pymilvus import MilvusClient
from pymilvus.client.types import LoadState

DOCUMENT_EMBEDDINGS_COLLECTION = "document_embeddings"


class DocumentEmbeddingRepository:
    def __init__(self, client: MilvusClient):
        self.client = client
        self._logger = logging.getLogger(self.__class__.__name__)

    def _load_if_needed(self):
        load_state = self.client.get_load_state(DOCUMENT_EMBEDDINGS_COLLECTION)
        if load_state["state"] != LoadState.Loaded:
            self.client.load_collection(DOCUMENT_EMBEDDINGS_COLLECTION)

    async def insert_embeddings(
        self,
        doc_id: str,
        text: str,
        embedding: list[list[float]],
    ) -> None:
        self._load_if_needed()

        self._logger.info(f"Inserting embedding for document {doc_id}")

        inserted = self.client.insert(
            collection_name=DOCUMENT_EMBEDDINGS_COLLECTION,
            data={
                "id": doc_id,
                "text": text,
                "embedding": embedding,
            },
        )
        self._logger.info(f"Inserted {len(inserted['ids'])} embeddings")
        return inserted

    async def query_embeddings(
        self, query_embedding: list[list[float]], limit: int
    ) -> list[dict]:
        self._load_if_needed()

        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = self.client.search(
            collection_name=DOCUMENT_EMBEDDINGS_COLLECTION,
            data=query_embedding,
            anns_field="embedding",
            search_params=search_params,
            limit=limit,
            output_fields=["text"],
        )
        print(results)
        return [{"text": hit[0]["entity"]["text"]} for hit in results]
