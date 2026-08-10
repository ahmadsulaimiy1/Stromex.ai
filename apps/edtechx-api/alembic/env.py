"""Alembic environment.

Migrations connect as `edtechx_migrator`, never as the request-path role. That
separation is what makes `FORCE ROW LEVEL SECURITY` meaningful: the application
must not own the tables it queries. Reading the URL from settings rather than
from alembic.ini removes the possibility of pointing a migration at the wrong
role by editing a config file.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import create_engine

from app.core.config import get_settings
from app.db.registry import Base

config = context.config
target_metadata = Base.metadata


def _url() -> str:
    return get_settings().migration_database_url


def run_migrations_offline() -> None:
    context.configure(
        url=_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_url(), future=True)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
