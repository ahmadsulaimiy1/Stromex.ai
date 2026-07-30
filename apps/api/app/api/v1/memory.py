import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.base import get_db
from app.db.models.user import User
from app.schemas.memory import (
    MemoryCreate,
    MemoryRead,
    MemorySearchRequest,
    MemorySearchResult,
)
from app.services import memory_service

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("", response_model=MemoryRead, status_code=status.HTTP_201_CREATED)
async def create_memory(
    payload: MemoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> memory_service.MemoryItem:
    return await memory_service.create_memory(
        db,
        user_id=user.id,
        tier=payload.tier,
        summary=payload.summary,
        project_ref=payload.project_ref,
        source_conversation_id=payload.source_conversation_id,
        importance=payload.importance,
    )


@router.post("/search", response_model=list[MemorySearchResult])
async def search_memory(
    payload: MemorySearchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[MemorySearchResult]:
    results = await memory_service.search_memory(
        db,
        user_id=user.id,
        query=payload.query,
        tiers=payload.tiers,
        project_ref=payload.project_ref,
        limit=payload.limit,
    )
    return [MemorySearchResult(memory=item, score=score) for item, score in results]


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(
    memory_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    deleted = memory_service.delete_memory(db, user_id=user.id, memory_id=memory_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")
