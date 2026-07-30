import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.db.base import get_db
from app.db.models.audit import AuditLog
from app.db.models.book import Book
from app.db.models.conversation import Conversation, Message
from app.db.models.quran import QuranPlan
from app.db.models.user import User
from app.schemas.admin import AdminOverview, AdminUserRow, AdminUserUpdate, AuditLogRead

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[AdminUserRow])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}", response_model=AdminUserRow)
def update_user(
    user_id: uuid.UUID,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> User:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(target, field, value)

    db.add(
        AuditLog(
            actor_user_id=admin.id,
            action="admin.user.update",
            resource_type="user",
            resource_id=str(target.id),
            metadata_json=changes,
        )
    )
    db.commit()
    db.refresh(target)
    return target


@router.get("/overview", response_model=AdminOverview)
def overview(db: Session = Depends(get_db)) -> dict:
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users_7d = (
        db.query(func.count(func.distinct(Conversation.user_id)))
        .filter(Conversation.updated_at >= week_ago)
        .scalar()
        or 0
    )
    total_conversations = db.query(func.count(Conversation.id)).scalar() or 0
    total_messages = db.query(func.count(Message.id)).scalar() or 0
    total_books = db.query(func.count(Book.id)).scalar() or 0
    total_quran_plans = db.query(func.count(QuranPlan.id)).scalar() or 0

    provider_rows = (
        db.query(Message.provider, func.count(Message.id))
        .filter(Message.provider.isnot(None))
        .group_by(Message.provider)
        .all()
    )

    return {
        "total_users": total_users,
        "active_users_7d": active_users_7d,
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "total_books": total_books,
        "total_quran_plans": total_quran_plans,
        "messages_by_provider": {provider: count for provider, count in provider_rows},
    }


@router.get("/audit-logs", response_model=list[AuditLogRead])
def audit_logs(db: Session = Depends(get_db), limit: int = 100) -> list[AuditLog]:
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 500)).all()
