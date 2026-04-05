import os

import pytest

from backend.startup import _configure_gdal


@pytest.fixture(autouse=True)
def isolate_os_environ():
    snapshot = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(snapshot)


def test_configure_gdal_maps_s3_access_key_to_aws_credential(monkeypatch):
    monkeypatch.setenv("S3_ACCESS_KEY", "my-access-key")
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)

    _configure_gdal()

    assert os.environ["AWS_ACCESS_KEY_ID"] == "my-access-key"


def test_configure_gdal_does_not_overwrite_existing_aws_access_key_id(monkeypatch):
    monkeypatch.setenv("S3_ACCESS_KEY", "new-key")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "existing-key")

    _configure_gdal()

    assert os.environ["AWS_ACCESS_KEY_ID"] == "existing-key"


def test_configure_gdal_maps_s3_secret_key_to_aws_credential(monkeypatch):
    monkeypatch.setenv("S3_SECRET_KEY", "my-secret-key")
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    _configure_gdal()

    assert os.environ["AWS_SECRET_ACCESS_KEY"] == "my-secret-key"


def test_configure_gdal_does_not_overwrite_existing_aws_secret_access_key(monkeypatch):
    monkeypatch.setenv("S3_SECRET_KEY", "new-secret")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "existing-secret")

    _configure_gdal()

    assert os.environ["AWS_SECRET_ACCESS_KEY"] == "existing-secret"


def test_configure_gdal_skips_credential_mapping_when_s3_keys_absent(monkeypatch):
    monkeypatch.delenv("S3_ACCESS_KEY", raising=False)
    monkeypatch.delenv("S3_SECRET_KEY", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    _configure_gdal()

    assert "AWS_ACCESS_KEY_ID" not in os.environ
    assert "AWS_SECRET_ACCESS_KEY" not in os.environ


def test_configure_gdal_strips_http_protocol_from_endpoint_url(monkeypatch):
    monkeypatch.setenv("S3_ENDPOINT_URL", "http://localhost:5005")
    monkeypatch.delenv("AWS_S3_ENDPOINT", raising=False)

    _configure_gdal()

    assert os.environ["AWS_S3_ENDPOINT"] == "localhost:5005"


def test_configure_gdal_strips_https_protocol_from_endpoint_url(monkeypatch):
    monkeypatch.setenv("S3_ENDPOINT_URL", "https://custom.s3.example.com")
    monkeypatch.delenv("AWS_S3_ENDPOINT", raising=False)

    _configure_gdal()

    assert os.environ["AWS_S3_ENDPOINT"] == "custom.s3.example.com"


def test_configure_gdal_does_not_overwrite_existing_aws_s3_endpoint(monkeypatch):
    monkeypatch.setenv("S3_ENDPOINT_URL", "http://localhost:5005")
    monkeypatch.setenv("AWS_S3_ENDPOINT", "already-set:9000")

    _configure_gdal()

    assert os.environ["AWS_S3_ENDPOINT"] == "already-set:9000"


def test_configure_gdal_sets_virtual_hosting_false_for_custom_endpoint(monkeypatch):
    monkeypatch.setenv("S3_ENDPOINT_URL", "http://localhost:5005")
    monkeypatch.delenv("AWS_VIRTUAL_HOSTING", raising=False)

    _configure_gdal()

    assert os.environ["AWS_VIRTUAL_HOSTING"] == "FALSE"


def test_configure_gdal_sets_https_no_for_http_endpoint(monkeypatch):
    monkeypatch.setenv("S3_ENDPOINT_URL", "http://localhost:5005")
    monkeypatch.delenv("AWS_HTTPS", raising=False)

    _configure_gdal()

    assert os.environ["AWS_HTTPS"] == "NO"


def test_configure_gdal_does_not_set_https_no_for_https_endpoint(monkeypatch):
    monkeypatch.setenv("S3_ENDPOINT_URL", "https://custom.s3.example.com")
    monkeypatch.delenv("AWS_HTTPS", raising=False)

    _configure_gdal()

    assert "AWS_HTTPS" not in os.environ


def test_configure_gdal_skips_endpoint_config_when_s3_endpoint_url_absent(monkeypatch):
    monkeypatch.delenv("S3_ENDPOINT_URL", raising=False)
    monkeypatch.delenv("AWS_S3_ENDPOINT", raising=False)

    _configure_gdal()

    assert "AWS_S3_ENDPOINT" not in os.environ


def test_configure_gdal_sets_performance_defaults(monkeypatch):
    for key in ("GDAL_DISABLE_READDIR_ON_OPEN", "CPL_VSIL_CURL_CACHE_SIZE", "GDAL_HTTP_MAX_RETRY", "GDAL_NUM_THREADS"):
        monkeypatch.delenv(key, raising=False)

    _configure_gdal()

    assert os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] == "EMPTY_DIR"
    assert os.environ["CPL_VSIL_CURL_CACHE_SIZE"] == str(100 * 1024 * 1024)
    assert os.environ["GDAL_HTTP_MAX_RETRY"] == "3"
    assert os.environ["GDAL_NUM_THREADS"] == "ALL_CPUS"


def test_configure_gdal_does_not_overwrite_existing_performance_settings(monkeypatch):
    monkeypatch.setenv("GDAL_DISABLE_READDIR_ON_OPEN", "YES")
    monkeypatch.setenv("GDAL_NUM_THREADS", "4")

    _configure_gdal()

    assert os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] == "YES"
    assert os.environ["GDAL_NUM_THREADS"] == "4"
