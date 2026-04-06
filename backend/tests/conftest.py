import subprocess
import time
import urllib.request
import uuid
from pathlib import Path

import boto3
import pytest

from backend.container import Container
from tests.factories import (
    PropertyInfoFactory,  # noqa: F401 — registers property_info_factory fixture
)

COMPOSE_FILE = Path(__file__).parent / "docker-compose.yml"
MILVUS_HEALTH_URL = "http://localhost:9091/healthz"
MOTO_SERVER_URL = "http://localhost:5005"
S3_TEST_BUCKET = "test-documents"


def _wait_for_milvus(timeout: int = 120, interval: int = 2):
    from pymilvus import MilvusClient

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(MILVUS_HEALTH_URL, timeout=2) as resp:
                if resp.status != 200:
                    raise Exception("not ready")
            # HTTP health passed — verify gRPC is also ready
            client = MilvusClient(uri="http://localhost:19530")
            client.list_collections()
            client.close()
            return
        except Exception:
            pass
        time.sleep(interval)
    raise TimeoutError(f"Milvus did not become healthy within {timeout}s")


def _wait_for_motoserver(timeout: int = 30, interval: int = 1):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(MOTO_SERVER_URL, timeout=2) as resp:
                if resp.status in (200, 400, 404):
                    return
        except Exception:
            pass
        time.sleep(interval)
    raise TimeoutError(f"Moto server did not become ready within {timeout}s")


def _create_test_s3_bucket():
    client = boto3.client(
        "s3",
        endpoint_url=MOTO_SERVER_URL,
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    client.create_bucket(Bucket=S3_TEST_BUCKET)


@pytest.fixture(scope="session")
def integration_services():
    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "down", "-v"],
        check=True,
    )
    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d"],
        check=True,
    )
    _wait_for_milvus()
    _wait_for_motoserver()
    _create_test_s3_bucket()
    yield
    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "down", "-v"],
        check=True,
    )


@pytest.fixture
def test_container():
    return Container()


@pytest.fixture
def random_database_name():
    return str(uuid.uuid4())
