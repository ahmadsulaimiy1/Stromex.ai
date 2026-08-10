"""Compiling scopes into SQL, so authorization constrains the query itself.

A permission answers *may this person do it*. A scope answers *to which
records*. The second is worthless unless it reaches the database: a correct
permission with a filter applied after the rows have been fetched is still a
breach, because the rows were fetched — they exist in the process, in the log
line, in the pagination total, and in whatever the next developer does with the
list before the filter runs.

So a scope becomes a `WHERE` clause. Three rules make that safe:

  **Fail closed, always.** Every path that cannot produce a predicate produces
  `false`. No scopes, no principal, an unknown scope kind, a resource with no
  clause for the scope held — every one of those yields *no rows*. The only way
  to obtain `true` is an explicit `tenant` scope on a resource whose plan says
  that scope reaches it, or an audited `system_access` block.

  **Scopes are resolved per permission.** `authz.scopes.scopes_for` returns
  only the scopes attached to grants that actually confer the permission being
  exercised. A broad scope on one permission cannot widen another.

  **Composition is union within a permission, intersection between concerns.**
  The scopes a principal holds for one permission are `OR`-ed, because holding
  two departments must reach both. Everything else is `AND`-ed and cannot be
  loosened by a scope: the tenant predicate (row-level security, in the
  database, always), the permission check (before the query runs at all), and
  any filter the caller applied. A scope can only ever narrow.

This layer complements row-level security rather than replacing it. RLS is the
tenant boundary and is enforced by PostgreSQL on every path including raw SQL.
Scope is the boundary *within* a tenant, and is enforced here — which is why
every read of a scoped resource goes through `scoped_select` and why obtaining
an unrestricted predicate any other way is deliberately difficult.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from sqlalchemy import ColumnElement, Select, false, func, or_, select, true
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import True_

from app.core.context import Principal, get_tenant
from app.modules.authz.scopes import ScopeKind, ScopeSet, scopes_for

# --- the elevated context -------------------------------------------------

_system_reason: ContextVar[str | None] = ContextVar(
    "edtechx_system_access_reason", default=None
)


class SystemAccessRefused(RuntimeError):
    """Raised when elevated access is attempted without a tenant bound."""


class ScopePlanError(RuntimeError):
    """A resource's plan tried to widen a query rather than narrow it."""


@contextmanager
def system_access(reason: str) -> Iterator[None]:
    """Run scoped reads without a scope, deliberately, and leave a record.

    For the operations that genuinely have no principal: a nightly report over
    a whole school, a notification sweep, an export the school itself asked for.
    Three properties make it safe to have at all:

      *It is explicit.* A background job that forgets to enter it gets zero rows
      rather than every row — the failure is visible on the first run instead of
      invisible forever.

      *It is still inside a tenant.* Row-level security is untouched, so this
      widens reach within one school and never across two. Attempting it with no
      tenant bound is refused rather than granted.

      *It is audited.* Every entry writes a security event naming the reason, so
      "why did a job read every student record on Tuesday" has an answer.
    """
    if get_tenant() is None:
        raise SystemAccessRefused(
            "System access requires a tenant. Elevation widens reach within one "
            "school; it is not a way to work across all of them."
        )
    if not reason or not reason.strip():
        raise SystemAccessRefused("System access requires a stated reason.")

    from app.modules.audit.service import SecurityEventKind, Severity, record_security

    record_security(
        SecurityEventKind.system_access,
        tenant_id=get_tenant(),
        severity=Severity.info,
        reason=reason.strip(),
    )
    token = _system_reason.set(reason.strip())
    try:
        yield
    finally:
        _system_reason.reset(token)


def is_elevated() -> bool:
    return _system_reason.get() is not None


# --- plans -----------------------------------------------------------------

# A clause builder receives the ids named by the scope (empty for the kinds that
# name none) and returns the SQL that narrows the resource to them — or `None`
# to say "this scope cannot reach this resource", which contributes no rows.
ClauseBuilder = Callable[["ScopeContext"], ColumnElement[bool] | None]


@dataclass(frozen=True, slots=True)
class ScopeContext:
    """What a clause builder needs: the session, the actor, and the scope's ids."""

    db: Session
    principal: Principal | None
    ids: frozenset[uuid.UUID]

    @property
    def membership_id(self) -> uuid.UUID | None:
        return self.principal.membership_id if self.principal else None

    @property
    def user_id(self) -> uuid.UUID | None:
        return self.principal.user_id if self.principal else None


@dataclass(frozen=True, slots=True)
class ScopePlan:
    """How one resource is narrowed by each kind of scope.

    Written by the module that owns the table, because only it knows how a
    student relates to a class group. `authz` owns the vocabulary and the
    composition; it does not own anybody else's joins.

    A kind absent from `clauses` reaches this resource not at all. That is the
    fail-closed default and it is deliberate: a scope nobody has taught this
    resource about must not be read as "no restriction".
    """

    resource: str
    clauses: Mapping[ScopeKind, ClauseBuilder]
    # Whether an explicit `tenant` scope reaches this resource without limit.
    # True for ordinary institutional records; a plan may set it false for a
    # resource that must never be readable school-wide by scope alone.
    tenant_scope_is_unrestricted: bool = True


