# EdTechX Technical Architecture

**Version:** 1.0
**Companion documents:** `EDTECHX_DATABASE.md`, `EDTECHX_SECURITY.md`, `EDTECHX_PERMISSION_MODEL.md`, `EDTECHX_AI_ARCHITECTURE.md`

---

## 1. Guiding constraints

1. **Simple architecture, strong boundaries.** A modular monolith, not microservices. Boundaries are enforced in code structure and database schema, so that any module *could* be extracted later — but nothing is distributed before there is a measured reason.
2. **Tenant isolation is structural, not conventional.** It cannot depend on a developer remembering to add a `WHERE` clause.
3. **Configuration over code.** Every institutional variation is data.
4. **No hidden magic.** Explicit dependencies, explicit transactions, explicit authorization.
5. **Nothing fake.** Where an external service is unavailable, we build the real abstraction plus a clearly-marked development adapter — never a lie dressed as an integration.

---

## 2. Stack

| Layer | Choice | Rationale |
|---|---|---|
| API | Python 3.11+, FastAPI | Typed, fast, first-class OpenAPI; matches the team's existing StromeX codebase |
| ORM | SQLAlchemy 2.0 (typed) | Mature; supports the session-level tenant enforcement we require |
| Migrations | Alembic | Standard; already in use in this repository |
| Database | PostgreSQL 15+ | Row-Level Security, JSONB, partial indexes, full-text search, `gen_random_uuid()` |
| Cache / queue | Redis | Sessions, rate limits, entitlement cache, job queue |
| Background work | Redis-backed worker (in-process for v1, extractable) | Avoids a broker dependency before it is earned |
| Object storage | S3-compatible, via an adapter | Tenant-prefixed paths; presigned URLs |
| Web | Next.js 15 (App Router), TypeScript, Tailwind | Matches repository convention; SSR for first-paint budget |
| Auth | JWT access (short) + rotating refresh, server-side revocation | Same model proven in `apps/api` |

**Rejected and why:** microservices (no scale justification, high isolation cost); GraphQL (weak fit for a permission model this granular; REST + typed clients is clearer); separate database per tenant as the default (operationally unsustainable past a few hundred tenants — offered instead as an Enterprise deployment option, see §4.4).

---

## 3. Code structure

```
apps/edtechx-api/
  app/
    core/            config, security, deps, tenancy, errors, logging, pagination
    db/              base, session, models/, rls/
    modules/
      tenancy/       models, schemas, service, router
      identity/
      authz/
      billing/
      institution/
      academics/
      people/
      customization/
      admissions/  attendance/  timetable/  assessment/
      reporting/   finance/     communication/  conduct/
      learning/    activities/  engagement/
      intelligence/
      platform_ops/
    api/v1/          router aggregation
    tests/
```

**Module contract**

- A module owns its tables. No other module writes them.
- Cross-module reads go through the owning module's service layer, never by importing its models.
- A module exposes: `models.py` (private), `schemas.py` (public DTOs), `service.py` (public API), `router.py` (HTTP).
- Import direction is enforced by a test (`test_module_boundaries.py`) that fails on a disallowed import.

**Layering**

```
router  → validates HTTP, resolves principal, calls service. No business logic. No ORM.
service → business rules, authorization decisions, transactions. No HTTP objects.
model   → persistence only.
```

---

## 4. Multi-tenancy

### 4.1 Model

Shared database, shared schema, `tenant_id UUID NOT NULL` on every tenant-owned table, enforced by **three independent layers**. Any one of them failing must not produce a leak.

### 4.2 Layer 1 — Request-scoped tenant context

Tenant is resolved once, at the edge, in this order:

1. **Host header** → `tenant_domains` lookup (`stbede.edtechx.com` or `portal.stbedes.ac.uk`).
2. **Authenticated principal** → the `tid` claim in the access token.

If both are present and disagree, the request is rejected `403` and the attempt is logged as a security event. A token minted for tenant A is unusable on tenant B's host, which defeats the most likely real-world confusion attack.

The resolved tenant is stored in a `ContextVar` for the request's lifetime. It is never read from a query parameter, a body field, or a client-supplied header.

