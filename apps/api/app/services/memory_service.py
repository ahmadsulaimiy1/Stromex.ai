"""The memory system: Postgres is the system of record (list/edit/delete,
ownership, auditability); Qdrant holds only the embedding for similarity
search, keyed by the same id Postgres uses. Every write goes to both stores
in the same call, so they never drift silently out of sync — StromeX Editorial
Bible, Part VII: 'all user-visible, exportable, and independently deletable.'
"""

import uuid

from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue, PointStruct
from sqlalchemy.orm import Session

from app.db.models.memory import MemoryItem, MemoryTier
from app.services import qdrant_client as qdrant_module
from app.services.embeddings import get_embedding_provider

# Called as `qdrant_module.get_qdrant()` (module-qualified, not imported by
# name) so tests can monkeypatch `qdrant_module.get_qdrant` and have it take
# effect here — a direct `from ... import get_qdrant` would bind the original
# function at import time and silently ignore the monkeypatch.
ensure_collection = qdrant_module.ensure_collection

_COLLECTION_PREFIX = "stromex_memories"


def _collection_name(dimension: int) -> str:
    return f"{_COLLECTION_PREFIX}_{dimension}"


async def create_memory(
    db: Session,
    *,
    user_id: uuid.UUID,
    tier: MemoryTier,
    summary: str,
    project_ref: str | None = None,
    source_conversation_id: uuid.UUID | None = None,
    importance: float = 0.5,
) -> MemoryItem:
    embedder = get_embedding_provider()
    vector = await embedder.embed(summary)

    client = qdrant_module.get_qdrant()
    collection = _collection_name(embedder.dimension)
    ensure_collection(client, collection, embedder.dimension)

    point_id = str(uuid.uuid4())
    client.upsert(
        collection_name=collection,
        points=[
            PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "user_id": str(user_id),
                    "tier": tier.value,
                    "project_ref": project_ref,
                },
            )
        ],
    )

    item = MemoryItem(
        user_id=user_id,
        tier=tier,
        project_ref=project_ref,
        source_conversation_id=source_conversation_id,
        summary=summary,
        importance=importance,
        qdrant_point_id=point_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


async def search_memory(
    db: Session,
    *,
    user_id: uuid.UUID,
    query: str,
    tiers: list[MemoryTier] | None = None,
    project_ref: str | None = None,
    limit: int = 8,
) -> list[tuple[MemoryItem, float]]:
    embedder = get_embedding_provider()
    collection = _collection_name(embedder.dimension)
    client = qdrant_module.get_qdrant()
    if not client.collection_exists(collection):
        return []

    must = [FieldCondition(key="user_id", match=MatchValue(value=str(user_id)))]
    if tiers:
        must.append(FieldCondition(key="tier", match=MatchAny(any=[t.value for t in tiers])))
    if project_ref:
        must.append(FieldCondition(key="project_ref", match=MatchValue(value=project_ref)))

    vector = await embedder.embed(query)
    hits = client.query_points(
        collection_name=collection,
        query=vector,
        query_filter=Filter(must=must),
        limit=limit,
    ).points

    if not hits:
        return []

    point_ids = [str(hit.id) for hit in hits]
    rows = (
        db.query(MemoryItem)
        .filter(MemoryItem.qdrant_point_id.in_(point_ids), MemoryItem.user_id == user_id)
        .all()
    )
    by_point_id = {row.qdrant_point_id: row for row in rows}

    results: list[tuple[MemoryItem, float]] = []
    for hit in hits:
        row = by_point_id.get(str(hit.id))
        if row is not None:
            results.append((row, hit.score))
    return results


def delete_memory(db: Session, *, user_id: uuid.UUID, memory_id: uuid.UUID) -> bool:
    item = db.get(MemoryItem, memory_id)
    if item is None or item.user_id != user_id:
        return False

    embedder = get_embedding_provider()
    collection = _collection_name(embedder.dimension)
    client = qdrant_module.get_qdrant()
    if client.collection_exists(collection):
        client.delete(collection_name=collection, points_selector=[item.qdrant_point_id])

    db.delete(item)
    db.commit()
    return True
