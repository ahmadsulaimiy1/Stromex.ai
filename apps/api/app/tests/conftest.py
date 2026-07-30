import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://stromex:stromex@localhost:5432/stromex_test")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("QDRANT_LOCAL_PATH", "")

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.base import Base, get_db
from app.db.models import *  # noqa: F401,F403
import app.services.qdrant_client as qdrant_module


@pytest.fixture(scope="session")
def engine():
    settings = get_settings()
    eng = create_engine(settings.database_url, future=True)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture()
def db_session(engine) -> Generator:
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, future=True)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def in_memory_qdrant(monkeypatch):
    """Every test gets a fresh, isolated in-memory Qdrant instance instead of
    the shared on-disk local store, so memory-service tests never leak
    vectors between test cases."""
    client = QdrantClient(":memory:")
    qdrant_module.get_qdrant.cache_clear()
    monkeypatch.setattr(qdrant_module, "get_qdrant", lambda: client)
    yield client


@pytest.fixture()
def app_client(db_session) -> Generator[TestClient, None, None]:
    from app.main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def random_email() -> str:
    return f"test-{uuid.uuid4().hex[:10]}@stromex.ai"


@pytest.fixture()
def make_user(db_session):
    """Create a persisted User row and return its id — memory_items.user_id
    (and every other user-owned table) has a real foreign key to users.id,
    so tests that write memories/conversations must create a real user first
    rather than an arbitrary uuid4()."""
    from app.core.security import hash_password
    from app.db.models.user import User

    def _make(email: str | None = None) -> uuid.UUID:
        user = User(
            email=email or f"test-{uuid.uuid4().hex[:10]}@stromex.ai",
            password_hash=hash_password("irrelevant-for-these-tests"),
            display_name="Test User",
        )
        db_session.add(user)
        db_session.flush()
        return user.id

    return _make
