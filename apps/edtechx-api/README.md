# EdirasX API

Backend for EdirasX — the education platform that becomes your school's own platform.

Governing documents live in [`docs/edtechx/`](../../docs/edtechx/). Read
[`EDTECHX_EDITORIAL_BIBLE.md`](../../docs/edtechx/EDTECHX_EDITORIAL_BIBLE.md) first;
it is the constitution, and it wins over anything here.

## What exists today

Phase 1, the isolation spine: tenancy, identity, authorization, audit, and the
three-layer tenant isolation everything else depends on. See
[`EDTECHX_PROGRESS.md`](../../docs/edtechx/EDTECHX_PROGRESS.md) for exactly what is
built, what is next, and what is deliberately deferred.

## The one thing to understand first

Tenant isolation is enforced in three independent layers, and the middle one is
the guarantee:

1. **Request context** — the tenant is resolved from the Host header and checked
   against the token's `tid` claim. Never from a query parameter, body field, or
   client-supplied header.
2. **PostgreSQL row-level security** — every tenant-owned table carries a
   `FORCE ROW LEVEL SECURITY` policy bound to `current_setting('app.tenant_id')`.
   The application connects as a role that neither owns the tables nor holds
   `BYPASSRLS`. A forgotten `WHERE tenant_id = ...` returns zero rows.
3. **ORM guard** — SQLAlchemy stamps `tenant_id` on insert and filters selects,
   so mistakes fail fast and legibly in development.

Layer 2 is not optional and not decorative. `app/tests/test_tenant_isolation.py`
proves it, generating a case per tenant-owned model from the registry, so a new
model is covered by existing.

## Running it locally

Requires Python 3.11+ and PostgreSQL 15+.

```bash
# 1. Roles and databases. Two roles, deliberately: see above.
sudo -u postgres psql <<'SQL'
CREATE ROLE edtechx_migrator LOGIN PASSWORD 'edtechx_migrator' NOBYPASSRLS;
CREATE ROLE edtechx_app      LOGIN PASSWORD 'edtechx_app'      NOBYPASSRLS;
CREATE DATABASE edtechx      OWNER edtechx_migrator;
CREATE DATABASE edtechx_test OWNER edtechx_migrator;
-- Scratch database for the migration tests. The migrator role deliberately
-- lacks CREATEDB, so this is created once, here.
CREATE DATABASE edtechx_mig  OWNER edtechx_migrator;
SQL
sudo -u postgres psql -d edtechx      -c 'CREATE EXTENSION IF NOT EXISTS pgcrypto' -c 'CREATE EXTENSION IF NOT EXISTS citext'
sudo -u postgres psql -d edtechx_test -c 'CREATE EXTENSION IF NOT EXISTS pgcrypto' -c 'CREATE EXTENSION IF NOT EXISTS citext'
sudo -u postgres psql -d edtechx_mig  -c 'CREATE EXTENSION IF NOT EXISTS pgcrypto' -c 'CREATE EXTENSION IF NOT EXISTS citext'

# 2. Dependencies
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt

# 3. Configuration
cp .env.example .env

# 4. Schema. In production this is `alembic upgrade head`, which applies row-
#    level security and refuses to complete if any tenant-owned table is left
#    unprotected. `build_schema()` is the equivalent for tests and development.
.venv/bin/alembic upgrade head

# 5. Run
.venv/bin/uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs` (disabled in production).

## Tests

```bash
.venv/bin/python -m pytest app/tests -q
.venv/bin/python -m ruff check app
```

Integration tests need real PostgreSQL and skip cleanly without it — but a run
that skips them has proven nothing about isolation. SQLite is not permitted in
this suite (ADR-016): the guarantee under test is a PostgreSQL feature, and a
green SQLite suite would be false confidence about the one thing that must never
be wrong.

### Blocking suites

These gate a release. A red run is not a "known failure":

| Suite | Proves |
|---|---|
| `test_tenant_isolation.py` | No tenant can reach another's data by any path |
| `test_boundaries.py` | Module boundaries hold; no route is unguarded |
| `test_authz.py` | Permission expansion cannot leak across resources |
| `test_security.py` | Tokens, hashing, and the production config guard |
| `test_api.py` | The request lifecycle enforces all of the above end to end |
| `test_rate_limit.py` | The limiter is atomic, tenant-scoped, and not an existence oracle |
| `test_migrations.py` | The migration path produces the protected schema the models describe |

## Trying tenant isolation by hand

```bash
.venv/bin/python - <<'PY'
import os, uuid
os.environ["EDTECHX_DATABASE_URL"] = "postgresql+psycopg://edtechx_app:edtechx_app@localhost:5432/edtechx"
from sqlalchemy import text
from app.db.session import get_session_factory, bind_tenant

s = get_session_factory()()
bind_tenant(s, uuid.uuid4())          # a school that owns nothing
print(s.execute(text("SELECT count(*) FROM roles")).scalar_one())   # -> 0, always
PY
```

## Layout

```
app/
  core/       config, context, security, errors, middleware
  db/         base + mixins, session + ORM guard, rls, registry, bootstrap
  modules/
    tenancy/  schools and their hostnames
    identity/ users, memberships, sessions
    authz/    permission catalogue, scopes, roles, system role templates
    audit/    audit and security events
  api/        dependencies (the enforced request lifecycle) and v1 routes
  tests/
```

A module owns its tables and is read through its service layer, never by
importing its models. `test_boundaries.py` enforces this, and its exception list
is empty.


## Redis

Required in production for rate limiting. A per-process limiter multiplies every
limit by the worker count while appearing to work, so `get_backend()` refuses
one outside development.

```bash
redis-server --daemonize yes
```

Without it, development falls back to the in-process backend with a warning.
