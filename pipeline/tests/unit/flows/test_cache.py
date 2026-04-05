from pipeline.cache import CACHE_VERSIONS, make_cache_key


def test_cache_key_includes_task_name():
    key_fn = make_cache_key("fetch_raw")
    key = key_fn(None, {"date_from": "2025-01-01"})
    assert "fetch_raw" in key


def test_cache_key_includes_version():
    key_fn = make_cache_key("fetch_raw")
    key = key_fn(None, {"date_from": "2025-01-01"})
    assert CACHE_VERSIONS["fetch_raw"] in key


def test_cache_key_same_inputs_produce_same_key():
    key_fn = make_cache_key("fetch_raw")
    params = {"date_from": "2025-01-01", "date_to": "2025-12-31"}
    assert key_fn(None, params) == key_fn(None, params)


def test_cache_key_different_inputs_produce_different_keys():
    key_fn = make_cache_key("fetch_raw")
    key1 = key_fn(None, {"date_from": "2025-01-01"})
    key2 = key_fn(None, {"date_from": "2025-06-01"})
    assert key1 != key2


def test_cache_key_different_versions_produce_different_keys():
    params = {"date_from": "2025-01-01"}
    original = CACHE_VERSIONS["fetch_raw"]
    try:
        CACHE_VERSIONS["fetch_raw"] = "v999"
        key_v999 = make_cache_key("fetch_raw")(None, params)
        CACHE_VERSIONS["fetch_raw"] = original
        key_v1 = make_cache_key("fetch_raw")(None, params)
    finally:
        CACHE_VERSIONS["fetch_raw"] = original

    assert key_v1 != key_v999


def test_all_cacheable_tasks_have_version_entries():
    expected_tasks = {"fetch_raw", "geocode_batch", "geocode_records", "compute_kde_grid", "write_cog"}
    assert set(CACHE_VERSIONS.keys()) == expected_tasks
