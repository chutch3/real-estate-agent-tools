import re


def collection_name(model: str, dim: int) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9]+", "_", model).strip("_")
    return f"document_embeddings_{sanitized}_{dim}"
