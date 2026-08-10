"""Engine, session factory, and the ORM tenant guard.

Every session carries its tenant in `session.info["tenant_id"]`, and every
transaction it opens re-applies the PostgreSQL setting the RLS policy reads.
Re-applying on *every* begin matters: `SET LOCAL` is scoped to a transaction,
so a session that commits and continues would otherwise silently lose its
tenant binding and start seeing nothing (or, without RLS, everything).

The ORM guard here is layer 3 of the three described in
EDTECHX_ARCHITECTURE.md §4. It exists to produce fast, obvious failures during
development. The database is the actual guarantee.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import ORMExecuteState, Session, sessionmaker, with_loader_criteria

from app.core.config import get_settings
from app.core.context import get_tenant
from app.db.base import TenantOwned
from app.db.rls import TENANT_SETTING

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,
            echo=settings.db_echo,
            future=True,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(), expire_on_commit=False, future=True
        )
    return _session_factory


def reset_engine() -> None:
    """Drop cached engine/factory. Used by tests that reconfigure settings."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


# --- tenant binding -------------------------------------------------------


def bind_tenant(session: Session, tenant_id: uuid.UUID | None) -> None:
    """Bind a session to a tenant and apply the setting to the live transaction."""
    session.info["tenant_id"] = tenant_id
    _apply_tenant_setting(session)


def _apply_tenant_setting(session: Session) -> None:
    tenant_id = session.info.get("tenant_id")
    # `set_config(..., is_local => true)` is the parameterizable equivalent of
    # SET LOCAL. SET LOCAL itself cannot take a bind parameter, and string
    # interpolation of a value into DDL-adjacent SQL is exactly the habit we
    # do not want anywhere in this codebase.
    session.execute(
        text("SELECT set_config(:key, :value, true)"),
        {"key": TENANT_SETTING, "value": str(tenant_id) if tenant_id else ""},
    )


@event.listens_for(Session, "after_begin")
def _set_tenant_on_begin(session: Session, transaction: Any, connection: Any) -> None:
    tenant_id = session.info.get("tenant_id")
    connection.execute(
        text("SELECT set_config(:key, :value, true)"),
        {"key": TENANT_SETTING, "value": str(tenant_id) if tenant_id else ""},
    )


# --- ORM guard ------------------------------------------------------------


@event.listens_for(Session, "do_orm_execute")
def _filter_by_tenant(state: ORMExecuteState) -> None:
    """Apply `tenant_id = :tenant` to every ORM select on a tenant-owned model."""
    if not state.is_select or state.is_column_load or state.is_relationship_load:
        return
    if state.execution_options.get("skip_tenant_filter"):
        return
    tenant_id = state.session.info.get("tenant_id")
    if tenant_id is None:
        return
    state.statement = state.statement.options(
        with_loader_criteria(
            TenantOwned,
            lambda cls: cls.tenant_id == tenant_id,
            include_aliases=True,
        )
    )


@event.listens_for(Session, "before_flush")
def _stamp_tenant_on_insert(session: Session, flush_context: Any, instances: Any) -> None:
    """Stamp `tenant_id` on new tenant-owned rows, and refuse foreign ones.

    Raising here rather than letting the database reject it gives a stack trace
    pointing at the offending code. The WITH CHECK clause on the RLS policy is
    what actually stops it in production.
    """
    tenant_id = session.info.get("tenant_id")
    if tenant_id is None:
        return
    for obj in session.new:
        if not isinstance(obj, TenantOwned):
            continue
        current = getattr(obj, "tenant_id", None)
        if current is None:
            obj.tenant_id = tenant_id
        elif current != tenant_id:
            raise PermissionError(
                f"Refusing to write {type(obj).__name__} for tenant {current} "
                f"from a session bound to tenant {tenant_id}."
            )


# --- session helpers ------------------------------------------------------


@contextmanager
def tenant_session(tenant_id: uuid.UUID | None = None) -> Iterator[Session]:
    """Open a session bound to a tenant, committing on success.

    Defaults to the tenant in the request context, so ordinary service code
    never passes it explicitly and background jobs must set the context from
    the job envelope before calling.
    """
    resolved = tenant_id if tenant_id is not None else get_tenant()
    session = get_session_factory()()
    bind_tenant(session, resolved)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
