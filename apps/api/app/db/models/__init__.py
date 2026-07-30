"""Import every model module so `Base.metadata` is fully populated for Alembic
autogenerate and for `Base.metadata.create_all()` in tests."""

from app.db.models.audit import AuditLog
from app.db.models.book import Book, BookChapter
from app.db.models.conversation import Conversation, Message
from app.db.models.memory import MemoryItem
from app.db.models.quran import QuranPlan, QuranReviewLog, QuranRevisionItem
from app.db.models.user import User

__all__ = [
    "AuditLog",
    "Book",
    "BookChapter",
    "Conversation",
    "Message",
    "MemoryItem",
    "QuranPlan",
    "QuranReviewLog",
    "QuranRevisionItem",
    "User",
]