# --- compilation ------------------------------------------------------------


def compile_scope_set(
    plan: ScopePlan,
    scope_set: ScopeSet,
    *,
    db: Session,
    principal: Principal | None,
) -> ColumnElement[bool]:
    """Turn the scopes held for one permission into one boolean expression.

    Union across the scopes, because they were granted separately and each is a
    reach the principal genuinely has. Never `true` unless a `tenant` scope is
    present and the plan permits it.
    """
    if not scope_set.scopes:
        return false()

    clauses: list[ColumnElement[bool]] = []
    for scope in scope_set.scopes:
        # `tenant` is handled here rather than by a clause builder, so that
        # "no restriction" is a decision this function makes from an explicit
        # scope kind — never something a plan can return by accident.
        if scope.kind is ScopeKind.tenant:
            if plan.tenant_scope_is_unrestricted:
                return true()
            continue
        builder = plan.clauses.get(scope.kind)
        if builder is None:
            # A scope kind this resource was never taught about reaches none of
            # it. The fail-closed default, and the reason a new scope kind
            # cannot silently widen an existing resource.
            continue
        clause = builder(ScopeContext(db=db, principal=principal, ids=scope.ids))
        if clause is None:
            continue
        if isinstance(clause, True_):
            raise ScopePlanError(
                f"The {plan.resource!r} plan returned an unrestricted clause for "
                f"{scope.kind.value!r}. A clause narrows; only an explicit "
                "tenant scope removes the restriction."
            )
        clauses.append(clause)
    if not clauses:
        return false()
    return or_(*clauses)


def predicate_for(
    plan: ScopePlan,
    *,
    db: Session,
    principal: Principal | None,
    permission: str,
) -> ColumnElement[bool]:
    """The predicate a principal's authority produces for one resource.

    The entry point everything else uses. Note the order: elevation first (and
    only inside an audited block), then the principal, then the scopes for
    *this* permission. There is no branch that reaches `true` by accident.
    """
    if is_elevated():
        return true()
    if principal is None:
        # A query with no actor is a background job that forgot its context, or
        # an anonymous request that should never have got this far. Either way,
        # nothing.
        return false()
    return compile_scope_set(
        plan, scopes_for(principal, permission), db=db, principal=principal
    )


# --- the sanctioned query helpers ------------------------------------------


def scoped_select(
    entity: type,
    plan: ScopePlan,
    *,
    db: Session,
    principal: Principal | None,
    permission: str,
) -> Select:
    """A `SELECT` that is already constrained. The only sanctioned way to read.

    Returning a `Select` rather than rows is deliberate: the caller may still
    order, paginate, join and filter, and every one of those composes with
    `AND` on top of a predicate it cannot remove.
    """
    return select(entity).where(
        predicate_for(plan, db=db, principal=principal, permission=permission)
    )


def scoped_count(
    entity: type,
    plan: ScopePlan,
    *,
    db: Session,
    principal: Principal | None,
    permission: str,
) -> int:
    """A count over exactly the rows the principal may see.

    Exists so that counting is not the hole in an otherwise-scoped resource. A
    count endpoint built with `select(func.count())` and no predicate tells an
    unauthorized caller precisely how many records they cannot see — which is
    most of what they wanted to know.
    """
    return db.execute(
        select(func.count())
        .select_from(entity)
        .where(predicate_for(plan, db=db, principal=principal, permission=permission))
    ).scalar_one()


def scoped_get(
    entity: type,
    identifier: uuid.UUID,
    plan: ScopePlan,
    *,
    db: Session,
    principal: Principal | None,
    permission: str,
):
    """Fetch one row by id, or `None` if it is out of scope.

    `None` rather than a refusal, because the caller turns it into a 404 and not
    a 403 (ADR-004). "You may not see this" and "this does not exist" must be
    the same answer, or the difference between them is the answer.
    """
    return db.execute(
        scoped_select(entity, plan, db=db, principal=principal, permission=permission)
        .where(entity.id == identifier)
    ).scalars().first()


def scoped_exists(
    entity: type,
    identifier: uuid.UUID,
    plan: ScopePlan,
    *,
    db: Session,
    principal: Principal | None,
    permission: str,
) -> bool:
    return (
        scoped_get(
            entity, identifier, plan, db=db, principal=principal, permission=permission
        )
        is not None
    )


__all__ = [
    "ClauseBuilder",
    "ScopeContext",
    "ScopePlan",
    "ScopePlanError",
    "SystemAccessRefused",
    "compile_scope_set",
    "is_elevated",
    "predicate_for",
    "scoped_count",
    "scoped_exists",
    "scoped_get",
    "scoped_select",
    "system_access",
]
