from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import get_settings


@lru_cache
def get_qdrant() -> QdrantClient:
    settings = get_settings()
    if settings.qdrant_url:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    # Embedded local mode — a real, persistent Qdrant instance backed by local
    # storage, no server process required. Used for local dev and CI; a real
    # deployment should set QDRANT_URL to a running Qdrant service (see infra/).
    return QdrantClient(path=settings.qdrant_local_path or "./.qdrant-local")


def ensure_collection(client: QdrantClient, name: str, dimension: int) -> None:
    if client.collection_exists(name):
        return
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
    )
