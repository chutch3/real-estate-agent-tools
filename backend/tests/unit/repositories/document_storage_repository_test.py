import boto3
import pytest
from moto import mock_aws

from backend.exceptions import DocumentNotFoundError
from backend.repositories.document_storage import DocumentStorageRepository


class TestDocumentStorageRepository:
    @pytest.fixture
    def s3_client(self):
        with mock_aws():
            client = boto3.client(
                "s3",
                region_name="us-east-1",
                aws_access_key_id="test",
                aws_secret_access_key="test",
            )
            client.create_bucket(Bucket="test-documents")
            yield client

    @pytest.fixture
    def subject(self, s3_client):
        yield DocumentStorageRepository(client=s3_client, bucket_name="test-documents")

    def test_save_stores_pdf_in_s3(self, subject, s3_client):
        content = b"%PDF-1.4 fake pdf content"
        subject.save("doc-1", content)

        response = s3_client.get_object(Bucket="test-documents", Key="doc-1.pdf")
        assert response["Body"].read() == content

    def test_save_sets_pdf_content_type(self, subject, s3_client):
        subject.save("doc-1", b"%PDF fake")

        response = s3_client.head_object(Bucket="test-documents", Key="doc-1.pdf")
        assert response["ContentType"] == "application/pdf"

    def test_get_retrieves_stored_pdf(self, subject):
        content = b"%PDF-1.4 some content"
        subject.save("doc-2", content)

        result = subject.get("doc-2")
        assert result == content

    def test_get_raises_document_not_found_for_unknown_id(self, subject):
        with pytest.raises(DocumentNotFoundError):
            subject.get("nonexistent-id")

    def test_delete_removes_pdf_from_s3(self, subject, s3_client):
        subject.save("doc-3", b"%PDF delete me")
        subject.delete("doc-3")

        with pytest.raises(DocumentNotFoundError):
            subject.get("doc-3")

    def test_delete_does_not_raise_when_key_does_not_exist(self, subject):
        subject.delete("never-uploaded")  # should not raise

    def test_ensure_bucket_exists_creates_bucket_when_missing(self, s3_client):
        subject = DocumentStorageRepository(client=s3_client, bucket_name="new-bucket")
        subject.ensure_bucket_exists()

        buckets = [b["Name"] for b in s3_client.list_buckets()["Buckets"]]
        assert "new-bucket" in buckets

    def test_ensure_bucket_exists_is_idempotent(self, subject):
        subject.ensure_bucket_exists()
        subject.ensure_bucket_exists()  # should not raise
