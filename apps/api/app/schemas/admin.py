import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models.user import UserRole


class AdminUserRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class AdminUserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


class AdminOverview(BaseModel):
    total_users: int
    active_users_7d: int
    total_conversations: int
    total_messages: int
    total_books: int
    total_quran_plans: int
    messages_by_provider: dict[str, int]


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    created_at: datetime
