from pymilvus import MilvusClient


class DocumentEmbeddingRepository:
    def __init__(self, client: MilvusClient, collection_name: str):
        self.client = client
        self.collection_name = collection_name

    async def insert_embeddings(
        self,
        doc_id: str,
        text: str,
        embedding: list[list[float]],
    ) -> None:
        inserted = self.client.insert(
            collection_name=self.collection_name,
            data={
                "id": doc_id,
                "text": text,
                "embedding": embedding,
            },
        )
        return inserted

    async def query_embeddings(
        self, query_embedding: list[list[float]], limit: int
    ) -> list[dict]:
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = self.client.search(
            collection_name=self.collection_name,
            data=query_embedding,
            anns_field="embedding",
            search_params=search_params,
            limit=limit,
            output_fields=["text"],
        )
        print(results)
        return [{"text": hit[0]["entity"]["text"]} for hit in results]
