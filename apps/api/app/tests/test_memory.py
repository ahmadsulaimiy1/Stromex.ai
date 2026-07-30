import pytest

from app.db.models.memory import MemoryTier
from app.services import memory_service


@pytest.mark.asyncio
async def test_create_and_search_memory_round_trip(db_session, in_memory_qdrant, make_user):
    user_id = make_user()

    about_book = await memory_service.create_memory(
        db_session,
        user_id=user_id,
        tier=MemoryTier.USER,
        summary="The user is writing a bilingual book about trustworthy AI.",
    )
    about_arabic = await memory_service.create_memory(
        db_session,
        user_id=user_id,
        tier=MemoryTier.USER,
        summary="The user prefers Modern Standard Arabic over dialect for formal writing.",
    )

    results = await memory_service.search_memory(
        db_session, user_id=user_id, query="What book is the user writing?", limit=5
    )

    assert len(results) == 2
    top_match, top_score = results[0]
    assert top_match.id == about_book.id
    assert top_score >= results[1][1]  # the book-related memory should rank first
    assert about_arabic.id in {row.id for row, _ in results}


@pytest.mark.asyncio
async def test_search_is_scoped_to_the_requesting_user(db_session, in_memory_qdrant, make_user):
    user_a = make_user()
    user_b = make_user()

    await memory_service.create_memory(
        db_session, user_id=user_a, tier=MemoryTier.USER, summary="User A likes tea."
    )
    await memory_service.create_memory(
        db_session, user_id=user_b, tier=MemoryTier.USER, summary="User B likes tea."
    )

    results = await memory_service.search_memory(db_session, user_id=user_a, query="tea", limit=10)

    assert len(results) == 1
    assert results[0][0].user_id == user_a


@pytest.mark.asyncio
async def test_delete_memory_removes_it_from_search(db_session, in_memory_qdrant, make_user):
    user_id = make_user()
    item = await memory_service.create_memory(
        db_session, user_id=user_id, tier=MemoryTier.USER, summary="Temporary fact to delete."
    )

    deleted = memory_service.delete_memory(db_session, user_id=user_id, memory_id=item.id)
    assert deleted is True

    results = await memory_service.search_memory(
        db_session, user_id=user_id, query="Temporary fact", limit=5
    )
    assert results == []


@pytest.mark.asyncio
async def test_delete_memory_rejects_wrong_owner(db_session, in_memory_qdrant, make_user):
    owner = make_user()
    attacker = make_user()
    item = await memory_service.create_memory(
        db_session, user_id=owner, tier=MemoryTier.USER, summary="Owned by someone else."
    )

    deleted = memory_service.delete_memory(db_session, user_id=attacker, memory_id=item.id)
    assert deleted is False


@pytest.mark.asyncio
async def test_tier_filter_excludes_other_tiers(db_session, in_memory_qdrant, make_user):
    user_id = make_user()
    await memory_service.create_memory(
        db_session, user_id=user_id, tier=MemoryTier.CONVERSATION, summary="Ephemeral detail."
    )
    await memory_service.create_memory(
        db_session, user_id=user_id, tier=MemoryTier.LONG_TERM, summary="Durable knowledge."
    )

    results = await memory_service.search_memory(
        db_session, user_id=user_id, query="detail", tiers=[MemoryTier.LONG_TERM], limit=10
    )

    assert len(results) == 1
    assert results[0][0].tier == MemoryTier.LONG_TERM
