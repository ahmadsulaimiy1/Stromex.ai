# EdirasX Progress

**The resumption document.** A session that picks this up cold should be able to
continue without re-deriving anything. Consolidated from the nine state files
the brief specified — see `EDTECHX_DECISIONS.md` ADR-015 for why three files
beat nine.

**Last updated:** end of session 1
**Current phase:** Phase 1 complete → Phase 2 next

---

## Current state in one paragraph

The eleven governing documents exist and are internally consistent. EdirasX is
placed in its own namespace (`docs/edtechx/`, `apps/edtechx-api/`) leaving
StromeX untouched. Phase 1 — the isolation spine — is built and tested against
real PostgreSQL: three-layer tenant isolation with `FORCE ROW LEVEL SECURITY`
proven load-bearing, host-based tenant resolution with a token/host agreement
check, an additive permission catalogue with ABAC scopes, eleven system role
templates, append-only audit, Argon2id credentials, and a FastAPI request
lifecycle that enforces all of it. 121 tests pass; ruff is clean. Nothing is
stubbed or faked. Phase 2 (the institution: academic structure, people,
enrolment) is next.

---

## Completed

### Phase 0 — Constitution ✅
- Repository and environment inspected; PostgreSQL 16, Python 3.11, Node 22 confirmed available.
- Placement decision made and recorded (ADR-001): EdirasX in its own namespace; StromeX untouched.
- Eleven governing documents written: Editorial Bible, Product Spec, UX Principles, Design System, Architecture, Database, Security, Permission Model, AI Architecture, Billing, Customization Engine.
- Roadmap, decision record, and this progress system established.

### Phase 1 — Isolation spine ✅

| Area | What was built |
|---|---|
| Configuration | `Settings` with two database URLs; production guard that **refuses to boot** on a default secret, debug mode, localhost database, plaintext CORS, or a shared migration role |
| Context | `ContextVar`-based tenant/principal/request-id context; tenant-scoped work cannot run without a tenant established |
| Tenant isolation L1 | Host → tenant resolution; token `tid` checked against host tenant; mismatch → 403 + critical security event |
| Tenant isolation L2 | `ENABLE` + **`FORCE` ROW LEVEL SECURITY** on every tenant-owned table, policy on `current_setting('app.tenant_id')`; app role holds no `BYPASSRLS` and owns no tables; applied idempotently and verified |
| Tenant isolation L3 | SQLAlchemy `after_begin` re-applies the setting per transaction; `do_orm_execute` filters selects; `before_flush` stamps `tenant_id` and refuses foreign ones |
| Registry | `TenantOwned.__init_subclass__` registers models, driving policy emission *and* test generation from one marker |
| Identity | Global `User`, tenant-scoped `Membership`, `UserSession` (refresh family with rotation lineage and revocation) |
| Authorization | ~150-permission catalogue validated at boot; `manage`/wildcard expansion; 9 scope kinds with union semantics; 11 system role templates |
| Audit | `AuditEvent` (tenant-owned, append-only — `UPDATE`/`DELETE` revoked from the app role) and `SecurityEvent` (platform-level, so pre-auth events are recordable) |
| Credentials | Argon2id; bcrypt accepted on import and flagged for rehash; timing-equalized verification; keyed-hash refresh tokens; elevation window |
| HTTP | Request-id + structured access logging, strict CSP and security headers, body-size limit, error taxonomy that maps missing-permission→403 and out-of-scope→404 |
| Request lifecycle | Steps 2/4/5/6/8 of Architecture §5 enforced as FastAPI dependencies |

### Verification performed

| Claim | How it was proven |
|---|---|
| RLS is load-bearing, not decorative | Disabled the policy on `roles` and re-ran a stranger-context query: **32 rows leaked**. Re-enabled: **0 rows**. The ORM guard alone did not catch the raw-SQL path — which is exactly the point of layer 2 |
| Isolation coverage cannot rot | Cases generated from the model registry; 8 tenant-owned models × 2 generated checks, plus targeted write/update/delete/IDOR cases |
| Route coverage check works | Added a deliberately unguarded route; the check flagged `GET /api/v1/leaky` and nothing else |
| Module boundaries hold | Boundary test caught a real reverse dependency (identity → authz) introduced mid-session; fixed by removing the back-reference. **Exception list is now empty** |
| Production guard works | Five separate misconfigurations each refuse to construct `Settings` |

### Test suite — 121 passing, 0 failing, 0 skipped (with PostgreSQL available)

