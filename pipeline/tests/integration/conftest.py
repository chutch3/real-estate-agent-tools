from pathlib import Path

import pytest
from prefect.settings import PREFECT_LOCAL_STORAGE_PATH
from prefect.testing.utilities import prefect_test_harness


@pytest.fixture(scope="module", autouse=True)
def prefect_harness():
    with prefect_test_harness():
        yield


@pytest.fixture(autouse=True)
def clear_prefect_task_cache(prefect_harness):
    """Delete all persisted task result files before each test so cached results
    from one test cannot pollute another.

    Prefect stores results at PREFECT_LOCAL_STORAGE_PATH using the cache key as
    the filename. Deleting those files before each test ensures a clean cache
    state without changing any Prefect settings.
    """
    storage_path = Path(PREFECT_LOCAL_STORAGE_PATH.value())
    storage_path.mkdir(parents=True, exist_ok=True)
    for f in storage_path.glob("*"):
        if f.is_file():
            f.unlink()
    yield