### 4.3 Layer 2 — Database session enforcement

Every request opens its session and immediately executes:

```sql
SET LOCAL app.tenant_id = '<uuid>';
```

Tenant-owned tables carry a **`FORCE ROW LEVEL SECURITY`** policy:

```sql
CREATE POLICY tenant_isolation ON students
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
```

The application connects as a role that is **not** the table owner and does **not** hold `BYPASSRLS`. Consequently a forgotten `WHERE tenant_id = ...` returns zero rows rather than another school's data, and an `INSERT` with a foreign `tenant_id` is rejected by the database.

Migrations and operator maintenance use a separate, privileged role over a separate connection, never the request path.

### 4.4 Layer 3 — ORM guard

A SQLAlchemy event hook stamps `tenant_id` on insert from the context, and a mixin-aware query filter applies the predicate. This layer exists to produce *fast, clear failures in development* — the database is the actual guarantee.

**Enterprise option:** a dedicated database (same schema, same code path) per tenant, selected by the tenant record. This changes the connection string, not the application.

### 4.5 Everywhere else

| Surface | Enforcement |
|---|---|
| Cache | Every key prefixed `t:{tenant_id}:` — enforced by the cache client, not by callers |
| Object storage | Every object path prefixed `tenants/{tenant_id}/`; presigned URLs are short-lived and path-scoped |
| Background jobs | Tenant id is a required field of the job envelope; the worker establishes the same context and RLS setting before running the handler |
| Search | Tenant filter injected by the search client |
| Logs / metrics | `tenant_id` as a structured field on every record |
| Rate limits | Keyed by tenant and by principal |
| Exports | Generated inside the tenant context; the file path and download authorization are tenant-scoped |

### 4.6 Cross-tenant by design

Only four things are legitimately cross-tenant, each explicitly modelled and audited:
1. Platform operator console (break-glass, §9).
2. Billing aggregation.
3. Anonymous aggregate benchmarking, **opt-in per tenant**, k-anonymized, never raw.
4. A person with memberships in several tenants (a teacher at two schools) — modelled as *distinct memberships*, never a shared session. Switching tenants re-mints the token.

---

## 5. Request lifecycle

```
1  Edge          TLS, security headers, body size limit, request id
2  Tenancy       resolve tenant from host → context
3  Rate limit    per ip / tenant / principal / route class
4  Auth          verify access token, check revocation, load principal
5  Tenant match  token tenant == host tenant, else 403 + security event
6  Session       open DB session, SET LOCAL app.tenant_id
7  Entitlement   is this feature enabled for this tenant's plan?
8  Authorization permission + scope evaluated against the resource
9  Validation    Pydantic request model
10 Service       business logic inside an explicit transaction
11 Audit         mutations write an audit record in the same transaction
12 Response      DTO serialization; no ORM object crosses the boundary
13 Metering      usage counters incremented out of band
```

Steps 2, 5, 6, 8, and 11 are the ones that must never be skippable per-route by accident. They are applied by dependency defaults; a route that opts out must do so explicitly and is flagged by a test that enumerates public routes.

---

## 6. Customization resolution

Configuration resolves through a deterministic cascade, computed once per request and cached:

```
EdTechX default
  → tenant configuration
    → campus override        (optional)
      → role override        (optional)
        → user preference    (optional, only where the school permits)
```

Four resolvers, all following the same cascade:

| Resolver | Produces |
|---|---|
| **Theme** | Resolved CSS custom properties + font references, served as a per-tenant stylesheet with an ETag keyed to the theme version |
| **Terminology** | A term map (`class → "form"`, `student → "pupil"`), applied at render time. The UI never contains a hard-coded domain noun |
| **Navigation** | The navigation tree: items, labels, order, visibility — filtered by permission and entitlement |
| **Dashboard** | Widget set, order, and size per persona |

**Versioning:** every configuration object has `draft` and `published` versions with full history. Publishing is an explicit, audited action. Rollback restores a prior version by reference, never by re-editing.

---

## 7. Entitlements

