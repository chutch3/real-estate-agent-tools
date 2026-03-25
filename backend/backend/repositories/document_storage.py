import logging

from botocore.exceptions import ClientError

from backend.exceptions import DocumentNotFoundError


class DocumentStorageRepository:
    def __init__(self, client, bucket_name: str):
        self._client = client
        self._bucket_name = bucket_name
        self._logger = logging.getLogger(self.__class__.__name__)

    def save(self, doc_id: str, content: bytes) -> None:
        self._logger.info(f"Saving document {doc_id} to S3")
        self._client.put_object(
            Bucket=self._bucket_name,
            Key=f"{doc_id}.pdf",
            Body=content,
            ContentType="application/pdf",
        )

    def get(self, doc_id: str) -> bytes:
        try:
            response = self._client.get_object(
                Bucket=self._bucket_name,
                Key=f"{doc_id}.pdf",
            )
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                raise DocumentNotFoundError(f"Document {doc_id} not found")
            raise

    def delete(self, doc_id: str) -> None:
        self._logger.info(f"Deleting document {doc_id} from S3")
        self._client.delete_object(
            Bucket=self._bucket_name,
            Key=f"{doc_id}.pdf",
        )

    def ensure_bucket_exists(self) -> None:
        try:
            self._client.head_bucket(Bucket=self._bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchBucket"):
                self._logger.info(f"Creating bucket {self._bucket_name}")
                self._client.create_bucket(Bucket=self._bucket_name)
            else:
                raise
