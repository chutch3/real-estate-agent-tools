import os
import subprocess
import time
import urllib.request
from pathlib import Path

import boto3
import pytest

os.environ.setdefault("PREFECT_LOGGING_TO_API_WHEN_MISSING_FLOW", "ignore")

_COMPOSE_FILE = Path(__file__).parent / "docker-compose.yml"
_MOTO_URL = "http://localhost:5006"
_TEST_BUCKET = "crime-data"
_AWS_ACCESS_KEY = "test"
_AWS_SECRET_KEY = "testpassword"
_AWS_REGION = "us-east-1"


def _wait_for_motoserver(timeout: int = 30) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            # MinIO health check endpoint
            with urllib.request.urlopen(f"{_MOTO_URL}/minio/health/live", timeout=1) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(1)
    raise RuntimeError(f"minio did not become ready within {timeout}s")


@pytest.fixture(scope="session")
def integration_services():
    subprocess.run(
        ["docker", "compose", "-f", str(_COMPOSE_FILE), "up", "-d"],
        check=True,
    )
    _wait_for_motoserver()
    yield
    subprocess.run(
        ["docker", "compose", "-f", str(_COMPOSE_FILE), "down", "-v"],
        check=True,
    )


@pytest.fixture
def s3_client(integration_services):
    client = boto3.client(
        "s3",
        endpoint_url=_MOTO_URL,
        aws_access_key_id=_AWS_ACCESS_KEY,
        aws_secret_access_key=_AWS_SECRET_KEY,
        region_name=_AWS_REGION,
    )
    client.create_bucket(Bucket=_TEST_BUCKET)
    yield client
    response = client.list_objects_v2(Bucket=_TEST_BUCKET)
    for obj in response.get("Contents", []):
        client.delete_object(Bucket=_TEST_BUCKET, Key=obj["Key"])
    client.delete_bucket(Bucket=_TEST_BUCKET)