The plan a tenant is on never appears in a conditional. Instead:

```python
entitlements.require(Feature.AI_DESIGN_STUDIO)      # raises 402 with an upgrade path
entitlements.limit(Limit.ACTIVE_STUDENTS)           # returns the numeric ceiling
entitlements.meter(Meter.AI_TOKENS, n)              # records consumption
```

An entitlement set is computed from `plan → features/limits`, plus per-tenant grants and overrides (trials, pilots, negotiated Enterprise terms), cached in Redis, invalidated on subscription change. See `EDTECHX_BILLING.md`.

---

## 8. Integration abstractions

Every external dependency sits behind a port with pluggable adapters, configured per tenant or per platform:

| Port | Adapters (v1) | Development adapter |
|---|---|---|
| `AIProvider` | Anthropic, OpenAI, Google, DeepSeek, self-hosted OpenAI-compatible | Deterministic echo provider — clearly labelled, never presented as a model |
| `PaymentProvider` | Paystack, Flutterwave, Stripe | Sandbox adapter driving the real state machine |
| `NotificationChannel` | Email (SMTP/API), SMS, WhatsApp Business, Web Push | Console/outbox adapter |
| `ObjectStorage` | S3-compatible | Local filesystem |
| `SearchIndex` | Postgres FTS (v1), external engine later | — |

**The rule:** when credentials are absent, the port reports itself unconfigured and the feature degrades honestly with an actionable message. It never pretends to have succeeded. Development adapters are refused entirely when `ENVIRONMENT=production`.

---

## 9. Platform operations and break-glass

Operator access to tenant *metadata* (health, usage, subscription) is ordinary and audited. Operator access to tenant *content* (student records, messages, grades) requires break-glass:

1. Operator states a reason and a duration (maximum 4 hours).
2. A time-boxed, scope-limited grant is issued.
3. The tenant's administrators are notified.
4. Every action under the grant is audited with the grant id.
5. The grant expires automatically and cannot be renewed silently.

---

## 10. Observability

Structured JSON logs (structlog) with `request_id`, `tenant_id`, `principal_id`, `route`, `duration_ms`, `status`. **Never** credentials, tokens, AI prompt content, or personal data beyond identifiers.

Metrics: request rate/latency/error by route and tenant; database pool saturation; job queue depth and age; AI cost and tokens by tenant/provider/feature; entitlement denials (a leading indicator of both upsell and of a limit set wrongly).

Audit log is a separate, append-only concern — a compliance artefact, not a debugging tool. It records actor, tenant, action, resource type and id, before/after for academic and financial records, ip, user agent, and request id.

---

## 11. Testing architecture

| Layer | Approach |
|---|---|
| Unit | Pure service logic, no I/O |
| Integration | Real PostgreSQL with RLS active — SQLite is not permitted, because it cannot express the isolation guarantee we are testing |
| API | Full stack through the router with a real database |
| Authorization | Matrix: every role × every route class × allowed/denied |
| **Tenant isolation** | Every tenant-owned resource, exercised from a foreign tenant's context, must return 404/403 — never data. Generated from the model registry so that a *new model is automatically covered* |
| Boundary | Static check of cross-module imports |
| E2E | The twelve critical journeys |
| Accessibility | Automated axe pass + a manual keyboard/screen-reader script per journey |
| Performance | Budgets asserted on key routes |

---

## 12. Environments and deployment

`development` (local, docker compose) → `test` (ephemeral, CI) → `staging` (production-shaped, anonymized data) → `production`.

Deployment: containerized API and web behind a reverse proxy with wildcard TLS for `*.edtechx.com` and on-demand certificates for custom domains. Migrations run as a separate, gated step with a privileged role. Zero-downtime requires the expand/contract migration discipline described in `EDTECHX_DATABASE.md` §9.

---

## 13. What we deliberately are not building yet

Recorded so that absence is a decision, not an oversight: event sourcing, CQRS, a service mesh, a bespoke search cluster, multi-region active-active, a plugin runtime for third-party code. Each is revisited when a measured constraint demands it. See `EDTECHX_DECISIONS.md` ADR-002.