| Suite | Tests | Covers |
|---|---|---|
| `test_tenant_isolation.py` | 23 | Journey 12; generated per model; forced-policy audit; append-only audit log |
| `test_authz.py` | 23 | Catalogue integrity, expansion leaks, role restraint, scope parsing |
| `test_security.py` | 22 | Hashing, token forgery/expiry/type-confusion, production guard |
| `test_tenant_resolution.py` | 21 | Host normalization, subdomain rules, custom-domain verification, suspension |
| `test_boundaries.py` | 16 | Module imports, core layering, provider-SDK confinement, route coverage |
| `test_api.py` | 16 | Full lifecycle: host → auth → tenant agreement → permission → response |

---

## Next — Phase 2: the institution

In priority order. Each carries the Bible's Definition of Done.

1. **Alembic baseline migration** for the Phase 1 schema, with the RLS-gate check wired in (currently the schema is built by `app.db.bootstrap`, which is correct for tests and development but is not a migration path).
2. **Tenant provisioning service** — create tenant + domain + system roles + owner membership as one audited transaction. The logic currently lives in the test fixture and must become real.
3. **Authentication endpoints** — login (with lockout), refresh (with rotation and reuse detection), logout, sign-out-everywhere, TOTP enrolment and challenge.
4. **Academic structure** — stages, levels, academic years, terms, class groups, subjects, class-subject allocation, grading scales and bands.
5. **People** — students, enrolments, guardians, student–guardian links, custom fields.
6. **The Four Schools fixture** — configure all four Bible §8 shapes in tests and assert zero code changes were needed. This is the acceptance criterion for Phase 2.
7. **Scope predicate compilation** — `taught_by_self`, `own_children`, `department` as SQL predicates applied to list queries, with the leak-by-row-count tests.
8. **Bulk import** with dry-run and per-row error reporting.
9. **Entitlement engine** with plan seeding.

---

## Blocked

Nothing is blocked. Items awaiting external input, none of which stop Phase 2:

| Item | Needs | Interim |
|---|---|---|
| Real AI provider calls | Provider API keys | Gateway + adapters are Phase 5; a deterministic development provider is specified and refuses to load in production |
| Real payment capture | Paystack/Flutterwave/Stripe credentials | Payment port + sandbox adapter driving the real state machine (Phase 3) |
| Email and SMS delivery | SMTP / provider credentials | Notification port + outbox adapter (Phase 3) |
| Custom domain TLS | Deployment environment | Verification model exists; unverified domains already refuse to resolve |
| Pilot data | A partner school | Phase 9 |

---

## Known issues

| # | Issue | Severity | Plan |
|---|---|---|---|
| 1 | Schema is created by `build_schema()`, not by a migration | Medium | Phase 2 item 1. Blocks nothing yet; would block a second deployment |
| 2 | Redis is configured but unused — no rate limiting or token denylist yet | Medium | Phase 2 item 3, alongside the auth endpoints they protect |
| 3 | Scopes are parsed and unioned but not yet compiled to SQL predicates | Medium | Phase 2 item 7. No route currently returns scoped lists, so nothing is under-enforced today |
| 4 | `starlette.testclient` deprecation warning from FastAPI 0.141 | Trivial | Upstream; revisit on the next FastAPI bump |
| 5 | `_IncludedRouter` traversal in `test_boundaries.py` reaches into a FastAPI internal | Low | Written to accept both routing shapes so it degrades to the public shape rather than silently checking nothing |
| 6 | No frontend yet | Expected | Phase 4 |

---

## Working notes for the next session

- **Start here:** `apps/edtechx-api/README.md`, then this file, then `EDTECHX_ROADMAP.md` Phase 2.
- **Environment:** PostgreSQL must be running (`service postgresql start`). Roles and databases are created by the block in the API README. Without them, integration tests skip — and a skipped isolation suite proves nothing.
- **Before writing any model:** if it belongs to a school, it inherits `TenantOwned`. That single decision gets it a policy and an isolation test automatically. If it does *not*, write down why, as `Tenant`, `TenantDomain`, `User`, and `SecurityEvent` each do in their docstrings.
- **Before adding a route:** give it a `RequirePermission` dependency, or add it to `PUBLIC_ROUTES` in `test_boundaries.py`. There is no third option.
- **Before adding a permission:** add it to `CATALOGUE` first. Roles referencing unknown permissions fail the boot.
- **Never** connect the request path as `edtechx_migrator`. It owns the tables, and `FORCE RLS` is bypassed for owners. The production guard refuses this; development would not notice.
