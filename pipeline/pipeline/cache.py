import hashlib
from typing import Any

import cloudpickle

CACHE_VERSIONS: dict[str, str] = {
    "fetch_raw": "v1",
    "geocode_batch": "v1",
    "geocode_records": "v1",
    "compute_kde_grid": "v1",
    "write_cog": "v2",
}


def make_cache_key(task_name: str):
    def cache_key_fn(task_run_context: Any, parameters: dict) -> str:
        version = CACHE_VERSIONS[task_name]
        params_hash = hashlib.md5(cloudpickle.dumps(parameters, protocol=4)).hexdigest()
        return f"{task_name}:{version}:{params_hash}"

    return cache_key_fn
