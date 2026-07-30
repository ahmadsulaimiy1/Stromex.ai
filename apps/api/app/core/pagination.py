"""Audit finding: `list_conversations`, `list_messages`, `admin.list_users`,
`list_books`, and `list_plans` had no limit at all — at real scale (a power
user with tens of thousands of messages, or an admin listing a million-user
table) each of those returns the entire table in one response. This is a
shared, capped limit/offset dependency so every list endpoint gets the same
sane default and the same hard ceiling, rather than five different ad-hoc
`Query(...)` declarations that could drift out of sync.

Limit/offset (not a cursor) is a deliberate MVP-scope choice: it's correct
and simple at the row counts a single StromeX account or a Platform-phase
tenant will realistically have. A keyset/cursor scheme is the right call the
moment `OFFSET` on a very large, frequently-written table starts show up in
slow-query logs — noted here rather than built speculatively.
"""

from dataclasses import dataclass

from fastapi import Query


@dataclass(slots=True)
class Page:
    limit: int
    offset: int


def pagination(
    limit: int = Query(50, ge=1, le=200, description="Max rows to return"),
    offset: int = Query(0, ge=0, description="Rows to skip"),
) -> Page:
    return Page(limit=limit, offset=offset)


def wide_pagination(
    limit: int = Query(200, ge=1, le=500, description="Max rows to return"),
    offset: int = Query(0, ge=0, description="Rows to skip"),
) -> Page:
    """For endpoints whose natural page size is bigger than the default —
    currently just message history."""
    return Page(limit=limit, offset=offset)
