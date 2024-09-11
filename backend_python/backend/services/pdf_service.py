import io
import uuid
import PyPDF2
from typing import List, Dict
import openai
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType


class PDFService:
    def __init__(self, milvus_host: str, milvus_port: int, openai_api_key: str):
        connections.connect(host=milvus_host, port=milvus_port)
        self.collection = self._get_or_create_collection()
        openai.api_key = openai_api_key

    def _get_or_create_collection(self):
        collection_name = "property_docs"
        if Collection.has_collection(collection_name):
            return Collection(collection_name)

        fields = [
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
        schema = CollectionSchema(fields, "Property documents collection")
        collection = Collection(collection_name, schema)
        collection.create_index(
            field_name="embedding",
            index_params={
                "index_type": "IVF_FLAT",
                "metric_type": "L2",
                "params": {"nlist": 1024},
            },
        )
        return collection

    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text

    def create_embeddings(self, text: str) -> List[float]:
        response = openai.Embedding.create(input=[text], model="text-embedding-ada-002")
        return response["data"][0]["embedding"]

    def process_and_store_pdf(
        self, pdf_content: bytes, metadata: Dict[str, str]
    ) -> str:
        text = self.extract_text_from_pdf(pdf_content)
        embedding = self.create_embeddings(text)

        doc_id = str(uuid.uuid4())
        self.collection.insert([[doc_id], [text], [embedding]])
        return doc_id

    def retrieve_similar_chunks(
        self, query: str, top_k: int = 5
    ) -> List[Dict[str, str]]:
        query_embedding = self.create_embeddings(query)
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = self.collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text"],
        )
        return [{"text": hit.entity.get("text")} for hit in results[0]]
